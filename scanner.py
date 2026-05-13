import requests
import pandas as pd
import ta
import time
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPHAVANTAGE_API_KEY") or os.getenv("ALPHA_VANTAGE_API_KEY")

MIN_SCORE = 0.92

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
    if not API_KEY:
        print("Missing Alpha Vantage API key")
        return None

    url = (
        "https://www.alphavantage.co/query"
        f"?function=TIME_SERIES_DAILY"
        f"&symbol={symbol}"
        f"&apikey={API_KEY}"
        f"&outputsize=compact"
    )

    try:
        response = requests.get(url, timeout=20)
        data = response.json()

        if "Note" in data:
            print(f"Alpha Vantage rate limit for {symbol}")
            return None

        if "Time Series (Daily)" not in data:
            print(f"No data for {symbol}: {data}")
            return None

        prices = data["Time Series (Daily)"]
        df = pd.DataFrame.from_dict(prices, orient="index")
        df.columns = ["Open", "High", "Low", "Close", "Volume"]
        df = df.astype(float)
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()

        return df

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def scan_momentum_breakout(symbol):
    df = get_daily_data(symbol)

    if df is None or len(df) < 60:
        return None

    df["rsi"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
    df["vol_ma"] = df["Volume"].rolling(20).mean()
    df["high_20"] = df["High"].rolling(20).max().shift(1)
    df["ma_20"] = df["Close"].rolling(20).mean()
    df["ma_50"] = df["Close"].rolling(50).mean()

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    breakout = latest["Close"] > latest["high_20"]
    volume_surge = latest["Volume"] / latest["vol_ma"] if latest["vol_ma"] > 0 else 0
    vol_confirm = volume_surge >= 1.5

    rsi = latest["rsi"]
    rsi_ok = 55 <= rsi <= 72

    trend_20 = latest["Close"] > latest["ma_20"]
    trend_50 = latest["Close"] > latest["ma_50"]
    ma_stack = latest["ma_20"] > latest["ma_50"]

    green_day = latest["Close"] > latest["Open"]
    momentum = latest["Close"] > previous["Close"]

    near_high_close = latest["Close"] >= latest["High"] * 0.97

    score = 0

    if breakout:
        score += 0.25
    if vol_confirm:
        score += 0.20
    if rsi_ok:
        score += 0.15
    if trend_20:
        score += 0.10
    if trend_50:
        score += 0.10
    if ma_stack:
        score += 0.08
    if green_day:
        score += 0.05
    if momentum:
        score += 0.04
    if near_high_close:
        score += 0.03

    score = round(score, 2)

    if score < MIN_SCORE:
        return None

    reason_parts = [
        f"score {score}",
        f"close ${latest['Close']:.2f}",
    ]

    if breakout:
        reason_parts.append(f"broke 20d high ${latest['high_20']:.2f}")
    if vol_confirm:
        reason_parts.append(f"volume {volume_surge:.1f}x avg")
    if rsi_ok:
        reason_parts.append(f"RSI {rsi:.1f}")
    if trend_20 and trend_50:
        reason_parts.append("above 20MA and 50MA")
    if ma_stack:
        reason_parts.append("20MA above 50MA")
    if near_high_close:
        reason_parts.append("closed near daily high")

    return Signal(
        symbol=symbol,
        strategy="high_conviction_momentum_breakout",
        direction="long",
        underlying_price=round(latest["Close"], 2),
        rsi=round(rsi, 1),
        volume_surge=round(volume_surge, 2),
        breakout=breakout,
        score=score,
        reason=" | ".join(reason_parts)
    )

def run_scan(watchlist):
    print(f"Scanning {len(watchlist)} symbols...")
    print("-" * 55)

    signals = []

    for symbol in watchlist:
        print(f"Scanning {symbol}...", end=" ", flush=True)

        signal = scan_momentum_breakout(symbol)

        if signal:
            print(f"SIGNAL FOUND - score {signal.score}")
            signals.append(signal)
        else:
            print("no setup")

        time.sleep(12)

    print("-" * 55)
    print(f"Scan complete. {len(signals)} signal(s) found.")

    for s in signals:
        print(f"SIGNAL: {s.symbol} | Price: ${s.underlying_price} | RSI: {s.rsi} | Score: {s.score}")
        print(f"  Reason: {s.reason}")

    return signals

if __name__ == "__main__":
    watchlist = ["AAPL", "MSFT", "NVDA", "SPY", "QQQ"]
    run_scan(watchlist)
