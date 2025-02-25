import os
import time
import logging
import asyncio
from typing import Dict, Optional, List, Union, Tuple, Any
from datetime import datetime, timedelta
import concurrent.futures

import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

logger = logging.getLogger(__name__)

class DataLoadError(Exception):
    """Custom exception for data loading errors"""
    pass

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

class RetryHandler:
    """Handles retries for critical operations with exponential backoff"""
    def __init__(self, max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
        self.max_retries = max_retries
        self.delay = delay
        self.backoff = backoff
        self.logger = logging.getLogger(__name__)

    async def execute(self, operation: callable, *args, **kwargs) -> Any:
        """Execute an operation with retry in case of failure"""
        last_error = None
        current_delay = self.delay

        for attempt in range(self.max_retries):
            try:
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)
                return result
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed: {str(e)}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(current_delay)
                    current_delay *= self.backoff

        self.logger.error(f"All attempts failed: {str(last_error)}")
        raise last_error

class DataValidator:
    """Validates market data with improved error checking"""

    @staticmethod
    def validate_market_data(df: pd.DataFrame) -> bool:
        """Verify DataFrame contains all required fields with correct types"""
        required_columns = {
            'Open': np.float64,
            'High': np.float64,
            'Low': np.float64,
            'Close': np.float64,
            'Volume': np.float64
        }

        # Check missing columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing columns: {missing_cols}")
            return False

        # Verify data types
        for col, dtype in required_columns.items():
            if not pd.api.types.is_numeric_dtype(df[col]):
                logger.error(f"Invalid type for {col}: {df[col].dtype} instead of {dtype}")
                return False

        # Check for null values
        null_counts = df[required_columns.keys()].isnull().sum()
        if null_counts.any():
            logger.error(f"Null values found: {null_counts[null_counts > 0]}")
            return False

        return True

