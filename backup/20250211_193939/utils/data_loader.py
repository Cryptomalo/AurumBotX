import os
import time
import logging
from typing import Dict, Optional, List, Union, Tuple
from datetime import datetime, timedelta
import concurrent.futures

import pandas as pd
import numpy as np
import ccxt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class CryptoDataLoader:
    def __init__(self):
        """Initialize the data loader with supported coins and advanced caching"""
        self.supported_coins = {
            'BTC/USD': 'Bitcoin',
            'ETH/USD': 'Ethereum',
            'SOL/USD': 'Solana',
            'DOGE/USD': 'Dogecoin',
            'SHIB/USD': 'Shiba Inu',
            'ADA/USD': 'Cardano',
            'XRP/USD': 'Ripple',
            'DOT/USD': 'Polkadot',
            'MATIC/USD': 'Polygon',
            'AVAX/USD': 'Avalanche'
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

        self._setup_exchange()
        self._setup_database()

    def _setup_exchange(self):
        """Setup ccxt exchange connection"""
        try:
            self.exchange = ccxt.binanceus({
                'enableRateLimit': True,
                'options': {
                    'adjustForTimeDifference': True
                }
            })
            self.exchange.load_markets()  # Load markets to validate symbols
            logger.info("Exchange connection established and markets loaded")
        except Exception as e:
            logger.error(f"Exchange setup error: {e}", exc_info=True)
            raise  # Re-raise to ensure proper initialization

    def _setup_database(self):
        """Setup database connection for persistent storage"""
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

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for exchange"""
        return symbol.replace('-', '/') if '-' in symbol else symbol

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

    def get_historical_data(
        self,
        symbol: str,
        period: str = '1d',
        interval: str = '1m'
    ) -> Optional[pd.DataFrame]:
        """Fetch historical data using ccxt"""
        try:
            if not self.exchange:
                raise ValueError("Exchange not initialized")

            symbol = self._normalize_symbol(symbol)
            if symbol not in self.supported_coins:
                logger.warning(f"Unsupported symbol: {symbol}")
                return None

            cache_key = f"{symbol}_{period}_{interval}"
            cached_data = self._get_from_cache(cache_key, interval)
            if cached_data is not None:
                return cached_data

            logger.info(f"Fetching {symbol} data for period {period}")

            # Convert period and interval to ccxt format
            timeframe = interval
            since = None
            if period == '1d':
                since = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)
            elif period == '7d':
                since = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
            elif period == '30d':
                since = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)

            # Implement retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    ohlcv = self.exchange.fetch_ohlcv(
                        symbol,
                        timeframe=timeframe,
                        since=since,
                        limit=1000
                    )

                    if not ohlcv:
                        logger.warning(f"No data received for {symbol}")
                        if attempt < max_retries - 1:
                            continue
                        return None

                    df = pd.DataFrame(
                        ohlcv,
                        columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
                    )
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)

                    # Add technical indicators
                    df = self._add_technical_indicators(df)

                    # Save to cache and database
                    self._add_to_cache(cache_key, df)
                    self._save_to_database(symbol, df)

                    return df

                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Retry {attempt + 1} for {symbol}: {e}")
                        time.sleep(1)  # Wait before retry
                    else:
                        raise

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}", exc_info=True)
            return None

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators"""
        try:
            df = df.copy()

            # Basic indicators
            df['Returns'] = df['Close'].pct_change()
            df['Volatility'] = df['Returns'].rolling(window=20).std()
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']

            # Moving averages
            for period in [20, 50, 200]:
                df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
                df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()

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
            df['MACD_Hist'] = df['MACD'] - df['Signal']

            # Bollinger Bands
            df['BB_Middle'] = df['Close'].rolling(window=20).mean()
            df['BB_Upper'] = df['BB_Middle'] + 2 * df['Close'].rolling(window=20).std()
            df['BB_Lower'] = df['BB_Middle'] - 2 * df['Close'].rolling(window=20).std()

            # Clean up NaN values
            df = df.fillna(method='bfill').fillna(method='ffill').fillna(0)

            return df

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}", exc_info=True)
            return df

    def _save_to_database(self, symbol: str, df: pd.DataFrame):
        """Save market data to database for historical analysis"""
        if not self.engine:
            return

        try:
            table_name = f"market_data_{symbol.lower().replace('/', '_')}"
            df.to_sql(
                table_name,
                self.engine,
                if_exists='append',
                index=True
            )
            logger.debug(f"Saved {len(df)} rows to database for {symbol}")
        except Exception as e:
            logger.error(f"Database error for {symbol}: {e}", exc_info=True)

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price using ccxt"""
        try:
            if not self.exchange:
                raise ValueError("Exchange not initialized")

            symbol = self._normalize_symbol(symbol)
            if symbol not in self.supported_coins:
                logger.warning(f"Unsupported symbol: {symbol}")
                return None

            ticker = self.exchange.fetch_ticker(symbol)
            if ticker and ticker.get('last'):
                return float(ticker['last'])

            logger.warning(f"No price available for {symbol}")
            return None

        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}", exc_info=True)
            return None

    def get_available_coins(self) -> Dict[str, str]:
        """Return dictionary of supported cryptocurrencies"""
        return self.supported_coins.copy()

    def get_market_summary(self, symbol: str) -> Dict[str, Union[float, str]]:
        """Get comprehensive market summary"""
        try:
            symbol = self._normalize_symbol(symbol)
            df = self.get_historical_data(symbol, period='1d')
            if df is None or df.empty:
                return {}

            current_price = df['Close'].iloc[-1]
            previous_close = df['Close'].iloc[-2]
            price_change = ((current_price - previous_close) / previous_close) * 100

            return {
                'current_price': current_price,
                'price_change_24h': price_change,
                'volume_24h': df['Volume'].sum(),
                'high_24h': df['High'].max(),
                'low_24h': df['Low'].min(),
                'volatility': df['Returns'].std() * 100,
                'rsi': df['RSI'].iloc[-1],
                'macd': df['MACD'].iloc[-1],
                'trend': 'Bullish' if current_price > df['SMA_200'].iloc[-1] else 'Bearish'
            }

        except Exception as e:
            logger.error(f"Error getting market summary for {symbol}: {e}", exc_info=True)
            return {}