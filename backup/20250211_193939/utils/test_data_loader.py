import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime
from utils.data_loader import CryptoDataLoader

class TestCryptoDataLoader(unittest.TestCase):
    def setUp(self):
        self.data_loader = CryptoDataLoader()
        self.test_symbol = "BTC/USD"

    def test_normalize_symbol(self):
        """Test symbol normalization"""
        self.assertEqual(self.data_loader._normalize_symbol("BTC-USD"), "BTC/USD")
        self.assertEqual(self.data_loader._normalize_symbol("BTC/USD"), "BTC/USD")

    @patch('ccxt.binanceus')
    def test_get_historical_data(self, mock_exchange_class):
        # Setup mock exchange
        mock_exchange = MagicMock()
        mock_exchange_class.return_value = mock_exchange

        # Prepare mock data
        mock_ohlcv = [
            [1612137600000, 40000, 42000, 39000, 41000, 1000000],
            [1612138500000, 41000, 43000, 40000, 42000, 1100000]
        ]
        mock_exchange.fetch_ohlcv.return_value = mock_ohlcv

        # Set exchange instance
        self.data_loader.exchange = mock_exchange

        # Test data retrieval
        df = self.data_loader.get_historical_data(self.test_symbol, period='1d')

        # Verify mock was called correctly
        mock_exchange.fetch_ohlcv.assert_called_once()

        # Verify returned dataframe
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        self.assertTrue(all(col in df.columns for col in ['Close', 'Volume', 'Returns']))

    def test_get_available_coins(self):
        coins = self.data_loader.get_available_coins()
        self.assertIsInstance(coins, dict)
        self.assertIn('BTC/USD', coins)
        self.assertIn('ETH/USD', coins)

    @patch('ccxt.binanceus')
    def test_get_current_price(self, mock_exchange_class):
        # Setup mock exchange
        mock_exchange = MagicMock()
        mock_exchange_class.return_value = mock_exchange

        # Configure mock
        mock_exchange.fetch_ticker.return_value = {'last': 42000.0}

        # Set exchange instance
        self.data_loader.exchange = mock_exchange

        # Test price retrieval
        price = self.data_loader.get_current_price(self.test_symbol)

        # Verify mock was called
        mock_exchange.fetch_ticker.assert_called_once_with(self.test_symbol)

        # Verify price
        self.assertIsInstance(price, float)
        self.assertEqual(price, 42000.0)

    @patch('ccxt.binanceus')
    def test_error_handling(self, mock_exchange_class):
        # Setup mock exchange
        mock_exchange = MagicMock()
        mock_exchange_class.return_value = mock_exchange

        # Configure mock to raise exception
        mock_exchange.fetch_ohlcv.side_effect = Exception("API Error")

        # Set exchange instance
        self.data_loader.exchange = mock_exchange

        # Test error handling
        df = self.data_loader.get_historical_data(self.test_symbol)
        self.assertIsNone(df)

if __name__ == '__main__':
    unittest.main()