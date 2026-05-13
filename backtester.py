import pandas as pd
import numpy as np
import ta
from dataclasses import dataclass
from typing import List

@dataclass
class BacktestTrade:
    symbol      : str
    entry_date  : str
    exit_date   : str
    entry_price : float
    exit_price  : float
    pnl         : float
    pnl_pct     : float
    exit_reason : str

def get_full_history(symbol: str) -> pd.DataFrame:
    start_prices = {"AAPL": 150.0, "MSFT": 280.0, "SPY": 420.0}
    start_price  = start_prices.get(symbol, 100.0)
    dates        = pd.date_range(start="2022-01-01", end="2024-12-31", freq="B")
    np.random.seed(42)
    trend   = np.linspace(0, 0.4, len(dates))
    noise   = np.random.normal(0.0008, 0.018, len(dates))
    returns = noise + trend / len(dates)
    prices  = [start_price]
    for r in returns[1:]:
        prices.append(prices[-1] * (1 + r))
    prices     = np.array(prices)
    highs      = prices * (1 + abs(np.random.normal(0, 0.008, len(dates))))
    lows       = prices * (1 - abs(np.random.normal(0, 0.008, len(dates))))
    opens      = prices * (1 + np.random.normal(0, 0.005, len(dates)))
    vols       = np.abs(np.random.normal(50_000_000, 15_000_000, len(dates)))
    vol_spikes = np.random.choice(len(dates), size=60, replace=False)
    for i in vol_spikes:
        vols[i] *= np.random.uniform(2.0, 4.0)
    df = pd.DataFrame({
        "Open": opens, "High": highs, "Low": lows,
        "Close": prices, "Volume": vols
    }, index=dates)
    print(f"Generated {len(df)} days for {symbol} | Start: ${prices[0]:.2f} | End: ${prices[-1]:.2f}")
    return df

def run_backtest(symbol: str, start: str, end: str) -> List[BacktestTrade]:
    print(f"\nBacktesting {symbol} from {start} to {end}...")
    df = get_full_history(symbol)
    if df.empty or len(df) < 30:
        print("Not enough data.")
        return []
    df = df.loc[start:end]
    df["rsi"]     = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
    df["vol_ma"]  = df["Volume"].rolling(20).mean()
    df["high_20"] = df["High"].rolling(20).max().shift(1)
    trades      = []
    in_trade    = False
    entry_price = 0.0
    entry_date  = ""
    entry_index = 0
    stop_loss   = 0.0
    profit_target = 0.0
    for i in range(25, len(df)):
        row  = df.iloc[i]
        date = str(df.index[i].date())
        if not in_trade:
            breakout = row["Close"] > row["high_20"]
            rsi_ok   = 52 < row["rsi"] < 78
            if breakout and rsi_ok:
                entry_price   = row["Close"] * 0.015
                stop_loss     = entry_price * 0.50
                profit_target = entry_price * 2.0
                entry_date    = date
                entry_index   = i
                in_trade      = True
        else:
            current_price = row["Close"] * 0.015
            days_held     = i - entry_index
            if current_price >= profit_target:
                pnl = profit_target - entry_price
                trades.append(BacktestTrade(
                    symbol=symbol, entry_date=entry_date, exit_date=date,
                    entry_price=round(entry_price,2), exit_price=round(profit_target,2),
                    pnl=round(pnl*100,2), pnl_pct=round((pnl/entry_price)*100,1),
                    exit_reason="target_hit"
                ))
                in_trade = False
            elif current_price <= stop_loss:
                pnl = stop_loss - entry_price
                trades.append(BacktestTrade(
                    symbol=symbol, entry_date=entry_date, exit_date=date,
                    entry_price=round(entry_price,2), exit_price=round(stop_loss,2),
                    pnl=round(pnl*100,2), pnl_pct=round((pnl/entry_price)*100,1),
                    exit_reason="stop_hit"
                ))
                in_trade = False
            elif days_held >= 20:
                pnl = current_price - entry_price
                trades.append(BacktestTrade(
                    symbol=symbol, entry_date=entry_date, exit_date=date,
                    entry_price=round(entry_price,2), exit_price=round(current_price,2),
                    pnl=round(pnl*100,2), pnl_pct=round((pnl/entry_price)*100,1),
                    exit_reason="time_exit"
                ))
                in_trade = False
    return trades

def print_results(trades: List[BacktestTrade], symbol: str):
    if not trades:
        print("No trades generated.")
        return
    wins          = [t for t in trades if t.pnl > 0]
    losses        = [t for t in trades if t.pnl <= 0]
    total_pnl     = sum(t.pnl for t in trades)
    win_rate      = len(wins) / len(trades)
    avg_win       = sum(t.pnl for t in wins)   / len(wins)   if wins   else 0
    avg_loss      = sum(t.pnl for t in losses) / len(losses) if losses else 0
    profit_factor = abs(sum(t.pnl for t in wins) / sum(t.pnl for t in losses)) if losses else 0
    expectancy    = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
    print("\n" + "=" * 55)
    print(f"BACKTEST RESULTS — {symbol}")
    print("=" * 55)
    print(f"Total trades   : {len(trades)}")
    print(f"Winners        : {len(wins)}")
    print(f"Losers         : {len(losses)}")
    print(f"Win rate       : {win_rate:.1%}")
    print(f"Avg win        : ${avg_win:.2f}")
    print(f"Avg loss       : ${avg_loss:.2f}")
    print(f"Profit factor  : {profit_factor:.2f}")
    print(f"Expectancy     : ${expectancy:.2f}")
    print(f"Total P&L      : ${total_pnl:.2f}")
    print("=" * 55)
    if len(trades) < 20:
        print("WARNING: Less than 20 trades — not enough data to trust results.")
    if profit_factor < 1.5:
        print("WARNING: Profit factor below 1.5 — needs improvement before live trading.")
    if win_rate < 0.45:
        print("WARNING: Win rate below 45% — review strategy logic.")
    if profit_factor >= 1.5 and win_rate >= 0.45 and len(trades) >= 20:
        print("PASS: Strategy meets minimum criteria. Continue paper trading to confirm.")
    print("\nTrade log (last 10):")
    print(f"{'Entry':<12} {'Exit':<12} {'P&L':>8} {'Reason'}")
    print("-" * 50)
    for t in trades[-10:]:
        print(f"{t.entry_date:<12} {t.exit_date:<12} {t.pnl:>8.2f} {t.exit_reason}")

if __name__ == "__main__":
    symbols = ["AAPL", "MSFT", "SPY"]
    for symbol in symbols:
        trades = run_backtest(symbol, start="2022-01-01", end="2024-12-31")
        print_results(trades, symbol)
        print()