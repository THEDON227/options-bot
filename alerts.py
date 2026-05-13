import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_alert(message):
    if not TOKEN or not CHAT_ID:
        print("Telegram not configured. Skipping alert.")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, data=data, timeout=15)

        if response.status_code == 200:
            print("Telegram alert sent.")
        else:
            print(f"Telegram error: {response.text}")

    except Exception as e:
        print(f"Telegram request failed: {e}")

def alert_signal(symbol, strategy, price, rsi, score, reason):
    message = (
        f"Signal Found\n\n"
        f"Symbol: {symbol}\n"
        f"Strategy: {strategy}\n"
        f"Price: ${price}\n"
        f"RSI: {rsi}\n"
        f"Score: {score}\n\n"
        f"{reason}"
    )
    send_alert(message)

def alert_trade_opened(symbol, option_type, strike, entry, stop, target, trade_id):
    message = (
        f"Trade Opened\n\n"
        f"Trade ID: {trade_id}\n"
        f"Symbol: {symbol}\n"
        f"Type: {option_type}\n"
        f"Strike: {strike}\n\n"
        f"Entry: ${entry}\n"
        f"Stop: ${stop}\n"
        f"Target: ${target}"
    )
    send_alert(message)

def alert_risk_rejected(symbol, reason):
    message = (
        f"Risk Rejected\n\n"
        f"Symbol: {symbol}\n"
        f"Reason: {reason}"
    )
    send_alert(message)

def alert_daily_summary(summary):
    message = f"Daily Summary\n\n{summary}"
    send_alert(message)
