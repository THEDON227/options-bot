import requests
import pandas as pd
import ta
import time
import os
from dataclasses import dataclass
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

    url = (
        "https://www.alphavantage.co/query"
        f"?function=TIME_SERIES_DAILY"
        f"&symbol={symbol}"
        f"&apikey={API_KEY}"
        f"&outputsize=compact"
    )

    try:

        r = requests.get(url, timeout=20)

        data = r.json()

        if "Time Series (Daily)" not in data:
            print(f"No data for {symbol}")
            return None

        prices = data["Time Series (Daily)"]

        df = pd.DataFrame.from_dict(
            prices,
            orient="index"
        )

        df.columns = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]

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

    df["rsi"] = ta.momentum.RSIIndicator(
        df["Close"],
        window=14
    ).rsi()

    df["ema20"] = ta.trend.EMAIndicator(
        df["Close"],
        window=20
    ).ema_indicator()

    df["ema50"] = ta.trend.EMAIndicator(
        df["Close"],
        window=50
    ).ema_indicator()

    df["vol_ma"] = df["Volume"].rolling(20).mean()

    df["high_20"] = (
        df["High"]
        .rolling(20)
        .max()
        .shift(1)
    )

    latest = df.iloc[-1]

    breakout = latest["Close"] > latest["high_20"]

    trend_confirmed = (
        latest["ema20"] > latest["ema50"]
    )

    rsi_ok = 55 <= latest["rsi"] <= 72

    volume_surge = (
        latest["Volume"] / latest["vol_ma"]
        if latest["vol_ma"] > 0 else 0
    )

    volume_confirmed = volume_surge > 1.5

    score = 0

    if breakout:
        score += 0.30

    if trend_confirmed:
        score += 0.25

    if rsi_ok:
        score += 0.25

    if volume_confirmed:
        score += 0.20

    score = round(score, 2)

    if score < 0.75:
        return None

    reasons = []

    if breakout:
        reasons.append("20d breakout")

    if trend_confirmed:
        reasons.append("EMA trend confirmed")

    if rsi_ok:
        reasons.append(f"RSI {latest['rsi']:.1f}")

    if volume_confirmed:
        reasons.append(f"Volume {volume_surge:.1f}x")

    return Signal(
        symbol=symbol,
        strategy="ai_momentum_breakout",
        direction="long",
        underlying_price=round(latest["Close"],2),
        rsi=round(latest["rsi"],1),
        volume_surge=round(volume_surge,2),
        breakout=breakout,
        score=score,
        reason=" | ".join(reasons)
    )

def run_scan(watchlist):

    print()
    print("=" * 70)
    print("AI OPTIONS ENGINE SCAN")
    print("=" * 70)

    signals = []

    for symbol in watchlist:

        print(f"Scanning {symbol}...", end=" ")

        signal = scan_momentum_breakout(symbol)

        if signal:

            print(f"SIGNAL FOUND score={signal.score}")

            signals.append(signal)

        else:

            print("no setup")

        time.sleep(12)

    print()
    print("=" * 70)
    print(f"SCAN COMPLETE | {len(signals)} SIGNALS")
    print("=" * 70)

    for s in signals:

        print(
            f"{s.symbol} | "
            f"${s.underlying_price} | "
            f"RSI {s.rsi} | "
            f"Score {s.score}"
        )

    return signals

if __name__ == "__main__":

    WATCHLIST = [
        "AAPL",
        "MSFT",
        "NVDA",
        "SPY",
        "QQQ",
        "TSLA",
        "AMZN",
        "META"
    ]

    while True:

        try:

            run_scan(WATCHLIST)

        except Exception as e:

            print(f"SCAN ERROR: {e}")

        print()
        print("Sleeping 300 seconds...")
        print()

        time.sleep(300)
