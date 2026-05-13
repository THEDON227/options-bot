import time
from datetime import datetime
from dotenv import load_dotenv

from scanner import run_scan, Signal
from risk_manager import RiskManager, TradeSetup
from journal import (
    init_db,
    log_trade,
    close_trade,
    show_trades,
    get_all_trades
)
from alerts import (
    alert_signal,
    alert_trade_opened,
    alert_risk_rejected,
    alert_daily_summary,
    send_alert
)
from alpaca_broker import (
    get_account,
    place_market_order,
    get_positions,
    close_position
)

load_dotenv()

ACCOUNT_SIZE = 25000.00
SCAN_INTERVAL = 300
WATCHLIST = [
    "AAPL",
    "MSFT",
    "NVDA",
    "SPY",
    "QQQ",
    "TSLA",
    "AMZN"
]

rm = RiskManager(account_size=ACCOUNT_SIZE)

MAX_OPEN_TRADES = 3
MAX_DAILY_LOSS = 1000

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def market_is_open():
    now = datetime.utcnow()
    hour = now.hour
    minute = now.minute

    current = hour * 60 + minute

    market_open = 13 * 60 + 30
    market_close = 20 * 60

    return market_open <= current <= market_close

def already_open(symbol):
    trades = get_all_trades()

    for t in trades:
        if (
            t["symbol"] == symbol and
            t["status"] == "open"
        ):
            return True

    return False

def manage_positions():
    trades = get_all_trades()

    for t in trades:
        if t["status"] != "open":
            continue

        entry = float(t["entry_price"])
        stop = float(t["stop_loss"])
        target = float(t["profit_target"])

        positions = get_positions()

        for p in positions:
            symbol = p.get("symbol")

            if symbol != t["symbol"]:
                continue

            current_price = float(p.get("current_price", 0))

            if current_price <= stop:
                log(f"STOP LOSS HIT: {symbol}")

                close_position(symbol)

                pnl = (current_price - entry) * 100

                close_trade(t["id"], pnl)

                send_alert(
                    f"STOP LOSS HIT\n\n"
                    f"{symbol}\n"
                    f"P&L: ${pnl:.2f}"
                )

            elif current_price >= target:
                log(f"TARGET HIT: {symbol}")

                close_position(symbol)

                pnl = (current_price - entry) * 100

                close_trade(t["id"], pnl)

                send_alert(
                    f"TARGET HIT\n\n"
                    f"{symbol}\n"
                    f"P&L: ${pnl:.2f}"
                )

def signal_to_setup(signal: Signal):

    entry = round(signal.underlying_price * 0.015, 2)

    stop = round(entry * 0.70, 2)

    target = round(entry * 2.50, 2)

    return TradeSetup(
        symbol=signal.symbol,
        option_type="call",
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

def run_bot():

    init_db()

    account = get_account()

    send_alert(
        f"Options Bot Started\n"
        f"Portfolio: ${float(account.get('portfolio_value',0)):,.2f}"
    )

    scan_count = 0
    session_started_today = None
    session_ended_today = None

    while True:

        today = datetime.utcnow().strftime("%Y-%m-%d")

        if market_is_open():

            if session_started_today != today:
                send_alert(
                    "MARKET SESSION STARTED\n\n"
                    "Bot is online and scanning every 5 minutes.\n"
                    "Mode: Paper Trading\n"
                    "Status: Active"
                )
                session_started_today = today

            manage_positions()

            scan_count += 1

        log(f"Starting scan #{scan_count}")

        signals = run_scan(WATCHLIST)

        if not signals:
            log("No setups found.")

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

        log(f"Next scan in {SCAN_INTERVAL // 60} minutes")

        time.sleep(SCAN_INTERVAL)

        else:

            if session_ended_today != today and session_started_today == today:
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

                session_ended_today = today

            log("Market closed. Sleeping.")
            time.sleep(300)

if __name__ == "__main__":
    run_bot()
