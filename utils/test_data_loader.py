import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime
from utils.data_loader import CryptoDataLoader

class TestCryptoDataLoader(unittest.TestCase):
    def setUp(self):
        self.data_loader = CryptoDataLoader()
        self.test_symbol = "BTC-USD"

    @patch('yfinance.Ticker')
    def test_get_historical_data(self, mock_ticker):
        # Prepare mock data
        mock_data = pd.DataFrame({
            'Open': [40000, 41000],
            'High': [42000, 43000],
            'Low': [39000, 40000],
            'Close': [41000, 42000],
            'Volume': [1000000, 1100000]
        }, index=[datetime.now(), datetime.now()])

        mock_ticker.return_value.history.return_value = mock_data

        # Test data retrieval
        df = self.data_loader.get_historical_data(self.test_symbol, period='1d')

        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        self.assertTrue(all(col in df.columns for col in ['Close', 'Volume', 'Returns']))

    def test_get_available_coins(self):
        coins = self.data_loader.get_available_coins()
        self.assertIsInstance(coins, dict)
        self.assertIn('BTC-USD', coins)
        self.assertIn('ETH-USD', coins)

    @patch('yfinance.Ticker')
    def test_get_current_price(self, mock_ticker):
        mock_ticker.return_value.info = {'regularMarketPrice': 42000.0}
        price = self.data_loader.get_current_price(self.test_symbol)
        self.assertIsInstance(price, float)
        self.assertEqual(price, 42000.0)

    @patch('yfinance.Ticker')
    def test_error_handling(self, mock_ticker):
        mock_ticker.return_value.history.side_effect = Exception("API Error")
        df = self.data_loader.get_historical_data(self.test_symbol)
        self.assertIsNone(df)

if __name__ == '__main__':
    unittest.main()