# Options Bot — Complete Build

## Status: FULLY BUILT

## Environment
- Python 3.11 | macOS 11 | ~/options_bot
- Data: Alpha Vantage (live) + Synthetic (backtest)
- Paper account: Alpaca $100,000
- Alerts: Telegram

## All Files
- test_data.py      — live market data
- journal.py        — SQLite trade journal
- risk_manager.py   — 8 risk rules, $25k limit
- scanner.py        — momentum breakout scanner
- alerts.py         — Telegram alerts
- alpaca_broker.py  — Alpaca paper trading
- bot.py            — master controller
- dashboard.py      — Flask dashboard at localhost:5000
- backtester.py     — strategy backtester

## How to Run
cd ~/options_bot
source venv/bin/activate

python3.11 bot.py          # run the full bot
python3.11 dashboard.py    # open dashboard
python3.11 backtester.py   # run backtest
python3.11 scanner.py      # quick scan

## What to Do Next
1. Run bot.py every day for 3 months
2. Log every trade and review weekly
3. Improve scanner signals based on real results
4. Only consider live trading after:
   - 100+ paper trades
   - Win rate above 45%
   - Profit factor above 1.5
   - Max drawdown below 15%

## Key Commands
- Start bot    : python3.11 bot.py
- Dashboard    : python3.11 dashboard.py → http://127.0.0.1:5000
- Backtest     : python3.11 backtester.py
- Activate env : source venv/bin/activate