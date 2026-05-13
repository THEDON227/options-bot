import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY  = os.getenv("ALPACA_API_KEY")
SECRET   = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = os.getenv("ALPACA_BASE_URL")

HEADERS = {
    "APCA-API-KEY-ID"    : API_KEY,
    "APCA-API-SECRET-KEY": SECRET,
    "Content-Type"       : "application/json"
}

def get_account():
    r = requests.get(f"{BASE_URL}/account", headers=HEADERS)
    return r.json()

def get_positions():
    r = requests.get(f"{BASE_URL}/positions", headers=HEADERS)
    return r.json()

def get_orders():
    r = requests.get(f"{BASE_URL}/orders", headers=HEADERS)
    return r.json()

def place_market_order(symbol, qty, side):
    payload = {
        "symbol"        : symbol,
        "qty"           : qty,
        "side"          : side,
        "type"          : "market",
        "time_in_force" : "day"
    }
    r = requests.post(f"{BASE_URL}/orders", headers=HEADERS, json=payload)
    return r.json()

def close_position(symbol):
    r = requests.delete(f"{BASE_URL}/positions/{symbol}", headers=HEADERS)
    return r.json()

if __name__ == "__main__":
    print("Connecting to Alpaca paper account...")
    account = get_account()

    if "code" in account:
        print(f"Error: {account}")
    else:
        print(f"Account ID     : {account.get('id')}")
        print(f"Status         : {account.get('status')}")
        print(f"Portfolio value: ${float(account.get('portfolio_value', 0)):,.2f}")
        print(f"Cash           : ${float(account.get('cash', 0)):,.2f}")
        print(f"Buying power   : ${float(account.get('buying_power', 0)):,.2f}")
        print("Alpaca connection successful.")