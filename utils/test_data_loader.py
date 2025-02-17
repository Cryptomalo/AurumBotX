import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime
from utils.data_loader import CryptoDataLoader
import pandas.api.types as pdtypes
from typing import Dict, List, Optional, Union, Any

@pytest_asyncio.fixture
def data_loader():
    """Create a test instance of CryptoDataLoader"""
    return CryptoDataLoader(use_live_data=False)  # Use mock data

def test_normalize_symbol(data_loader):
    """Test symbol normalization with proper type hints"""
    assert data_loader._normalize_symbol("BTC-USD") == "BTCUSDT"
    assert data_loader._normalize_symbol("BTC/USD") == "BTCUSDT"
    assert data_loader._normalize_symbol("BTCUSD") == "BTCUSDT"
    assert data_loader._normalize_symbol("BTCUSDT") == "BTCUSDT"

@pytest.mark.asyncio
async def test_get_historical_data(data_loader):
    """Test data retrieval with async support"""
    test_symbol = "BTCUSDT"

    # Test data retrieval
    df = await data_loader.get_historical_data(test_symbol, period='1d')

    # Verify returned dataframe
    assert df is not None, "DataFrame should not be None"
    assert isinstance(df, pd.DataFrame)

    # Check non-empty DataFrame
    assert len(df) > 0, "DataFrame should not be empty"

    # Check all required columns are present and numeric
    required_columns = [
        'Open', 'High', 'Low', 'Close', 'Volume',
        'Returns', 'Volatility', 'Volume_MA', 'Volume_Ratio',
        'SMA_20', 'SMA_50', 'SMA_200'
    ]

    for col in required_columns:
        assert col in df.columns, f"Missing column: {col}"
        assert pdtypes.is_numeric_dtype(df[col]), f"Column {col} is not numeric"

def test_get_available_coins(data_loader):
    """Test available coins retrieval"""
    coins = data_loader.get_available_coins()
    assert isinstance(coins, dict)
    assert len(coins) > 0, "Should return at least one coin"
    assert 'BTC/USD' in coins
    assert 'ETH/USD' in coins

@pytest.mark.asyncio
async def test_get_market_summary(data_loader):
    """Test market summary retrieval with async support"""
    test_symbol = "BTCUSDT"
    summary = await data_loader.get_market_summary(test_symbol)
    assert isinstance(summary, dict)

    required_keys = [
        'current_price', 'price_change_24h', 'volume_24h',
        'high_24h', 'low_24h', 'volatility', 'rsi', 'trend'
    ]
    for key in required_keys:
        assert key in summary, f"Missing key: {key}"

@pytest.mark.asyncio
async def test_error_handling(data_loader):
    """Test error handling with async support"""
    # Test with unsupported symbol
    df = await data_loader.get_historical_data("INVALID-SYMBOL")
    assert df is None, "Should return None for unsupported symbols"

    # Test with valid symbol but invalid period
    df = await data_loader.get_historical_data("BTCUSDT", period='invalid')
    assert df is not None, "Should return mock data for invalid period"