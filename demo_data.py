import sqlite3
from datetime import datetime, timedelta
import random

DB_PATH = "trades.db"

trades = [
    ("AAPL",  "momentum_breakout", "call", 185.0, "2026-03-21", 1, 2.80, 1.40, 5.60,  4.90, "target_hit",  "Strong breakout above 20d high. RSI 64."),
    ("SPY",   "momentum_breakout", "call", 498.0, "2026-03-21", 1, 7.20, 3.60, 14.40, 3.60, "stop_hit",    "Failed breakout. Volume faded."),
    ("NVDA",  "momentum_breakout", "call", 875.0, "2026-03-28", 1, 13.10,6.55, 26.20, 24.80,"target_hit",  "Massive volume surge. RSI 71."),
    ("MSFT",  "momentum_breakout", "call", 415.0, "2026-04-04", 1, 6.20, 3.10, 12.40, 11.50,"target_hit",  "Clean breakout. VWAP reclaim confirmed."),
    ("QQQ",   "momentum_breakout", "call", 435.0, "2026-04-04", 1, 6.50, 3.25, 13.00, 3.25, "stop_hit",    "Market pulled back. Stop triggered."),
    ("TSLA",  "momentum_breakout", "call", 175.0, "2026-04-07", 1, 2.60, 1.30, 5.20,  4.80, "target_hit",  "RSI 68. Volume 2.3x average."),
    ("AAPL",  "momentum_breakout", "call", 192.0, "2026-04-11", 1, 2.90, 1.45, 5.80,  2.90, "time_exit",   "Held 20 days. No clear direction."),
    ("SPX",   "momentum_breakout", "call", 5200.0,"2026-04-14", 1, 78.0, 39.0, 156.0, 145.0,"target_hit",  "Index breakout. RSI 66. Strong trend."),
    ("AMZN",  "momentum_breakout", "call", 185.0, "2026-04-14", 1, 2.80, 1.40, 5.60,  1.40, "stop_hit",    "Earnings risk. Stopped out."),
    ("NVDA",  "momentum_breakout", "call", 890.0, "2026-04-17", 1, 13.35,6.68, 26.70, 24.50,"target_hit",  "Second NVDA signal. AI momentum strong."),
    ("SPY",   "momentum_breakout", "call", 502.0, "2026-04-22", 1, 7.53, 3.77, 15.06, 14.20,"target_hit",  "Market trend day. Clean setup."),
    ("MSFT",  "momentum_breakout", "call", 420.0, "2026-04-22", 1, 6.30, 3.15, 12.60, 3.15, "stop_hit",    "False breakout. Reversed same day."),
    ("TSLA",  "momentum_breakout", "call", 180.0, "2026-04-25", 1, 2.70, 1.35, 5.40,  5.00, "target_hit",  "Volume 3x average. RSI 72."),
    ("QQQ",   "momentum_breakout", "call", 442.0, "2026-04-28", 1, 6.63, 3.32, 13.26, 12.80,"target_hit",  "Tech sector momentum. Clean signal."),
    ("AAPL",  "momentum_breakout", "call", 196.0, "2026-04-28", 1, 2.94, 1.47, 5.88,  2.94, "time_exit",   "Choppy price action. Exited at 20 days."),
    ("SPX",   "momentum_breakout", "call", 5280.0,"2026-05-01", 1, 79.2, 39.6, 158.4, 79.2, "stop_hit",    "Market gap down. Stop hit immediately."),
    ("AMZN",  "momentum_breakout", "call", 190.0, "2026-05-01", 1, 2.85, 1.43, 5.70,  5.30, "target_hit",  "AWS earnings catalyst. Strong move."),
    ("NVDA",  "momentum_breakout", "call", 910.0, "2026-05-05", 1, 13.65,6.83, 27.30, 25.80,"target_hit",  "AI chip demand. Third NVDA win."),
    ("SPY",   "momentum_breakout", "call", 508.0, "2026-05-05", 1, 7.62, 3.81, 15.24, 3.81, "stop_hit",    "Fed meeting uncertainty. Stopped out."),
    ("MSFT",  "momentum_breakout", "call", 425.0, "2026-05-08", 1, 6.38, 3.19, 12.76, 11.90,"target_hit",  "Copilot revenue beat. Strong move."),
]

def populate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    base_date = datetime(2026, 3, 21)

    for idx, t in enumerate(trades):
        symbol, strategy, option_type, strike, expiry, contracts, entry, stop, target, exit_price, reason, notes = t

        entry_date = (base_date + timedelta(days=idx * 3)).strftime("%Y-%m-%d")
        pnl        = (exit_price - entry) * contracts * 100
        pnl_pct    = ((exit_price - entry) / entry) * 100
        max_risk   = entry * contracts * 100

        c.execute("""
            INSERT INTO trades
            (trade_date, symbol, strategy, option_type, strike, expiry,
             contracts, entry_price, exit_price, stop_loss, profit_target,
             status, pnl, pnl_pct, max_risk, close_reason, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'closed', ?, ?, ?, ?, ?)
        """, (
            entry_date, symbol, strategy, option_type, strike, expiry,
            contracts, entry, exit_price, stop, target,
            round(pnl, 2), round(pnl_pct, 1), round(max_risk, 2), reason, notes
        ))

    conn.commit()
    conn.close()

    print(f"Added {len(trades)} paper trades to journal.")
    print("\nSummary:")

    wins   = [t for t in trades if t[9] > t[6]]
    losses = [t for t in trades if t[9] <= t[6]]
    pnls   = [(t[9] - t[6]) * 100 for t in trades]
    total  = sum(pnls)

    print(f"Total trades  : {len(trades)}")
    print(f"Winners       : {len(wins)}")
    print(f"Losers        : {len(losses)}")
    print(f"Win rate      : {len(wins)/len(trades):.1%}")
    print(f"Total P&L     : ${total:.2f}")
    print("\nDone. Run dashboard.py to see your results.")

if __name__ == "__main__":
    populate()