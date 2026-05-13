import time
from datetime import datetime
from dotenv import load_dotenv

from scanner import run_scan, Signal
from risk_manager import RiskManager, TradeSetup
from journal import init_db, log_trade, close_trade, show_trades, get_all_trades
from alerts import alert_signal, alert_trade_opened, alert_risk_rejected, send_alert
from alpaca_broker import get_account, place_market_order, get_positions, close_position

load_dotenv()

ACCOUNT_SIZE = 25000.00
SCAN_INTERVAL = 300

WATCHLIST = ["AAPL", "MSFT", "NVDA", "SPY", "QQQ", "TSLA", "AMZN"]

rm = RiskManager(account_size=ACCOUNT_SIZE)


def log(msg):
    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {msg}", flush=True)


def market_is_open():
    now = datetime.utcnow()

    if now.weekday() >= 5:
        return False

    current_minutes = now.hour * 60 + now.minute

    market_open = 13 * 60 + 30
    market_close = 20 * 60

    return market_open <= current_minutes <= market_close


def today_string():
    return datetime.utcnow().strftime("%Y-%m-%d")


def already_open(symbol):
    trades = get_all_trades()

    for t in trades:
        if t.get("symbol") == symbol and t.get("status") == "open":
            return True

    return False


def send_session_start_alert():
    account = get_account()

    portfolio = float(account.get("portfolio_value", 0))
    cash = float(account.get("cash", 0))

    send_alert(
        "MARKET SESSION STARTED\n\n"
        "Bot is online and scanning every 5 minutes.\n"
        "Mode: Paper Trading\n"
        f"Portfolio: ${portfolio:,.2f}\n"
        f"Cash: ${cash:,.2f}"
    )


def send_session_end_alert():
    today = today_string()
    trades = get_all_trades()

    today_trades = [
        t for t in trades
        if str(t.get("created_at", "")).startswith(today)
    ]

    closed_trades = [
        t for t in today_trades
        if t.get("status") == "closed"
    ]

    total_pnl = sum(float(t.get("pnl") or 0) for t in closed_trades)
    wins = len([t for t in closed_trades if float(t.get("pnl") or 0) > 0])
    losses = len([t for t in closed_trades if float(t.get("pnl") or 0) < 0])

    send_alert(
        "MARKET SESSION ENDED\n\n"
        f"Trades Today: {len(today_trades)}\n"
        f"Closed Trades: {len(closed_trades)}\n"
        f"Wins: {wins}\n"
        f"Losses: {losses}\n"
        f"Daily P&L: ${total_pnl:.2f}\n\n"
        "Bot is now in overnight standby mode."
    )


def signal_to_setup(signal: Signal) -> TradeSetup:
    entry = round(signal.underlying_price * 0.015, 2)
    stop = round(entry * 0.70, 2)
    target = round(entry * 2.50, 2)

    return TradeSetup(
        symbol=signal.symbol,
        option_type="call" if signal.direction == "long" else "put",
        strike=round(signal.underlying_price * 1.02, 2),
        expiry="2026-07-18",
        contracts=1,
        entry_price=entry,
        stop_loss=stop,
        profit_target=target,
        bid=round(entry * 0.98, 2),
        ask=round(entry * 1.02, 2),
        open_interest=1000,
        strategy=signal.strategy,
        notes=signal.reason
    )


def manage_positions():
    trades = get_all_trades()
    positions = get_positions()

    if not isinstance(positions, list):
        return

    for t in trades:
        if t.get("status") != "open":
            continue

        symbol = t.get("symbol")
        entry = float(t.get("entry_price") or 0)
        stop = float(t.get("stop_loss") or 0)
        target = float(t.get("profit_target") or 0)

        for p in positions:
            if not isinstance(p, dict):
                continue

            if p.get("symbol") != symbol:
                continue

            current_price = float(
                p.get("current_price")
                or p.get("market_value")
                or entry
            )

            if current_price <= stop:
                close_position(symbol)
                pnl = (current_price - entry) * 100
                close_trade(t.get("id"), pnl)

                send_alert(
                    "STOP LOSS HIT\n\n"
                    f"Symbol: {symbol}\n"
                    f"P&L: ${pnl:.2f}"
                )

            elif current_price >= target:
                close_position(symbol)
                pnl = (current_price - entry) * 100
                close_trade(t.get("id"), pnl)

                send_alert(
                    "TARGET HIT\n\n"
                    f"Symbol: {symbol}\n"
                    f"P&L: ${pnl:.2f}"
                )


def run_bot():
    init_db()

    account = get_account()

    send_alert(
        "Options Bot Started\n\n"
        f"Portfolio: ${float(account.get('portfolio_value', 0)):,.2f}\n"
        f"Cash: ${float(account.get('cash', 0)):,.2f}"
    )

    scan_count = 0
    session_started_today = None
    session_ended_today = None

    while True:
        today = today_string()

        if market_is_open():
            if session_started_today != today:
                send_session_start_alert()
                session_started_today = today
                session_ended_today = None

            manage_positions()

            scan_count += 1
            log(f"Starting scan #{scan_count}")

            signals = run_scan(WATCHLIST)

            if not signals:
                log("No setups found this scan.")

            for signal in signals:
                if already_open(signal.symbol):
                    log(f"Skipping duplicate trade: {signal.symbol}")
                    continue

                setup = signal_to_setup(signal)
                result = rm.approve(setup)

                if not result.approved:
                    log(f"Risk rejected: {result.reason}")
                    alert_risk_rejected(signal.symbol, result.reason)
                    continue

                alert_signal(
                    symbol=signal.symbol,
                    strategy=signal.strategy,
                    price=signal.underlying_price,
                    rsi=signal.rsi,
                    score=signal.score,
                    reason=signal.reason
                )

                order = place_market_order(
                    symbol=signal.symbol,
                    qty=1,
                    side="buy"
                )

                alpaca_id = order.get("id", "N/A")

                trade_id = log_trade(
                    symbol=setup.symbol,
                    strategy=setup.strategy,
                    option_type=setup.option_type,
                    strike=setup.strike,
                    expiry=setup.expiry,
                    contracts=setup.contracts,
                    entry_price=setup.entry_price,
                    stop_loss=setup.stop_loss,
                    profit_target=setup.profit_target,
                    notes=f"{setup.notes} | alpaca_id:{alpaca_id}"
                )

                alert_trade_opened(
                    symbol=setup.symbol,
                    option_type=setup.option_type,
                    strike=setup.strike,
                    entry=setup.entry_price,
                    stop=setup.stop_loss,
                    target=setup.profit_target,
                    trade_id=trade_id
                )

                log(f"TRADE OPENED: {signal.symbol}")

            show_trades()
            log(f"Next scan in {SCAN_INTERVAL // 60} minutes.")
            time.sleep(SCAN_INTERVAL)

        else:
            if session_started_today == today and session_ended_today != today:
                send_session_end_alert()
                session_ended_today = today

            log("Market closed. Sleeping.")
            time.sleep(300)


if __name__ == "__main__":
    run_bot()
