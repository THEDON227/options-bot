import time
import os
from datetime import datetime
from dotenv import load_dotenv

from scanner import run_scan, Signal
from risk_manager import RiskManager, TradeSetup
from journal import init_db, log_trade, close_trade, show_trades
from alerts import alert_signal, alert_trade_opened, alert_risk_rejected, alert_daily_summary, send_alert
from alpaca_broker import get_account, place_market_order, get_positions

load_dotenv()

ACCOUNT_SIZE  = 25000.00
WATCHLIST = ["AAPL", "MSFT", "NVDA", "SPY", "QQQ", "TSLA", "AMZN", "SPX"]
SCAN_INTERVAL = 3600
rm = RiskManager(account_size=ACCOUNT_SIZE)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def signal_to_setup(signal: Signal) -> TradeSetup:
    entry  = round(signal.underlying_price * 0.015, 2)
    stop   = round(entry * 0.50, 2)
    target = round(entry * 2.0, 2)
    return TradeSetup(
        symbol        = signal.symbol,
        option_type   = "call" if signal.direction == "long" else "put",
        strike        = round(signal.underlying_price * 1.02, 2),
        expiry        = "2026-07-18",
        contracts     = 1,
        entry_price   = entry,
        stop_loss     = stop,
        profit_target = target,
        bid           = round(entry * 0.95, 2),
        ask           = round(entry * 1.05, 2),
        open_interest = 500,
        strategy      = signal.strategy,
        notes         = signal.reason
    )

def print_header(account):
    portfolio = float(account.get("portfolio_value", 0))
    cash      = float(account.get("cash", 0))
    print("\n" + "=" * 55)
    print("  OPTIONS PAPER TRADING BOT")
    print(f"  Started   : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Portfolio : ${portfolio:,.2f}")
    print(f"  Cash      : ${cash:,.2f}")
    print(f"  Symbols   : {', '.join(WATCHLIST)}")
    print("=" * 55)

def run_bot():
    init_db()
    account = get_account()
    print_header(account)
    send_alert(
        f"*Options Bot started*\n"
        f"Portfolio: ${float(account.get('portfolio_value',0)):,.2f}\n"
        f"Cash: ${float(account.get('cash',0)):,.2f}"
    )

    scan_count = 0

    while True:
        scan_count += 1
        log(f"Starting scan #{scan_count}")
        print("-" * 55)

        signals = run_scan(WATCHLIST)

        if not signals:
            log("No setups found this scan.")
        else:
            log(f"{len(signals)} signal(s) found — running risk checks.")
            for signal in signals:
                print()
                log(f"Signal : {signal.symbol} | Score: {signal.score} | RSI: {signal.rsi}")
                log(f"Reason : {signal.reason}")

                alert_signal(
                    symbol   = signal.symbol,
                    strategy = signal.strategy,
                    price    = signal.underlying_price,
                    rsi      = signal.rsi,
                    score    = signal.score,
                    reason   = signal.reason
                )

                setup  = signal_to_setup(signal)
                result = rm.approve(setup)

                if result.approved:
                    log(f"Risk check PASSED — max risk ${result.max_risk:.0f}")

                    # Place paper order on Alpaca (stock shares as proxy)
                    order = place_market_order(
                        symbol = signal.symbol,
                        qty    = 1,
                        side   = "buy"
                    )
                    alpaca_id = order.get("id", "N/A")
                    log(f"Alpaca order placed — ID: {alpaca_id}")

                    trade_id = log_trade(
                        symbol        = setup.symbol,
                        strategy      = setup.strategy,
                        option_type   = setup.option_type,
                        strike        = setup.strike,
                        expiry        = setup.expiry,
                        contracts     = setup.contracts,
                        entry_price   = setup.entry_price,
                        stop_loss     = setup.stop_loss,
                        profit_target = setup.profit_target,
                        notes         = f"{setup.notes} | alpaca_id:{alpaca_id}"
                    )

                    alert_trade_opened(
                        symbol      = setup.symbol,
                        option_type = setup.option_type,
                        strike      = setup.strike,
                        entry       = setup.entry_price,
                        stop        = setup.stop_loss,
                        target      = setup.profit_target,
                        trade_id    = trade_id
                    )
                    log(f"Trade #{trade_id} logged. Entry ${setup.entry_price} | Stop ${setup.stop_loss} | Target ${setup.profit_target}")

                else:
                    log(f"Risk check FAILED — {result.reason}")
                    alert_risk_rejected(signal.symbol, result.reason)

        print()
        print("-" * 55)

        # Print current Alpaca positions
        positions = get_positions()
        if positions:
            log(f"Open Alpaca positions: {len(positions)}")
            for p in positions:
                if isinstance(p, dict):
                    symbol = p.get("symbol", "UNKNOWN")
                    qty = p.get("qty", "N/A")
                    unrealized_pl = p.get("unrealized_pl", 0)
                else:
                    symbol = getattr(p, "symbol", "UNKNOWN")
                    qty = getattr(p, "qty", "N/A")
                    unrealized_pl = getattr(p, "unrealized_pl", 0)

                try:
                    unrealized_pl = float(unrealized_pl)
                except Exception:
                    unrealized_pl = 0

                log(f"  {symbol} | qty: {qty} | P&L: ${unrealized_pl:.2f}")
        else:
            log("No open Alpaca positions.")

        show_trades()
        print("-" * 55)
        log(f"Next scan in {SCAN_INTERVAL // 60} minutes. Press Ctrl+C to stop.")
        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n")
        log("Bot stopped by user.")
        send_alert("*Options Bot stopped* by user.")
        show_trades()