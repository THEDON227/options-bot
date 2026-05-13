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
        f"🚨 *Signal Found*\n\n"
        f"*Symbol:* {symbol}\n"
        f"*Strategy:* {strategy}\n"
        f"*Price:* ${price}\n"
        f"*RSI:* {rsi}\n"
        f"*Score:* {score}\n\n"
        f"{reason}"
    )

    send_alert(message)


def alert_trade_opened(symbol, option_type, strike, entry, stop, target, trade_id):
    message = (
        f"✅ *Trade Opened*\n\n"
        f"*Trade ID:* {trade_id}\n"
        f"*Symbol:* {symbol}\n"
        f"*Type:* {option_type}\n"
        f"*Strike:* {strike}\n\n"
        f"*Entry:* ${entry}\n"
        f"*Stop:* ${stop}\n"
        f"*Target:* ${target}"
    )

    send_alert(message)


def alert_risk_rejected(symbol, reason):
    message = (
        f"❌ *Risk Rejected*\n\n"
        f"*Symbol:* {symbol}\n"
        f"*Reason:* {reason}"
    )

    send_alert(message)


def alert_daily_summary(summary):
    message = f"📊 *Daily Summary*\n\n{summary}"
    send_alert(message)
from dotenv import load_dotenv

load_dotenv()

TOKEN   = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_alert(message: str):
    if not TOKEN or not CHAT_ID:
        print("Telegram not configured. Skipping alert.")
        return
    url  = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("Alert sent to Telegram.")
        else:
            print(f"Telegram error: {response.text}")
    except Exception as e:
        print(f"Alert failed: {e}")

def alert_signal(symbol, strategy, price, rsi, score, reason):
    msg = (
        f"*SIGNAL DETECTED*\n"
        f"Symbol   : {symbol}\n"
        f"Strategy : {strategy}\n"
        f"Price    : {price}\n"
        f"RSI      : {rsi}\n"
        f"Score    : {score}\n"
        f"Reason   : {reason.replace('$', '')}"
    )
    send_alert(msg)

def alert_trade_opened(symbol, option_type, strike, entry, stop, target, trade_id):
    msg = (
        f"*PAPER TRADE OPENED*\n"
        f"ID       : {trade_id}\n"
        f"Symbol   : {symbol}\n"
        f"Type     : {option_type.upper()}\n"
        f"Strike   : ${strike}\n"
        f"Entry    : ${entry}\n"
        f"Stop     : ${stop}\n"
        f"Target   : ${target}\n"
        f"Max risk : ${round(entry * 100, 2)}"
    )
    send_alert(msg)

def alert_trade_closed(symbol, trade_id, pnl, reason):
    emoji = "GREEN" if pnl > 0 else "RED"
    msg = (
        f"*PAPER TRADE CLOSED — {emoji}*\n"
        f"ID       : {trade_id}\n"
        f"Symbol   : {symbol}\n"
        f"P&L      : ${pnl:.2f}\n"
        f"Reason   : {reason}"
    )
    send_alert(msg)

def alert_risk_rejected(symbol, reason):
    msg = (
        f"*TRADE REJECTED BY RISK MANAGER*\n"
        f"Symbol : {symbol}\n"
        f"Reason : {reason}"
    )
    send_alert(msg)

def alert_daily_summary(total_trades, open_trades, daily_pnl, win_rate):
    msg = (
        f"*DAILY SUMMARY*\n"
        f"Total trades : {total_trades}\n"
        f"Open trades  : {open_trades}\n"
        f"Daily P&L    : ${daily_pnl:.2f}\n"
        f"Win rate     : {win_rate:.1%}"
    )
    send_alert(msg)

if __name__ == "__main__":
    send_alert("*Options Bot online* — paper trading system connected.")
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
        f"🚨 *Signal Found*\n\n"
        f"*Symbol:* {symbol}\n"
        f"*Strategy:* {strategy}\n"
        f"*Price:* ${price}\n"
        f"*RSI:* {rsi}\n"
        f"*Score:* {score}\n\n"
        f"{reason}"
    )

    send_alert(message)

def alert_trade_opened(symbol, option_type, strike, entry, stop, target, trade_id):
    message = (
        f"✅ *Trade Opened*\n\n"
        f"*Trade ID:* {
