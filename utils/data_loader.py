import asyncio
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
    def __init__(self, use_live_data=True):
        """Initialize the data loader with supported coins and advanced caching"""
        self.supported_coins = {
            'BTC-USDT': 'Bitcoin',
            'ETH-USDT': 'Ethereum',
            'SOL-USDT': 'Solana',
            'DOGE-USDT': 'Dogecoin',
            'SHIB-USDT': 'Shiba Inu',
            'ADA-USDT': 'Cardano',
            'XRP-USDT': 'Ripple',
            'DOT-USDT': 'Polkadot',
            'MATIC-USDT': 'Polygon',
            'AVAX-USDT': 'Avalanche'
        }

        self._cache = {}
        self._cache_duration = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }

        self.use_live_data = use_live_data
        self._setup_exchange()
        self._setup_database()

        # Add real-time price tracking
        self.last_prices = {}
        self.price_updates = {}

    def _setup_exchange(self):
        """Setup ccxt exchange connection with separate instances for data and trading"""
        try:
            # Exchange for live market data
            self.market_exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',
                    'adjustForTimeDifference': True,
                    'test': False  # Use real market data
                }
            })

            # Exchange for testnet trading
            self.trading_exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',
                    'adjustForTimeDifference': True,
                    'test': True  # Keep testnet for trading
                }
            })

            logger.info("Exchange connections established: market(live) and trading(testnet)")
        except Exception as e:
            logger.error(f"Exchange setup failed: {e}")
            self.market_exchange = None
            self.trading_exchange = None

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

    async def get_historical_data(
        self,
        symbol: str,
        period: str = '1d',
        interval: str = '1m'
    ) -> Optional[pd.DataFrame]:
        """Fetch historical data with real market data support"""
        try:
            symbol = self._normalize_symbol(symbol)
            logger.info(f"Getting historical data for {symbol}")

            if not self.use_live_data or not self.market_exchange:
                return await self._get_simulated_data(symbol, period, interval)

            # Try to get from cache first
            cached_data = self._get_from_cache(f"{symbol}_{period}_{interval}")
            if cached_data is not None:
                return cached_data

            # Fetch live market data
            try:
                timeframes = {
                    '1m': '1m',
                    '5m': '5m',
                    '15m': '15m',
                    '1h': '1h',
                    '4h': '4h',
                    '1d': '1d'
                }

                ohlcv = self.market_exchange.fetch_ohlcv(
                    symbol,
                    timeframe=timeframes.get(interval, '1m'),
                    limit=500  # Adjust based on period
                )

                df = pd.DataFrame(
                    ohlcv,
                    columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
                )
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)

                # Add technical indicators
                df = await self._add_technical_indicators(df)

                # Cache the data
                self._add_to_cache(f"{symbol}_{period}_{interval}", df)

                # Save to database for historical analysis
                await self._save_to_database(symbol, df)

                return df

            except Exception as e:
                logger.error(f"Error fetching live data for {symbol}: {e}")
                logger.info("Falling back to simulated data")
                return await self._get_simulated_data(symbol, period, interval)

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return await self._get_simulated_data(symbol, period, interval)

    async def _get_simulated_data(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        """Generate simulated market data for testing"""
        periods = {'1d': 1, '7d': 7, '30d': 30}
        intervals = {'1m': 1, '5m': 5, '15m': 15, '1h': 60, '4h': 240, '1d': 1440}

        days = periods.get(period, 1)
        mins = intervals.get(interval, 1)

        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        # Generate timestamps
        timestamps = pd.date_range(start=start_time, end=end_time, freq=f'{mins}min')

        # Generate simulated prices with some randomness
        base_price = 100 if 'BTC' not in symbol else 30000
        price_data = []
        current_price = base_price

        for _ in range(len(timestamps)):
            change = np.random.normal(0, 0.001)
            current_price *= (1 + change)
            high_price = current_price * (1 + abs(np.random.normal(0, 0.0005)))
            low_price = current_price * (1 - abs(np.random.normal(0, 0.0005)))
            volume = abs(np.random.normal(1000000, 100000))
            price_data.append([
                current_price * 0.9999,  # Open
                high_price,              # High
                low_price,               # Low
                current_price,           # Close
                volume                   # Volume
            ])

        df = pd.DataFrame(
            price_data,
            index=timestamps,
            columns=['Open', 'High', 'Low', 'Close', 'Volume']
        )

        # Add technical indicators
        df = await self._add_technical_indicators(df)
        return df

    async def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
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

            # Clean up NaN values
            df = df.fillna(method='bfill').fillna(method='ffill').fillna(0)

            return df
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}", exc_info=True)
            return df

    async def _save_to_database(self, symbol: str, df: pd.DataFrame):
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
        """Get current price from live market when possible"""
        try:
            symbol = self._normalize_symbol(symbol)

            if not self.use_live_data or not self.market_exchange:
                return self._get_simulated_current_price(symbol)

            try:
                ticker = self.market_exchange.fetch_ticker(symbol)
                price = float(ticker['last'])

                # Update price tracking
                self.last_prices[symbol] = price
                self.price_updates[symbol] = datetime.now()

                return price

            except Exception as e:
                logger.error(f"Error getting live price for {symbol}: {e}")
                return self._get_simulated_current_price(symbol)

        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None

    def _get_simulated_current_price(self, symbol: str) -> Optional[float]:
        """Get current price from simulation as fallback"""
        try:
            df = self._get_simulated_data(symbol, '1d', '1m')
            return float(df['Close'].iloc[-1])
        except Exception as e:
            logger.error(f"Error getting simulated price for {symbol}: {e}")
            return None

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

    def get_available_coins(self) -> Dict[str, str]:
        """Return dictionary of supported cryptocurrencies"""
        return self.supported_coins.copy()

    async def get_market_summary(self, symbol: str) -> Dict[str, Union[float, str]]:
        """Get market summary using simulated data"""
        try:
            symbol = self._normalize_symbol(symbol)
            df = await self.get_historical_data(symbol, period='1d')
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
                'volatility': df['Close'].pct_change().std() * 100,
                'trend': 'Bullish' if price_change > 0 else 'Bearish'
            }

        except Exception as e:
            logger.error(f"Error getting market summary for {symbol}: {e}")
            return {}