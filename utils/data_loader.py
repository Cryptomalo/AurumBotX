import os
import time
import logging
from typing import Dict, Optional, List
from datetime import datetime

import pandas as pd
import numpy as np
import yfinance as yf

logger = logging.getLogger(__name__)

class CryptoDataLoader:
    def __init__(self):
        """Initialize the data loader with supported coins"""
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
        self._cache_duration = 60  # Cache duration in seconds

    def get_historical_data(
        self,
        symbol: str,
        period: str = '1d',
        interval: str = '1m'
    ) -> Optional[pd.DataFrame]:
        """Fetch historical data for a cryptocurrency"""
        try:
            if symbol not in self.supported_coins:
                logger.warning(f"Unsupported symbol: {symbol}")
                return None

            cache_key = f"{symbol}_{period}_{interval}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                return cached_data

            logger.info(f"Downloading data for {symbol}")
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)

            if df.empty:
                logger.warning(f"No data received for {symbol}")
                return None

            # Add technical indicators
            df = self._add_technical_indicators(df)

            # Save to cache
            self._add_to_cache(cache_key, df)
            return df

        except Exception as e:
            logger.error(f"Error loading data for {symbol}: {str(e)}")
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
        """Add data to cache"""
        try:
            self._cache[key] = (data.copy(), time.time())
        except Exception as e:
            logger.error(f"Cache error for {key}: {str(e)}")

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        try:
            df = df.copy()

            # Calculate returns
            df['Returns'] = df['Close'].pct_change()

            # Volume moving average
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

            # Fill NaN values with 0
            df = df.fillna(0)
            return df

        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            return df

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price"""
        try:
            if symbol not in self.supported_coins:
                logger.warning(f"Unsupported symbol: {symbol}")
                return None

            logger.info(f"Loading price for {symbol}")
            ticker = yf.Ticker(symbol)
            current_price = ticker.info.get('regularMarketPrice')

            if current_price is None:
                logger.warning(f"No price available for {symbol}")
                return None

            return float(current_price)

        except Exception as e:
            logger.error(f"Error loading price for {symbol}: {str(e)}")
            return None

    def get_available_coins(self) -> Dict[str, str]:
        """Return dictionary of supported cryptocurrencies"""
        return self.supported_coins.copy()