class CryptoDataLoader:
    def __init__(self, testnet=True):
        self.testnet = testnet

    async def initialize(self):
        # Initialize data loader, e.g., connect to API
        pass

    async def get_historical_data(self, symbol, period):
        # Simulate fetching historical data
        dates = pd.date_range(start="2023-01-01", periods=100)
        data = {
            'Open': [100 + i for i in range(100)],
            'High': [105 + i for i in range(100)],
            'Low': [95 + i for i in range(100)],
            'Close': [100 + i for i in range(100)]
        }
        df = pd.DataFrame(data, index=dates)
        return df

    """Enhanced data loader with improved error handling and caching"""

    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 1  # seconds
    BATCH_SIZE = 500  # optimized batch size for database operations

    def __init__(self, testnet):
        pass

    async def initialize(self):
        try:
            # Setup exchange connection
            if self.use_live_data:
                try:
                    self._setup_client()
                except Exception as e:
                    logger.error(f"Error setting up client: {e}")
                    self.use_live_data = False

            # Setup database connection
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                logger.warning("DATABASE_URL not found, running without persistent storage")
                return

            # Convert URL to async format if needed
            if not database_url.startswith('postgresql+asyncpg://'):
                database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')

            self.engine = create_async_engine(
                database_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                echo=False
            )

            self.async_session = async_sessionmaker(
                self.engine,
                expire_on_commit=False,
                class_=AsyncSession
            )

            logger.info("Database connection established successfully")

        except Exception as e:
            logger.error(f"Initialization error: {e}", exc_info=True)
            raise

    async def get_historical_data(self, symbol, period):
        try:
            symbol = symbol.upper()
            if symbol not in self.supported_coins:
                logger.warning(f"Unsupported symbol: {symbol}")
                return None

            # Cache key that includes date range
            cache_key = f"{symbol}_{period}_{interval}"
            if start_date:
                cache_key += f"_from_{start_date}"
            if end_date:
                cache_key += f"_to_{end_date}"

            # Try cache first
            cached_data = self._get_from_cache(cache_key, interval)
            if cached_data is not None and self.data_validator.validate_market_data(cached_data):
                return cached_data

            if self.use_live_data and self.client:
                try:
                    # Calculate start timestamp
                    since = None
                    if start_date:
                        since = int(pd.Timestamp(start_date).timestamp() * 1000)
                    elif period:
                        period_delta = {
                            '1d': timedelta(days=1),
                            '7d': timedelta(days=7),
                            '30d': timedelta(days=30)
                        }.get(period)
                        if period_delta:
                            since = int((datetime.now() - period_delta).timestamp() * 1000)

                    # Retrieve data with retry
                    klines = await self.retry_handler.execute(
                        self.client.get_klines,
                        symbol=symbol,
                        interval=interval,
                        limit=1000,
                        startTime=since
                    )

                    if not klines:
                        logger.warning(f"No data received for {symbol}")
                        return self._get_mock_data(symbol, period, interval)

                    # Process and validate data
                    df = self._process_klines_data(klines)
                    if not self.data_validator.validate_market_data(df):
                        raise ValueError("Data validation failed")

                    # Filter by end date if specified
                    if end_date:
                        end_timestamp = pd.Timestamp(end_date)
                        df = df[df.index <= end_timestamp]

                    # Add technical indicators
                    df = self._add_technical_indicators(df)

                    # Save to cache
                    self._add_to_cache(cache_key, df)

                    # Asynchronous database save without waiting
                    asyncio.create_task(self._save_to_database(symbol, df))

                    return df

                except Exception as e:
                    logger.error(f"Error fetching live data for {symbol}: {str(e)}")
                    return self._get_mock_data(symbol, period, interval)

            return self._get_mock_data(symbol, period, interval)

        except Exception as e:
            logger.error(f"Error in get_historical_data for {symbol}: {str(e)}")
            return None

    def __init__(self, use_live_data: bool = True, testnet: bool = True):
        self.use_live_data = use_live_data
        self.testnet = testnet
        self.retry_handler = RetryHandler()
        self.data_validator = DataValidator()
        self.client = None
        self._cache = {}
        self._cache_duration = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }
        self.engine = None
        self.async_session = None
        self.logger = logger
        self.supported_coins = {
            'BTCUSDT': 'Bitcoin',
            'ETHUSDT': 'Ethereum',
            'BNBUSDT': 'Binance Coin',
            'SOLUSDT': 'Solana',
            'ADAUSDT': 'Cardano',
            'XRPUSDT': 'Ripple',
            'DOGEUSDT': 'Dogecoin',
            'DOTUSDT': 'Polkadot',
            'MATICUSDT': 'Polygon',
            'AVAXUSDT': 'Avalanche'
        }

    async def initialize(self):
        """Initialize database connection and Binance client asynchronously"""
        try:
            # Setup exchange connection
            if self.use_live_data:
                try:
                    self._setup_client()
                except Exception as e:
                    logger.error(f"Error setting up client: {e}")
                    self.use_live_data = False

            # Setup database connection
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                logger.warning("DATABASE_URL not found, running without persistent storage")
                return

            # Convert URL to async format if needed
            if not database_url.startswith('postgresql+asyncpg://'):
                database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')

            self.engine = create_async_engine(
                database_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                echo=False
            )

            self.async_session = async_sessionmaker(
                self.engine,
                expire_on_commit=False,
                class_=AsyncSession
            )

            logger.info("Database connection established successfully")

        except Exception as e:
            logger.error(f"Initialization error: {e}", exc_info=True)
            raise

    def _setup_client(self):
        """Setup Binance client with enhanced error handling"""
        try:
            api_key = os.environ.get('BINANCE_API_KEY_TESTNET' if self.testnet else 'BINANCE_API_KEY')
            api_secret = os.environ.get('BINANCE_API_SECRET_TESTNET' if self.testnet else 'BINANCE_API_SECRET')

            if not api_key or not api_secret:
                logger.warning("API credentials not found. Mock data will be used instead.")
                self.use_live_data = False
                return

            self.client = Client(
                api_key,
                api_secret,
                testnet=self.testnet,
                tld='us' if not self.testnet else None
            )

            # Test connection
            self.client.ping()
            logger.info("Binance client initialized successfully")

        except BinanceAPIException as e:
            error_msg = f"Binance API error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.use_live_data = False
            raise DataLoadError(error_msg)

        except Exception as e:
            error_msg = f"Client setup error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.use_live_data = False
            raise DataLoadError(error_msg)

    async def get_historical_data(
        self,
        symbol: str,
        period: str = '1d',
        interval: str = '1m',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """Get historical data with improved error handling and validation"""
        try:
            symbol = symbol.upper()
            if symbol not in self.supported_coins:
                logger.warning(f"Unsupported symbol: {symbol}")
                return None

            # Cache key that includes date range
            cache_key = f"{symbol}_{period}_{interval}"
            if start_date:
                cache_key += f"_from_{start_date}"
            if end_date:
                cache_key += f"_to_{end_date}"

            # Try cache first
            cached_data = self._get_from_cache(cache_key, interval)
            if cached_data is not None and self.data_validator.validate_market_data(cached_data):
                return cached_data

            if self.use_live_data and self.client:
                try:
                    # Calculate start timestamp
                    since = None
                    if start_date:
                        since = int(pd.Timestamp(start_date).timestamp() * 1000)
                    elif period:
                        period_delta = {
                            '1d': timedelta(days=1),
                            '7d': timedelta(days=7),
                            '30d': timedelta(days=30)
                        }.get(period)
                        if period_delta:
                            since = int((datetime.now() - period_delta).timestamp() * 1000)

                    # Retrieve data with retry
                    klines = await self.retry_handler.execute(
                        self.client.get_klines,
                        symbol=symbol,
                        interval=interval,
                        limit=1000,
                        startTime=since
                    )

                    if not klines:
                        logger.warning(f"No data received for {symbol}")
                        return self._get_mock_data(symbol, period, interval)

                    # Process and validate data
                    df = self._process_klines_data(klines)
                    if not self.data_validator.validate_market_data(df):
                        raise ValueError("Data validation failed")

                    # Filter by end date if specified
                    if end_date:
                        end_timestamp = pd.Timestamp(end_date)
                        df = df[df.index <= end_timestamp]

                    # Add technical indicators
                    df = self._add_technical_indicators(df)

                    # Save to cache
                    self._add_to_cache(cache_key, df)

                    # Asynchronous database save without waiting
                    asyncio.create_task(self._save_to_database(symbol, df))

                    return df

                except Exception as e:
                    logger.error(f"Error fetching live data for {symbol}: {str(e)}")
                    return self._get_mock_data(symbol, period, interval)

            return self._get_mock_data(symbol, period, interval)

        except Exception as e:
            logger.error(f"Error in get_historical_data for {symbol}: {str(e)}")
            return None

    def _process_klines_data(self, klines: List) -> pd.DataFrame:
        """Process raw klines data with improved error handling"""
        try:
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_base',
                'taker_quote', 'ignore'
            ])

            # Convert numeric columns
            numeric_columns = {
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }

            for old_name, new_name in numeric_columns.items():
                df[new_name] = pd.to_numeric(df[old_name], errors='coerce')

            # Drop original columns and unused ones
            columns_to_drop = [
                'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades',
                'taker_base', 'taker_quote', 'ignore'
            ]
            df = df.drop(columns=columns_to_drop)

            # Convert timestamp and set index
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)

            # Clean up NaN values
            df = df.ffill().bfill()

            return df

        except Exception as e:
            logger.error(f"Error processing klines data: {str(e)}", exc_info=True)
            raise DataLoadError(f"Failed to process klines data: {str(e)}")

    async def _save_to_database(self, symbol: str, df: pd.DataFrame) -> None:
        """Save market data to database with optimized batch processing"""
        if not self.engine or not self.async_session:
            logger.warning("Database engine not available")
            return

        try:
            async with self.async_session() as session:
                # Process in optimized batches
                for i in range(0, len(df), self.BATCH_SIZE):
                    batch_df = df.iloc[i:i + self.BATCH_SIZE]

                    values = [
                        {
                            'symbol': symbol,
                            'timestamp': row.name,
                            'open': float(row['Open']),
                            'high': float(row['High']),
                            'low': float(row['Low']),
                            'close': float(row['Close']),
                            'volume': float(row['Volume'])
                        }
                        for _, row in batch_df.iterrows()
                        if not any(pd.isna([
                            row['Open'], row['High'],
                            row['Low'], row['Close'],
                            row['Volume']
                        ]))
                    ]

                    if values:
                        await session.execute(
                            text("""
                            INSERT INTO market_data 
                            (symbol, timestamp, open, high, low, close, volume)
                            VALUES 
                            (:symbol, :timestamp, :open, :high, :low, :close, :volume)
                            ON CONFLICT (symbol, timestamp) 
                            DO UPDATE SET
                                open = EXCLUDED.open,
                                high = EXCLUDED.high,
                                low = EXCLUDED.low,
                                close = EXCLUDED.close,
                                volume = EXCLUDED.volume
                            """),
                            values
                        )

                await session.commit()
                logger.info(f"Successfully saved {len(df)} rows for {symbol}")

        except Exception as e:
            error_msg = f"Database error for {symbol}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg)

    def _get_mock_data(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        """Generate realistic mock data for testing"""
        periods = {'1d': 1440, '7d': 10080, '30d': 43200}
        n_periods = periods.get(period, 1440)

        np.random.seed(42)  # For reproducible mock data
        timestamps = pd.date_range(
            end=datetime.now(),
            periods=n_periods,
            freq='1min'
        )

        # Generate more realistic price movements
        price_changes = np.random.normal(0, 0.0002, n_periods)
        price_changes[0] = 0
        cum_returns = np.exp(np.cumsum(price_changes))
        base_price = 100 if 'BTC' not in symbol else 30000

        close_price = base_price * cum_returns
        volatility = np.abs(np.random.normal(0, 0.001, n_periods))

        df = pd.DataFrame({
            'Open': close_price * (1 - volatility),
            'High': close_price * (1 + volatility),
            'Low': close_price * (1 - volatility),
            'Close': close_price,
            'Volume': np.random.lognormal(10, 1, n_periods)
        }, index=timestamps)

        return self._add_technical_indicators(df)

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators with optimized calculations"""
        try:
            df = df.copy()

            # Basic metrics with vectorized operations
            df['Returns'] = df['Close'].pct_change()
            df['Volatility'] = df['Returns'].rolling(window=20).std()
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']

            # Moving averages using vectorized operations
            for period in [20, 50, 200]:
                df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
                df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()

            # MACD with vectorized calculations
            df['MACD'] = df['Close'].ewm(span=12, adjust=False).mean() - \
                        df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

            # ATR using vectorized operations
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            df['ATR'] = true_range.rolling(window=14).mean()

            # Bollinger Bands
            bb_period = 20
            df['BB_Middle'] = df['Close'].rolling(window=bb_period).mean()
            bb_std = df['Close'].rolling(window=bb_period).std()
            df['BB_Upper'] = df['BB_Middle'] + (2 * bb_std)
            df['BB_Lower'] = df['BB_Middle'] - (2 * bb_std)
            df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']

            # RSI with vectorized calculations
            delta = df['Close'].diff()
            gain = (delta.clip(lower=0)).rolling(window=14).mean()
            loss = (-delta.clip(upper=0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # Clean up NaN values using forward fill then backward fill
            df = df.ffill().bfill()

            return df

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}", exc_info=True)
            return df

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
            if len(self._cache) > 100:  # Maximum cache items
                oldest_key = min(self._cache.items(), key=lambda x: x[1][1])[0]
                del self._cache[oldest_key]
            self._cache[key] = (data.copy(), time.time())
        except Exception as e:
            logger.error(f"Cache error for {key}: {e}", exc_info=True)

    def load_market_data(self, symbol: str, period: str = '1d') -> Optional[pd.DataFrame]:
        """Load market data safely with improved error handling"""
        try:
            if not self.engine or not self.async_session:
                logger.warning("Data loader not fully initialized.  Call initialize() first.")
                return None

            # Use existing event loop if available
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Add loading message
            logger.info(f"Loading market data for {symbol}...")

            df = loop.run_until_complete(self.get_historical_data(symbol, period))

            if df is not None and len(df) > 0:
                logger.info(f"Successfully loaded {len(df)} rows of market data for {symbol}")
                return df

            logger.warning(f"No data available for {symbol}")
            return None
        except Exception as e:
            logger.error(f"Error loading market data for {symbol}: {str(e)}")
            return None

    async def get_market_summary(self, symbol: str) -> Dict[str, Union[float, str]]:
        """Get comprehensive market summary with standardized column names"""
        try:
            symbol = self._normalize_symbol(symbol)
            df = await self.get_historical_data_async(symbol, period='1d')
            if df is None or df.empty:
                return {
                    'current_price': 0.0,
                    'price_change_24h': 0.0,
                    'volume_24h': 0.0,
                    'high_24h': 0.0,
                    'low_24h': 0.0,
                    'volatility': 0.0,
                    'rsi': 0.0,
                    'trend': 'Unknown'
                }

            current_price = float(df['Close'].iloc[-1])
            previous_close = float(df['Close'].iloc[-2])
            price_change = ((current_price - previous_close) / previous_close) * 100

            return {
                'current_price': current_price,
                'price_change_24h': float(price_change),
                'volume_24h': float(df['Volume'].sum()),
                'high_24h': float(df['High'].max()),
                'low_24h': float(df['Low'].min()),
                'volatility': float(df['Returns'].std() * 100) if 'Returns' in df.columns else 0.0,
                'rsi': float(df['RSI'].iloc[-1]) if 'RSI' in df.columns else 0.0,
                'trend': 'Bullish' if current_price > df['SMA_20'].iloc[-1] else 'Bearish'
            }

        except Exception as e:
            logger.error(f"Error getting market summary for {symbol}: {e}", exc_info=True)
            return {
                'current_price': 0.0,
                'price_change_24h': 0.0,
                'volume_24h': 0.0,
                'high_24h': 0.0,
                'low_24h': 0.0,
                'volatility': 0.0,
                'rsi': 0.0,
                'trend': 'Error'
            }

    def get_available_coins(self) -> Dict[str, str]:
        """Return dictionary of supported cryptocurrencies"""
        # Convert USDT pairs to USD format for display
        display_coins = {}
        for symbol, name in self.supported_coins.items():
            display_symbol = symbol.replace('USDT', '/USD')
            display_coins[display_symbol] = name
        return display_coins

    def _validate_and_fix_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and fix DataFrame to ensure all required columns are present"""
        if df is None or df.empty:
            raise ValueError("Invalid DataFrame: None or empty")

        required_columns = [
            'Open', 'High', 'Low', 'Close', 'Volume',
            'Returns', 'Volatility', 'Volume_MA', 'Volume_Ratio',
            'SMA_20', 'SMA_50', 'SMA_200', 'EMA_20', 'EMA_50', 'EMA_200',
            'MACD', 'MACD_Signal', 'MACD_Hist', 'RSI', 'ATR',
            'BB_Middle', 'BB_Upper', 'BB_Lower', 'BB_Width'
        ]

        df = df.copy()

        # Ensure basic price columns exist
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col not in df.columns:
                raise ValueError(f"Missing critical column: {col}")

        # Add missing technical indicators
        if 'Returns' not in df.columns:
            df['Returns'] = df['Close'].pct_change()

        if 'Volatility' not in df.columns:
            df['Volatility'] = df['Returns'].rolling(window=20).std()

        # Add or recalculate other technical indicators
        df = self._add_technical_indicators(df)

        # Verify all required columns are present
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.warning(f"Adding missing columns with default values: {missing_columns}")
            for col in missing_columns:
                df[col] = 0.0

        # Clean up NaN values using the recommended approach instead of the deprecated method
        df = df.ffill().bfill().fillna(0)

        return df

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

    async def get_historical_data_async(
        self,
        symbol: str,
        period: str = '1d',
        interval: str = '1m',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """Async wrapper for get_historical_data with error handling"""
        try:
            return await self.get_historical_data(
                symbol,
                period,
                interval,
                start_date,
                end_date
            )
        except Exception as e:
            error_msg = f"Error in async historical data fetch: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DataLoadError(error_msg)

    async def preload_data(self, period: str = '30d') -> bool:
        """
        Preload historical data for all supported coins
        Args:
            period: Time period to load (default: 30 days)
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            symbols = list(self.supported_coins.keys())
            logger.info(f"Preloading data for {len(symbols)} symbols")

            success_count = 0
            for symbol in symbols:
                try:
                    data = await self.get_historical_data_async(
                        symbol=symbol,
                        period=period,
                        interval='1m'
                    )

                    if data is not None:
                        success_count += 1
                        logger.info(f"Successfully preloaded data for {symbol}")
                    else:
                        logger.warning(f"Failed to preload data for {symbol}")

                except Exception as e:
                    logger.error(f"Error preloading data for {symbol}: {str(e)}")
                    continue

            success_rate = success_count / len(symbols) if symbols else 0
            logger.info(f"Preload completed. Success rate: {success_rate:.2%}")
            return success_rate > 0.5  # Consider successful if more than 50% loaded

        except Exception as e:
            logger.error(f"Error in preload_data: {str(e)}", exc_info=True)
            return False

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price using ccxt"""
        try:
            if not self.use_live_data:
                # Return mock price for testing
                return 41000.0

            if not self.client:
                self._setup_client()
                if not self.client:
                    raise ValueError("Client not initialized")

            symbol = self._normalize_symbol(symbol)
            if symbol not in self.supported_coins:
                logger.warning(f"Unsupported symbol: {symbol}")
                return None

            # Get latest klines data
            klines = self.client.get_klines(
                symbol=symbol,
                interval='1m',
                limit=1
            )

            if not klines:
                return None

            # Return the closing price from the latest kline
            return float(klines[0][4])  # Close price is at index 4

        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}", exc_info=True)
            return None

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for exchange"""
        return symbol.upper().replace('-', '').replace('/', '')