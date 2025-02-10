import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

class CryptoDataLoader:
    def __init__(self):
        self.supported_coins = {
            'BTC-USD': 'Bitcoin',
            'ETH-USD': 'Ethereum',
            'DOGE-USD': 'Dogecoin',
            'SHIB-USD': 'Shiba Inu'
        }

    def get_historical_data(self, symbol, period='1y'):
        """Fetch historical data for a given crypto symbol"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)
            df.index = pd.to_datetime(df.index)
            return df
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None

    def get_current_price(self, symbol):
        """Get current price for a crypto symbol"""
        try:
            ticker = yf.Ticker(symbol)
            return ticker.info['regularMarketPrice']
        except:
            return None

    def get_available_coins(self):
        """Return list of available coins"""
        return self.supported_coins
