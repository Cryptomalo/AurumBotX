import os
import time
import logging
import asyncio
from typing import Dict, Optional, List, Union, Tuple
from datetime import datetime, timedelta
import concurrent.futures

import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class DataLoadError(Exception):
    """Custom exception for data loading errors"""
    pass

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

class CryptoDataLoader:
    """Enhanced data loader with improved error handling and standardization"""

    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 1  # seconds
    BATCH_SIZE = 500

    def __init__(self, use_live_data: bool = True, testnet: bool = True):
        """Initialize the data loader with supported coins and advanced caching"""
        self.use_live_data = use_live_data
        self.testnet = testnet
        self.client = None  # Initialize client as None
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
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }

        if self.use_live_data:
            try:
                self._setup_client()
                logger.info("Live data client setup completed successfully")
            except Exception as e:
                logger.warning(f"Failed to setup live data client: {e}. Falling back to mock data.")
                self.use_live_data = False
        self._setup_database()

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

    def _setup_database(self):
        """Setup database connection with retry mechanism"""
        for attempt in range(self.RETRY_ATTEMPTS):
            try:
                database_url = os.getenv('DATABASE_URL')
                if not database_url:
                    logger.warning("DATABASE_URL not found, running without persistent storage")
                    self.engine = None
                    return

                self.engine = create_engine(database_url)

                # Test connection
                with self.engine.connect() as conn:
                    conn.execute(text('SELECT 1'))

                logger.info("Database connection established successfully")
                return

            except SQLAlchemyError as e:
                error_msg = f"Database connection error (attempt {attempt + 1}/{self.RETRY_ATTEMPTS}): {str(e)}"
                logger.error(error_msg)
                if attempt == self.RETRY_ATTEMPTS - 1:
                    raise DatabaseError(error_msg)
                time.sleep(self.RETRY_DELAY)

    def _save_to_database(self, symbol: str, df: pd.DataFrame):
        """Save market data to database with optimized batch processing"""
        if not self.engine:
            return

        try:
            # Prepare DataFrame
            df = df.copy()
            df = df.reset_index()
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['symbol'] = symbol

            # Required columns with correct order and types
            required_columns = [
                'symbol', 'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'
            ]

            # Select only required columns in correct order
            df = df[required_columns]

            # Rename columns to match database schema
            df.columns = ['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']

            # Process in optimized batches
            batch_size = self.BATCH_SIZE
            total_rows = len(df)

            for start_idx in range(0, total_rows, batch_size):
                end_idx = min(start_idx + batch_size, total_rows)
                batch_df = df.iloc[start_idx:end_idx]

                # Convert batch to records
                records = batch_df.to_dict('records')

                # Insert data with upsert using the new table
                insert_sql = """
                INSERT INTO market_data_optimized (symbol, timestamp, open, high, low, close, volume)
                VALUES (%(symbol)s, %(timestamp)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s)
                ON CONFLICT (symbol, timestamp) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume;
                """

                # Execute with retries
                for attempt in range(self.RETRY_ATTEMPTS):
                    try:
                        with self.engine.begin() as conn:
                            conn.execute(text(insert_sql), records)
                        break
                    except SQLAlchemyError as e:
                        if attempt == self.RETRY_ATTEMPTS - 1:
                            raise DatabaseError(
                                f"Failed to save batch {start_idx}-{end_idx} after "
                                f"{self.RETRY_ATTEMPTS} attempts: {str(e)}"
                            )
                        logger.warning(
                            f"Save attempt {attempt + 1}/{self.RETRY_ATTEMPTS} failed: {str(e)}"
                        )
                        time.sleep(self.RETRY_DELAY * (2 ** attempt))

                logger.info(f"Successfully saved batch {start_idx}-{end_idx} for {symbol}")

            logger.info(f"Successfully saved all {total_rows} rows for {symbol}")

        except Exception as e:
            error_msg = f"Database error for {symbol}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg)

    def _process_klines_data(self, klines: List) -> pd.DataFrame:
        """Process raw klines data into DataFrame with standardized column names and types"""
        try:
            # Create DataFrame with standard column names
            df = pd.DataFrame(
                klines,
                columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 'taker_base', 'taker_quote', 'ignore'
                ]
            )

            # Convert numeric columns and standardize column names
            numeric_columns = {
                'open': 'Open',
                'high': 'High',
                'low': 'Low', 
                'close': 'Close',
                'volume': 'Volume'
            }

            # Convert to numeric ensuring float64 type
            for old_name, new_name in numeric_columns.items():
                df[new_name] = pd.to_numeric(df[old_name], errors='coerce').astype(np.float64)

            # Drop original lowercase columns and unused columns
            columns_to_drop = [
                'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_base', 'taker_quote', 'ignore'
            ]
            df = df.drop(columns=columns_to_drop)

            # Convert timestamp to datetime and set as index
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            # Sort index to ensure chronological order
            df.sort_index(inplace=True)

            # Verify required columns exist with correct types
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns after processing: {missing_columns}")
                raise ValueError(f"Missing required columns after processing: {missing_columns}")

            # Add basic metrics before technical indicators
            df['Returns'] = df['Close'].pct_change()

            # Clean up NaN values using recommended methods
            df = df.ffill().bfill().fillna(0)

            # Ensure all numeric columns are float64
            for col in df.columns:
                if df[col].dtype != np.float64 and col != 'timestamp':
                    df[col] = df[col].astype(np.float64)

            return df

        except Exception as e:
            logger.error(f"Error processing klines data: {str(e)}", exc_info=True)
            raise DataLoadError(f"Failed to process klines data: {str(e)}")

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for exchange"""
        # Convert dashes to forward slashes for consistency
        symbol = symbol.replace('-', '/')
        # Handle both formats (BTC/USD and BTCUSDT)
        if 'USDT' in symbol:
            return symbol
        elif '/USD' in symbol:
            return symbol
        else:
            return f"{symbol}USDT"

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

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate basic technical indicators with standardized column names"""
        try:
            df = df.copy()

            # Basic metrics
            df['Returns'] = df['Close'].pct_change()
            df['Volatility'] = df['Returns'].rolling(window=20).std()
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']

            # Moving averages
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
            df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
            df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()


            # MACD
            short_ema = df['Close'].ewm(span=12, adjust=False).mean()
            long_ema = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = short_ema - long_ema
            df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

            # ATR calculation
            high_low = df['High'] - df['Low']
            high_close = (df['High'] - df['Close'].shift()).abs()
            low_close = (df['Low'] - df['Close'].shift()).abs()
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            df['ATR'] = true_range.rolling(window=14).mean()

            # Bollinger Bands
            bb_period = 20
            bb_std = 2
            df['BB_Middle'] = df['Close'].rolling(window=bb_period).mean()
            bb_std_dev = df['Close'].rolling(window=bb_period).std()
            df['BB_Upper'] = df['BB_Middle'] + (bb_std * bb_std_dev)
            df['BB_Lower'] = df['BB_Middle'] - (bb_std * bb_std_dev)
            df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']

            # RSI
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # Clean up NaN values using recommended methods
            df = df.ffill().bfill().fillna(0)

            return df

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}", exc_info=True)
            return df

    def _get_mock_data(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        """Generate mock data for testing with all required columns"""
        periods = {'1d': 1440, '7d': 10080, '30d': 43200}
        n_periods = periods.get(period, 1440)  # Default to 1 day

        timestamps = pd.date_range(
            end=datetime.now(),
            periods=n_periods,
            freq='1min'
        )

        np.random.seed(42)  # For reproducible mock data
        close_price = 100 * (1 + np.random.randn(n_periods).cumsum() * 0.02)

        # Create DataFrame with all required columns
        df = pd.DataFrame({
            'Open': close_price * (1 + np.random.randn(n_periods) * 0.001),
            'High': close_price * (1 + abs(np.random.randn(n_periods) * 0.002)),
            'Low': close_price * (1 - abs(np.random.randn(n_periods) * 0.002)),
            'Close': close_price,
            'Volume': np.random.randint(1000, 100000, n_periods)
        }, index=timestamps)

        # Clean up NaN values using recommended methods
        df = df.ffill().bfill().fillna(0)

        # Add technical indicators
        df = self._add_technical_indicators(df)

        return df

    def get_market_summary(self, symbol: str) -> Dict[str, Union[float, str]]:
        """Get comprehensive market summary with standardized column names"""
        try:
            symbol = self._normalize_symbol(symbol)
            df = self.get_historical_data(symbol, period='1d')
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
                'volatility': float(df['Returns'].std() * 100) if 'Returns' in df else 0.0,
                'rsi': float(df['RSI'].iloc[-1]) if 'RSI' in df else 0.0,
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
        interval: str = '1m'
    ) -> Optional[pd.DataFrame]:
        """Async wrapper for get_historical_data with error handling"""
        try:
            return await asyncio.to_thread(
                self.get_historical_data,
                symbol,
                period,
                interval
            )
        except Exception as e:
            error_msg = f"Error in async historical data fetch: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DataLoadError(error_msg)

    def get_historical_data(
        self,
        symbol: str,
        period: str = '1d',
        interval: str = '1m'
    ) -> Optional[pd.DataFrame]:
        """Get historical data using optimized queries"""
        try:
            symbol = self._normalize_symbol(symbol)
            if symbol not in self.supported_coins:
                logger.warning(f"Unsupported symbol: {symbol}")
                return None

            # Check cache first
            cache_key = f"{symbol}_{period}_{interval}"
            cached_data = self._get_from_cache(cache_key, interval)
            if cached_data is not None:
                return cached_data

            start_time = self._get_start_time(period)

            # Optimize query using indexes
            query = """
            SELECT timestamp, open, high, low, close, volume
            FROM market_data_optimized
            WHERE symbol = %s
            AND timestamp >= %s
            ORDER BY timestamp DESC
            """

            params = [symbol, datetime.fromtimestamp(start_time/1000) if start_time else None]

            try:
                with self.engine.begin() as conn:
                    df = pd.read_sql(query, conn, params=params, index_col='timestamp')

                if df.empty:
                    logger.warning(f"No data found for {symbol}, using mock data")
                    return self._get_mock_data(symbol, period, interval)

                df = self._add_technical_indicators(df)
                self._add_to_cache(cache_key, df)
                return df

            except SQLAlchemyError as e:
                logger.error(f"Database error for {symbol}: {str(e)}")
                return self._get_mock_data(symbol, period, interval)

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return self._get_mock_data(symbol, period, interval)

    def _cleanup_old_data(self):
        """Clean up old market data to maintain performance"""
        try:
            cleanup_sql = """
            DELETE FROM market_data_optimized 
            WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '90 days'
            AND id NOT IN (
                SELECT id FROM market_data_optimized
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '90 days'
                ORDER BY timestamp DESC
                LIMIT 1000000
            );
            """

            with self.engine.begin() as conn:
                conn.execute(text(cleanup_sql))
                logger.info("Successfully cleaned up old market data")

        except SQLAlchemyError as e:
            logger.error(f"Error cleaning up old data: {str(e)}")

    def _optimize_table_stats(self):
        """Update table statistics for query optimization"""
        try:
            analyze_sql = """
            ANALYZE market_data_optimized;
            """

            with self.engine.begin() as conn:
                conn.execute(text(analyze_sql))
                logger.info("Successfully updated table statistics")

        except SQLAlchemyError as e:
            logger.error(f"Error updating table statistics: {str(e)}")

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

            # Create tasks for each symbol
            tasks = []
            for symbol in symbols:
                tasks.append(
                    self.get_historical_data_async(
                        symbol=symbol,
                        period=period,
                        interval='1m'
                    )
                )

            # Execute all tasks concurrently
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Check results
                success_count = sum(1 for r in results if isinstance(r, pd.DataFrame))
                logger.info(f"Successfully preloaded data for {success_count}/{len(tasks)} symbols")

                return success_count >0

            return False

        except Exception as e:
            logger.error(f"Error preloading data: {e}", exc_info=True)
            return False

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price using ccxt"""
        try:
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