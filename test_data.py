import requests
import pandas as pd

API_KEY = "S3FTG6P69V4C9U6S"
symbol = "AAPL"

url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}&outputsize=compact"

print(f"Fetching {symbol} data...")
response = requests.get(url, timeout=15)
data = response.json()

prices = data["Time Series (Daily)"]
df = pd.DataFrame.from_dict(prices, orient="index")
df.columns = ["Open", "High", "Low", "Close", "Volume"]
df = df.astype(float)
df.index = pd.to_datetime(df.index)
df = df.sort_index()

print(df.tail(10))
print("\nLatest close: $", round(df["Close"].iloc[-1], 2))

def get_stock_data(symbol):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=30d"
    
    response = requests.get(url, headers=headers, timeout=15)
    print("Status code:", response.status_code)
    
    data = response.json()
    quotes = data['chart']['result'][0]
    timestamps = quotes['timestamp']
    closes = quotes['indicators']['quote'][0]['close']
    volumes = quotes['indicators']['quote'][0]['volume']
    
    df = pd.DataFrame({
        'Date': pd.to_datetime(timestamps, unit='s'),
        'Close': closes,
        'Volume': volumes
    })
    
    retur
