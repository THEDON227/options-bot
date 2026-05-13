import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")

def connect():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = connect()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        symbol TEXT,
        strategy TEXT,
        option_type TEXT,
        strike REAL,
        expiry TEXT,
        contracts INTEGER,
        entry_price REAL,
        stop_loss REAL,
        profit_target REAL,
        status TEXT DEFAULT 'open',
        pnl REAL DEFAULT 0,
        notes TEXT
    )
    """)

    conn.commit()
    conn.close()

def log_trade(
    symbol,
    strategy,
    option_type,
    strike,
    expiry,
    contracts,
    entry_price,
    stop_loss,
    profit_target,
    notes=""
):
    conn = connect()
    c = conn.cursor()

    c.execute("""
    INSERT INTO trades (
        symbol,
        strategy,
        option_type,
        strike,
        expiry,
        contracts,
        entry_price,
        stop_loss,
        profit_target,
        notes
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    RETURNING id
    """, (
        symbol,
        strategy,
        option_type,
        strike,
        expiry,
        contracts,
        entry_price,
        stop_loss,
        profit_target,
        notes
    ))

    trade_id = c.fetchone()[0]

    conn.commit()
    conn.close()

    return trade_id

def get_all_trades():
    conn = connect()
    c = conn.cursor(cursor_factory=RealDictCursor)

    c.execute("""
    SELECT *
    FROM trades
    ORDER BY created_at DESC
    """)

    rows = c.fetchall()

    conn.close()

    return rows

def close_trade(trade_id, pnl=0):
    conn = connect()
    c = conn.cursor()

    c.execute("""
    UPDATE trades
    SET status = %s,
        pnl = %s
    WHERE id = %s
    """, ("closed", pnl, trade_id))

    conn.commit()
    conn.close()

def show_trades():
    trades = get_all_trades()

    print()
    print("ID | Symbol | Type | Strike | Status | P&L")
    print("-" * 60)

    for t in trades:
        print(
            f"{t['id']} | "
            f"{t['symbol']} | "
            f"{t['option_type']} | "
            f"{t['strike']} | "
            f"{t['status']} | "
            f"{t['pnl']}"
        )
