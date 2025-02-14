import os
import time
import logging
import asyncio
from typing import Dict, Optional, List, Union
from datetime import datetime, timedelta
import concurrent.futures

import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class CryptoDataLoader:
    def __init__(self, use_live_data: bool = True, testnet: bool = True):
        """Initialize the data loader with supported coins and advanced caching"""
        self.use_live_data = use_live_data
        self.testnet = testnet
        self.supported_coins = {
            'BTCUSDT': 'Bitcoin',
            'ETHUSDT': 'Ethereum',
            'SOLUSDT': 'Solana',
            'DOGEUSDT': 'Dogecoin',
            'SHIBUSDT': 'Shiba Inu',
            'ADAUSDT': 'Cardano',
            'XRPUSDT': 'Ripple',
            'DOTUSDT': 'Polkadot',
            'MATICUSDT': 'Polygon',
            'AVAXUSDT': 'Avalanche'
        }

        self._cache = {}
        self._cache_duration = {
            '1m': 60,    # 1 minute cache for 1m data
            '5m': 300,   # 5 minutes cache for 5m data
            '15m': 900,  # 15 minutes cache for 15m data
            '1h': 3600,  # 1 hour cache for 1h data
            '4h': 14400, # 4 hours cache for 4h data
            '1d': 86400  # 1 day cache for daily data
        }

        if self.use_live_data:
            self._setup_client()
        self._setup_database()

    def _setup_client(self):
        """Setup Binance client connection synchronously"""
        try:
            api_key = os.environ.get('BINANCE_API_KEY')
            api_secret = os.environ.get('BINANCE_API_SECRET')

            if not api_key or not api_secret:
                raise ValueError("API credentials not found")

            self.client = Client(
                api_key,
                api_secret,
                testnet=self.testnet,
                tld='us' if not self.testnet else None
            )
            logger.info("Binance client initialized successfully")

            # Test connection synchronously
            self.client.ping()
            logger.info("Binance API connection test successful")
        except BinanceAPIException as e:
            logger.error(f"Binance API error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Client setup error: {e}", exc_info=True)
            raise

    def _setup_database(self):
        """Setup database connection synchronously"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                self.engine = create_engine(database_url)
                logger.info("Database connection established")
            else:
                logger.warning("DATABASE_URL not found, running without persistent storage")
                self.engine = None
        except Exception as e:
            logger.error(f"Database setup error: {e}", exc_info=True)
            self.engine = None

    async def get_historical_data_async(
        self,
        symbol: str,
        period: str = '1d',
        interval: str = '1m'
    ) -> Optional[pd.DataFrame]:
        """Async wrapper for get_historical_data"""
        try:
            return await asyncio.to_thread(
                self.get_historical_data,
                symbol,
                period,
                interval
            )
        except Exception as e:
            logger.error(f"Error in async historical data fetch: {e}")
            return None

    def get_historical_data(
        self,
        symbol: str,
        period: str = '1d',
        interval: str = '1m'
    ) -> Optional[pd.DataFrame]:
        """Synchronous method to fetch historical data"""
        try:
            if not self.client and self.use_live_data:
                raise ValueError("Client not initialized")

            symbol = self._normalize_symbol(symbol)
            if symbol not in self.supported_coins:
                logger.warning(f"Unsupported symbol: {symbol}")
                return None

            cache_key = f"{symbol}_{period}_{interval}"
            cached_data = self._get_from_cache(cache_key, interval)
            if cached_data is not None:
                return cached_data

            logger.info(f"Fetching {symbol} data for period {period}")

            if not self.use_live_data:
                return self._get_mock_data(symbol, period, interval)

            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                startTime=self._get_start_time(period),
                limit=1000
            )

            if not klines:
                logger.warning(f"No data received for {symbol}")
                return None

            df = self._process_klines_data(klines)
            df = self._add_technical_indicators(df)

            # Save to cache and database
            self._add_to_cache(cache_key, df)
            self._save_to_database(symbol, df)

            return df

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}", exc_info=True)
            return None

    def _get_start_time(self, period: str) -> Optional[int]:
        """Calculate start time based on period"""
        period_map = {
            '1d': timedelta(days=1),
            '7d': timedelta(days=7),
            '30d': timedelta(days=30)
        }
        delta = period_map.get(period)
        if delta:
            return int((datetime.now() - delta).timestamp() * 1000)
        return None

    def _process_klines_data(self, klines: List) -> pd.DataFrame:
        """Process raw klines data into DataFrame"""
        df = pd.DataFrame(
            klines,
            columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'
            ]
        )

        # Convert string values to float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        # Drop unnecessary columns
        return df[['open', 'high', 'low', 'close', 'volume']]

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for exchange"""
        return symbol.replace('-', '').replace('/', '')

    def _get_from_cache(self, key: str, interval: str = '1m') -> Optional[pd.DataFrame]:
        """Get data from cache if valid"""
        try:
            if key in self._cache:
                data, timestamp = self._cache[key]
                cache_duration = self._cache_duration.get(interval, 300)
                if time.time() - timestamp < cache_duration:
                    logger.debug(f"Cache hit for {key}")
                    return data.copy()
                logger.debug(f"Cache expired for {key}")
                del self._cache[key]
            return None
        except Exception as e:
            logger.error(f"Cache error for {key}: {e}", exc_info=True)
            return None

    def _add_to_cache(self, key: str, data: pd.DataFrame):
        """Add data to cache with memory management"""
        try:
            if len(self._cache) > 100:  # Maximum 100 cached items
                oldest_key = min(self._cache.items(), key=lambda x: x[1][1])[0]
                del self._cache[oldest_key]

            self._cache[key] = (data.copy(), time.time())
            logger.debug(f"Added to cache: {key}")
        except Exception as e:
            logger.error(f"Cache error for {key}: {e}", exc_info=True)

    def _save_to_database(self, symbol: str, df: pd.DataFrame):
        """Save market data to database for historical analysis"""
        if not self.engine:
            return

        try:
            table_name = f"market_data_{symbol.lower()}"
            df.to_sql(
                table_name,
                self.engine,
                if_exists='append',
                index=True
            )
            logger.debug(f"Saved {len(df)} rows to database for {symbol}")
        except Exception as e:
            logger.error(f"Database error for {symbol}: {e}", exc_info=True)

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate basic technical indicators"""
        try:
            df = df.copy()

            # Basic metrics
            df['Returns'] = df['close'].pct_change()
            df['Volatility'] = df['Returns'].rolling(window=20).std()
            df['Volume_MA'] = df['volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['volume'] / df['Volume_MA']

            # Moving averages
            df['SMA_20'] = df['close'].rolling(window=20).mean()
            df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()

            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # Clean up NaN values
            df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)

            return df

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}", exc_info=True)
            return df

    def _get_mock_data(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        """Generate mock data for testing"""
        periods = {'1d': 1440, '7d': 10080, '30d': 43200}
        n_periods = periods.get(period, 1440)  # Default to 1 day

        timestamps = pd.date_range(
            end=datetime.now(),
            periods=n_periods,
            freq='1min'
        )

        np.random.seed(42)  # For reproducible mock data
        close_price = 100 * (1 + np.random.randn(n_periods).cumsum() * 0.02)

        df = pd.DataFrame({
            'open': close_price * (1 + np.random.randn(n_periods) * 0.001),
            'high': close_price * (1 + abs(np.random.randn(n_periods) * 0.002)),
            'low': close_price * (1 - abs(np.random.randn(n_periods) * 0.002)),
            'close': close_price,
            'volume': np.random.randint(1000, 100000, n_periods)
        }, index=timestamps)

        return self._add_technical_indicators(df)

    def get_market_summary(self, symbol: str) -> Dict[str, Union[float, str]]:
        """Get comprehensive market summary"""
        try:
            symbol = self._normalize_symbol(symbol)
            df = self.get_historical_data(symbol, period='1d')
            if df is None or df.empty:
                return {}

            current_price = df['close'].iloc[-1]
            previous_close = df['close'].iloc[-2]
            price_change = ((current_price - previous_close) / previous_close) * 100

            return {
                'current_price': current_price,
                'price_change_24h': price_change,
                'volume_24h': df['volume'].sum(),
                'high_24h': df['high'].max(),
                'low_24h': df['low'].min(),
                'volatility': df['Returns'].std() * 100,
                'rsi': df['RSI'].iloc[-1],
                'trend': 'Bullish' if current_price > df['SMA_20'].iloc[-1] else 'Bearish'
            }

        except Exception as e:
            logger.error(f"Error getting market summary for {symbol}: {e}", exc_info=True)
            return {}

    def get_available_coins(self) -> Dict[str, str]:
        """Return dictionary of supported cryptocurrencies"""
        return self.supported_coins.copy()