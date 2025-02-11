import os
import time
import logging
from typing import Dict, Optional, List, Union
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import yfinance as yf
from sqlalchemy.orm import Session
from utils.database import get_db

logger = logging.getLogger(__name__)

class CryptoDataLoader:
    def __init__(self):
        """Initialize the data loader with supported coins and exchanges"""
        self.supported_coins = {
            'BTC-USD': 'Bitcoin',
            'ETH-USD': 'Ethereum',
            'SOL-USD': 'Solana',
            'DOGE-USD': 'Dogecoin',
            'SHIB-USD': 'Shiba Inu',
            'ADA-USD': 'Cardano',
            'XRP-USD': 'Ripple',
            'DOT-USD': 'Polkadot'
        }

        self._cache = {}
        self._cache_duration = 60  # Reduced cache duration for testing
        self._price_cache = {}

    def get_historical_data(
        self,
        symbol: str,
        period: str = '1d',
        interval: str = '1m'
    ) -> Optional[pd.DataFrame]:
        """Fetch historical data with improved error handling"""
        try:
            if symbol not in self.supported_coins:
                logger.warning(f"Unsupported symbol: {symbol}")
                return None

            cache_key = f"{symbol}_{period}_{interval}"
            cached_data = self._get_from_cache(cache_key)

            if cached_data is not None:
                return cached_data

            logger.info(f"Fetching {symbol} data using yfinance download")
            df = yf.download(
                symbol,
                period=period,
                interval=interval,
                progress=False
            )

            if df.empty:
                logger.warning(f"No data received for {symbol}")
                return None

            # Add technical indicators
            df = self._add_technical_indicators(df)
            self._add_to_cache(cache_key, df)
            return df

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None

    def _get_from_cache(self, key: str) -> Optional[pd.DataFrame]:
        """Get data from cache if valid"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_duration:
                return data.copy()
            del self._cache[key]
        return None

    def _add_to_cache(self, key: str, data: pd.DataFrame):
        """Add data to cache with current timestamp"""
        try:
            self._cache[key] = (data.copy(), time.time())
        except Exception as e:
            logger.error(f"Cache error for {key}: {str(e)}")

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators with error handling"""
        try:
            df = df.copy()

            # Basic indicators
            df['Returns'] = df['Close'].pct_change()
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()

            # RSI
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # MACD
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

            return df

        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            return df

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price with improved error handling"""
        try:
            cache_key = f"{symbol}_price"
            if cache_key in self._price_cache:
                cache_data = self._price_cache[cache_key]
                if time.time() - cache_data['timestamp'] < 5:
                    return cache_data['price']

            logger.info(f"Fetching current price for {symbol}")
            df = yf.download(symbol, period='1d', progress=False)

            if df.empty:
                logger.warning(f"No price data available for {symbol}")
                return None

            price = float(df['Close'].iloc[-1])
            self._price_cache[cache_key] = {
                'price': price,
                'timestamp': time.time()
            }
            return price

        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {str(e)}")
            return None

    def get_available_coins(self) -> Dict[str, str]:
        """Return dictionary of available coins"""
        return self.supported_coins.copy()

    def save_historical_data(
        self,
        symbol: str,
        df: pd.DataFrame,
        session: Optional[Session] = None
    ) -> bool:
        """
        Save historical data to database
        Args:
            symbol: Trading pair symbol
            df: DataFrame with historical data
            session: Optional database session
        """
        try:
            if session is None:
                session = next(get_db())

            # Implementation for saving to database
            # This would use the SQLAlchemy models defined in database.py

            return True

        except Exception as e:
            logger.error(f"Error saving data for {symbol}: {str(e)}")
            return False