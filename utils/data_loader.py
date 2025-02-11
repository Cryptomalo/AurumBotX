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

        self.timeframes = {
            '1m': '1Min',
            '5m': '5Min',
            '15m': '15Min',
            '30m': '30Min',
            '1h': '1H',
            '4h': '4H',
            '1d': '1D',
            '1w': '1W'
        }

        self._cache = {}
        self._cache_duration = 300  # 5 minutes cache

    def _get_from_cache(self, key: str) -> Optional[pd.DataFrame]:
        """Get data from cache if valid"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_duration:
                return data
            else:
                del self._cache[key]
        return None

    def _add_to_cache(self, key: str, data: pd.DataFrame):
        """Add data to cache with current timestamp"""
        self._cache[key] = (data, time.time())

    def get_historical_data(
        self, 
        symbol: str, 
        period: str = '1y',
        interval: str = '1d'
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical data with caching and error handling

        Args:
            symbol: Trading pair symbol
            period: Time period to fetch ('1d','5d','1mo','3mo','6mo','1y','2y','5y','10y','ytd','max')
            interval: Data interval ('1m','2m','5m','15m','30m','60m','90m','1h','1d','5d','1wk','1mo','3mo')
        """
        try:
            cache_key = f"{symbol}_{period}_{interval}"
            cached_data = self._get_from_cache(cache_key)

            if cached_data is not None:
                logger.debug(f"Retrieved {symbol} data from cache")
                return cached_data

            logger.info(f"Fetching {symbol} data for period {period}")
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)

            if df.empty:
                logger.warning(f"No data received for {symbol}")
                return None

            # Add technical indicators
            df = self._add_technical_indicators(df)

            # Cache the processed data
            self._add_to_cache(cache_key, df)

            return df

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add basic technical indicators to the dataframe"""
        try:
            # Calculate returns
            df['Returns'] = df['Close'].pct_change()

            # Volatility
            df['Volatility'] = df['Returns'].rolling(window=20).std()

            # Volume metrics
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']

            # Price metrics
            df['Price_MA_50'] = df['Close'].rolling(window=50).mean()
            df['Price_MA_200'] = df['Close'].rolling(window=200).mean()

            return df

        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            return df

    def get_market_data(
        self,
        symbols: Union[str, List[str]],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = '1d'
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch market data for multiple symbols

        Args:
            symbols: Single symbol or list of symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        market_data = {}
        for symbol in symbols:
            try:
                df = self.get_historical_data(
                    symbol,
                    interval=interval
                )
                if df is not None:
                    if start_date:
                        df = df[df.index >= start_date]
                    if end_date:
                        df = df[df.index <= end_date]
                    market_data[symbol] = df

            except Exception as e:
                logger.error(f"Error fetching {symbol}: {str(e)}")
                continue

        return market_data

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol with error handling"""
        try:
            ticker = yf.Ticker(symbol)
            return ticker.info.get('regularMarketPrice')
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {str(e)}")
            return None

    def get_available_coins(self) -> Dict[str, str]:
        """Return dictionary of available coins"""
        return self.supported_coins

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