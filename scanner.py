import requests
import pandas as pd
import ta
import time
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

@dataclass
class Signal:
    symbol: str
    strategy: str
    direction: str
    underlying_price: float
    rsi: float
    volume_surge: float
    breakout: bool
    score: float
    reason: str

def get_daily_data(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}&outputsize=compact"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        if "Time Series (Daily)" not in data:
            print(f"No data for {symbol}")
            return None
        prices = data["Time Series (Daily)"]
        df = pd.DataFrame.from_dict(prices, orient="index")
        df.columns = ["Open","High","Low","Close","Volume"]
        df = df.astype(float)
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def scan_momentum_breakout(symbol):
    df = get_daily_data(symbol)
    if df is None or len(df) < 25:
        return None
    df["rsi"]     = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
    df["vol_ma"]  = df["Volume"].rolling(20).mean()
    df["high_20"] = df["High"].rolling(20).max().shift(1)
    latest        = df.iloc[-1]
    previous      = df.iloc[-2]
    breakout      = latest["Close"] > latest["high_20"]
    volume_surge  = latest["Volume"] / latest["vol_ma"] if latest["vol_ma"] > 0 else 0
    vol_confirm   = volume_surge > 1.5
    rsi_ok        = 55 < latest["rsi"] < 75
    uptrend       = latest["Close"] > previous["Close"]
    score = sum([
        0.30 if breakout else 0,
        0.25 if vol_confirm else 0,
        0.25 if rsi_ok else 0,
        0.20 if uptrend else 0,
    ])
    if score < 0.75:
        return None
    reason_parts = []
    if breakout:    reason_parts.append(f"broke 20d high ${latest['high_20']:.2f}")
    if vol_confirm: reason_parts.append(f"volume {volume_surge:.1f}x avg")
    if rsi_ok:      reason_parts.append(f"RSI {latest['rsi']:.1f}")
    return Signal(symbol=symbol, strategy="momentum_breakout", direction="long",
                  underlying_price=round(latest["Close"],2), rsi=round(latest["rsi"],1),
                  volume_surge=round(volume_surge,2), breakout=breakout,
                  score=round(score,2), reason=" | ".join(reason_parts))

def run_scan(watchlist):
    print(f"Scanning {len(watchlist)} symbols...")
    print("-" * 55)
    signals = []
    for symbol in watchlist:
        print(f"Scanning {symbol}...", end=" ", flush=True)
        time.sleep(12)
        signal = scan_momentum_breakout(symbol)
        if signal:
            print(f"SIGNAL FOUND - score {signal.score}")
            signals.append(signal)
        else:
            print("no setup")
    print("-" * 55)
    print(f"Scan complete. {len(signals)} signal(s) found.")
    for s in signals:
        print(f"SIGNAL: {s.symbol} | Price: ${s.underlying_price} | RSI: {s.rsi} | Score: {s.score}")
        print(f"  Reason: {s.reason}")
    return signals

if __name__ == "__main__":
    watchlist = ["AAPL","MSFT","NVDA","SPY","QQQ"]
    run_scan(watchlist)