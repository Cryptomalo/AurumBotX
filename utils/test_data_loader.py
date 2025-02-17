import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime
from utils.data_loader import CryptoDataLoader
import pandas.api.types as pdtypes


class TestCryptoDataLoader(unittest.TestCase):
    def setUp(self):
        self.data_loader = CryptoDataLoader(use_live_data=False)  # Use mock data
        self.test_symbol = "BTCUSDT"

    def test_normalize_symbol(self):
        """Test symbol normalization"""
        self.assertEqual(self.data_loader._normalize_symbol("BTC-USD"), "BTC/USD")
        self.assertEqual(self.data_loader._normalize_symbol("BTC/USD"), "BTC/USD")
        self.assertEqual(self.data_loader._normalize_symbol("BTCUSDT"), "BTCUSDT")

    @patch('utils.data_loader.Client')
    def test_get_historical_data(self, mock_client_class):
        """Test data retrieval with proper type checking"""
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Prepare mock data with all required columns
        mock_klines = [
            [1612137600000, "40000", "42000", "39000", "41000", "1000000",
             1612138500000, "42000000", 1000, "500000", "20500000", "0"],
        ]
        mock_client.get_klines.return_value = mock_klines

        # Set client instance
        self.data_loader.client = mock_client
        self.data_loader.use_live_data = True

        # Test data retrieval
        df = self.data_loader.get_historical_data(self.test_symbol, period='1d')

        # Verify mock was called correctly
        mock_client.get_klines.assert_called_once()

        # Verify returned dataframe
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        # Check all required columns are present
        required_columns = [
            'Open', 'High', 'Low', 'Close', 'Volume',
            'Returns', 'Volatility', 'Volume_MA', 'Volume_Ratio',
            'SMA_20', 'SMA_50', 'SMA_200', 'EMA_20', 'EMA_50', 'EMA_200',
            'MACD', 'MACD_Signal', 'MACD_Hist', 'RSI', 'ATR',
            'BB_Middle', 'BB_Upper', 'BB_Lower', 'BB_Width'
        ]

        self.assertTrue(
            all(col in df.columns for col in required_columns),
            f"Missing columns: {[col for col in required_columns if col not in df.columns]}"
        )

        # Verify data types
        numeric_columns = [col for col in required_columns if col != 'timestamp']
        for col in numeric_columns:
            self.assertTrue(
                pdtypes.is_numeric_dtype(df[col]),
                f"Column {col} is not numeric"
            )

    def test_get_available_coins(self):
        coins = self.data_loader.get_available_coins()
        self.assertIsInstance(coins, dict)
        self.assertIn('BTC/USD', coins)
        self.assertIn('ETH/USD', coins)

    @patch('utils.data_loader.Client')
    def test_get_current_price(self, mock_client_class):
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Configure mock
        mock_klines = [[1612137600000, "40000", "42000", "39000", "41000", "1000000"]]
        mock_client.get_klines.return_value = mock_klines

        # Set client instance
        self.data_loader.client = mock_client
        self.data_loader.use_live_data = True

        # Test price retrieval
        price = self.data_loader.get_current_price(self.test_symbol)

        # Verify mock was called
        mock_client.get_klines.assert_called_once_with(
            symbol=self.test_symbol,
            interval='1m',
            limit=1
        )

        # Verify price
        self.assertIsInstance(price, float)
        self.assertEqual(price, 41000.0)

    @patch('utils.data_loader.Client')
    def test_error_handling(self, mock_client_class):
        """Test error handling during data fetching"""
        # Configure mock to raise exception
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_klines.side_effect = Exception("API Error")

        # Set client instance
        self.data_loader.client = mock_client
        self.data_loader.use_live_data = True

        # Test error handling with live data - should return mock data
        df = self.data_loader.get_historical_data(self.test_symbol)
        self.assertIsNotNone(df)  # Should return mock data
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        # Test with unsupported symbol
        df = self.data_loader.get_historical_data("INVALID-SYMBOL")
        self.assertIsNone(df)  # Should return None for unsupported symbols

    def test_process_klines_data(self):
        """Test klines data processing with standardized column names"""
        mock_klines = [
            [1612137600000, "40000", "42000", "39000", "41000", "1000000",
             1612138500000, "42000000", 1000, "500000", "20500000", "0"],
            [1612138500000, "41000", "43000", "40000", "42000", "1100000",
             1612139400000, "44000000", 1100, "550000", "21000000", "0"]
        ]

        df = self.data_loader._process_klines_data(mock_klines)

        # Check required columns exist
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            self.assertIn(col, df.columns, f"Missing required column: {col}")

        # Check data types
        self.assertTrue(all(df[col].dtype == np.float64 for col in required_columns))

        # Check calculated columns
        self.assertIn('Returns', df.columns)
        self.assertEqual(len(df), 2)

    def test_add_technical_indicators(self):
        """Test technical indicators calculation"""
        # Create sample data
        df = pd.DataFrame({
            'Open': [100, 101, 102, 103, 104],
            'High': [105, 106, 107, 108, 109],
            'Low': [95, 96, 97, 98, 99],
            'Close': [102, 103, 104, 105, 106],
            'Volume': [1000, 1100, 1200, 1300, 1400]
        }, index=pd.date_range(start='2025-01-01', periods=5))

        result = self.data_loader._add_technical_indicators(df)

        # Check if technical indicators are calculated
        expected_indicators = [
            'Returns', 'Volatility', 'Volume_MA', 'Volume_Ratio',
            'SMA_20', 'EMA_20', 'MACD', 'RSI', 'BB_Middle', 'BB_Upper', 'BB_Lower'
        ]
        for indicator in expected_indicators:
            self.assertIn(indicator, result.columns)


if __name__ == '__main__':
    unittest.main()