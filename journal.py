import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "trades.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.executescript("""
        CREATE TABLE IF NOT EXISTS trades (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date      TEXT NOT NULL,
            symbol          TEXT NOT NULL,
            strategy        TEXT,
            option_type     TEXT,
            strike          REAL,
            expiry          TEXT,
            contracts       INTEGER,
            entry_price     REAL,
            exit_price      REAL,
            stop_loss       REAL,
            profit_target   REAL,
            status          TEXT DEFAULT 'open',
            pnl             REAL,
            pnl_pct         REAL,
            max_risk        REAL,
            close_reason    TEXT,
            notes           TEXT,
            created_at      TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS account_snapshots (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_date   TEXT NOT NULL,
            account_value   REAL,
            daily_pnl       REAL,
            drawdown_pct    REAL,
            num_open_trades INTEGER,
            created_at      TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def log_trade(symbol, strategy, option_type, strike, expiry,
              contracts, entry_price, stop_loss, profit_target, notes=""):
    
    max_risk = contracts * entry_price * 100
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO trades 
        (trade_date, symbol, strategy, option_type, strike, expiry,
         contracts, entry_price, stop_loss, profit_target, max_risk, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d"),
        symbol, strategy, option_type, strike, expiry,
        contracts, entry_price, stop_loss, profit_target, max_risk, notes
    ))
    conn.commit()
    trade_id = c.lastrowid
    conn.close()
    print(f"Trade logged. ID: {trade_id} | {symbol} {option_type} ${strike} | Risk: ${max_risk:.0f}")
    return trade_id

def close_trade(trade_id, exit_price, close_reason):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT entry_price, contracts FROM trades WHERE id = ?", (trade_id,))
    row = c.fetchone()
    
    if not row:
        print(f"Trade ID {trade_id} not found.")
        return
    
    entry_price, contracts = row
    pnl = (exit_price - entry_price) * contracts * 100
    pnl_pct = ((exit_price - entry_price) / entry_price) * 100
    
    c.execute("""
        UPDATE trades 
        SET exit_price=?, status='closed', pnl=?, pnl_pct=?, close_reason=?
        WHERE id=?
    """, (exit_price, pnl, pnl_pct, close_reason, trade_id))
    
    conn.commit()
    conn.close()
    print(f"Trade {trade_id} closed. P&L: ${pnl:.2f} ({pnl_pct:.1f}%)")

def show_trades():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, trade_date, symbol, option_type, strike, 
               entry_price, status, pnl 
        FROM trades ORDER BY created_at DESC LIMIT 20
    """)
    rows = c.fetchall()
    conn.close()
    
    print(f"\n{'ID':<4} {'Date':<12} {'Symbol':<8} {'Type':<6} {'Strike':<8} {'Entry':<8} {'Status':<8} {'P&L'}")
    print("-" * 70)
    for r in rows:
        pnl = f"${r[7]:.2f}" if r[7] is not None else "open"
        print(f"{r[0]:<4} {r[1]:<12} {r[2]:<8} {r[3]:<6} {r[4]:<8} {r[5]:<8} {r[6]:<8} {pnl}")

if __name__ == "__main__":
    init_db()
    
    # Log a sample paper trade
    trade_id = log_trade(
        symbol="AAPL",
        strategy="momentum_breakout",
        option_type="call",
        strike=200.0,
        expiry="2026-06-20",
        contracts=1,
        entry_price=3.50,
        stop_loss=1.75,
        profit_target=7.00,
        notes="Strong volume breakout above 20d high. RSI 62."
    )
    
    # Simulate closing it at a profit
    close_trade(trade_id, exit_price=6.80, close_reason="target_hit")
    
    # Show the journal
    show_trades()
