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
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }

        if self.use_live_data:
            self._setup_client()
        self._setup_database()

    def _setup_client(self):
        """Setup Binance client with enhanced error handling"""
        try:
            api_key = os.environ.get('BINANCE_API_KEY_TESTNET' if self.testnet else 'BINANCE_API_KEY')
            api_secret = os.environ.get('BINANCE_API_SECRET_TESTNET' if self.testnet else 'BINANCE_API_SECRET')

            if not api_key or not api_secret:
                raise ValueError("API credentials not found. Please check environment variables.")

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
            raise DataLoadError(error_msg)
        except Exception as e:
            error_msg = f"Client setup error: {str(e)}"
            logger.error(error_msg, exc_info=True)
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

    def _ensure_consistent_schema(self, table_name: str):
        """Ensure table has consistent schema with template"""
        try:
            # Get template columns
            template_cols_sql = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'market_data_template'
            ORDER BY ordinal_position;
            """

            # Get table columns
            table_cols_sql = f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position;
            """

            with self.engine.begin() as conn:
                template_cols = {row[0]: (row[1], row[2]) 
                               for row in conn.execute(text(template_cols_sql))}
                table_cols = {row[0]: (row[1], row[2]) 
                             for row in conn.execute(text(table_cols_sql))}

                # Add missing columns and fix data types
                for col, (dtype, nullable) in template_cols.items():
                    if col not in table_cols:
                        alter_sql = f"""
                        ALTER TABLE {table_name} 
                        ADD COLUMN "{col}" {dtype} {'' if nullable == 'YES' else 'NOT NULL DEFAULT 0'};
                        """
                        conn.execute(text(alter_sql))
                        logger.info(f"Added missing column {col} to {table_name}")
                    elif table_cols[col] != (dtype, nullable):
                        # Fix column type if different
                        alter_sql = f"""
                        ALTER TABLE {table_name} 
                        ALTER COLUMN "{col}" TYPE {dtype} USING "{col}"::{dtype};
                        """
                        conn.execute(text(alter_sql))
                        logger.info(f"Fixed column type for {col} in {table_name}")

            logger.info(f"Schema consistency ensured for {table_name}")

        except SQLAlchemyError as e:
            logger.error(f"Error ensuring schema consistency for {table_name}: {str(e)}")
            raise DatabaseError(f"Schema consistency error: {str(e)}")

    def _save_to_database(self, symbol: str, df: pd.DataFrame):
        """Enhanced database save with schema validation and proper conflict handling"""
        if not self.engine:
            return

        try:
            table_name = f"market_data_{symbol.lower()}"

            # Clean up old tables and ensure template exists
            self._cleanup_old_tables(symbol)
            self._ensure_template_exists()

            # Create market data table if not exists
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                LIKE market_data_template INCLUDING ALL
            );
            """

            with self.engine.begin() as conn:
                conn.execute(text(create_table_sql))

            # Ensure schema consistency
            self._ensure_consistent_schema(table_name)

            # Prepare DataFrame
            df = df.copy()
            df = df.reset_index()
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Required columns with correct order
            required_columns = [
                'Open', 'High', 'Low', 'Close', 'Volume',
                'Returns', 'Volatility', 'Volume_MA', 'Volume_Ratio',
                'SMA_20', 'SMA_50', 'SMA_200', 'EMA_20', 'EMA_50', 'EMA_200',
                'MACD', 'MACD_Signal', 'MACD_Hist', 'RSI', 'ATR',
                'BB_Middle', 'BB_Upper', 'BB_Lower', 'BB_Width'
            ]

            # Fill missing columns with NaN
            for col in required_columns:
                if col not in df.columns:
                    df[col] = np.nan

            # Select only required columns in correct order
            df = df[['timestamp'] + required_columns]

            # Process in optimized batches
            total_rows = len(df)
            batch_size = min(self.BATCH_SIZE, max(1, total_rows // 10))

            for start_idx in range(0, total_rows, batch_size):
                end_idx = min(start_idx + batch_size, total_rows)
                batch_df = df.iloc[start_idx:end_idx]

                # Prepare the data as a list of dictionaries
                records = []
                for _, row in batch_df.iterrows():
                    record = {}
                    record['timestamp'] = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                    for col in required_columns:
                        val = row[col]
                        record[col] = float(val) if pd.notna(val) else None
                    records.append(record)

                # Construct the SQL query with explicit ON CONFLICT target
                columns = ['"timestamp"'] + [f'"{col}"' for col in required_columns]
                update_cols = [f'"{col}" = EXCLUDED."{col}"' for col in required_columns]

                insert_sql = f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES ({', '.join([f':{col}' for col in ['timestamp'] + required_columns])})
                ON CONFLICT ON CONSTRAINT {table_name}_pkey 
                DO UPDATE SET {', '.join(update_cols)}
                """

                # Execute with retries
                for attempt in range(self.RETRY_ATTEMPTS):
                    try:
                        with self.engine.begin() as conn:
                            for record in records:
                                conn.execute(text(insert_sql), record)
                        break
                    except SQLAlchemyError as e:
                        if attempt == self.RETRY_ATTEMPTS - 1:
                            raise DatabaseError(
                                f"Failed to save batch {start_idx}-{end_idx} after "
                                f"{self.RETRY_ATTEMPTS} attempts: {str(e)}"
                            )
                        logger.warning(
                            f"Batch {start_idx}-{end_idx} failed (attempt {attempt + 1}/{self.RETRY_ATTEMPTS}): {str(e)}"
                        )
                        time.sleep(self.RETRY_DELAY * (2 ** attempt))

            logger.info(f"Successfully saved {total_rows} rows to {table_name}")

        except Exception as e:
            error_msg = f"Database error for {symbol}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg)

    def _cleanup_old_tables(self, symbol: str):
        """Clean up old tables for the given symbol"""
        try:
            with self.engine.begin() as conn:
                # Get list of old tables for this symbol
                query = f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'market_data_{symbol.lower()}_%';
                """
                result = conn.execute(text(query))
                old_tables = [row[0] for row in result]

                # Drop old tables
                for table in old_tables:
                    logger.info(f"Dropping old table: {table}")
                    conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
        except SQLAlchemyError as e:
            logger.error(f"Error cleaning up old tables: {str(e)}")

    def _ensure_template_exists(self):
        """Ensure template table exists with correct schema"""
        try:
            create_template_sql = """
            CREATE TABLE IF NOT EXISTS market_data_template (
                timestamp TIMESTAMP NOT NULL PRIMARY KEY,
                "Open" DOUBLE PRECISION,
                "High" DOUBLE PRECISION,
                "Low" DOUBLE PRECISION,
                "Close" DOUBLE PRECISION,
                "Volume" DOUBLE PRECISION,
                "Returns" DOUBLE PRECISION,
                "Volatility" DOUBLE PRECISION,
                "Volume_MA" DOUBLE PRECISION,
                "Volume_Ratio" DOUBLE PRECISION,
                "SMA_20" DOUBLE PRECISION,
                "SMA_50" DOUBLE PRECISION,
                "SMA_200" DOUBLE PRECISION,
                "EMA_20" DOUBLE PRECISION,
                "EMA_50" DOUBLE PRECISION,
                "EMA_200" DOUBLE PRECISION,
                "MACD" DOUBLE PRECISION,
                "MACD_Signal" DOUBLE PRECISION,
                "MACD_Hist" DOUBLE PRECISION,
                "RSI" DOUBLE PRECISION,
                "ATR" DOUBLE PRECISION,
                "BB_Middle" DOUBLE PRECISION,
                "BB_Upper" DOUBLE PRECISION,
                "BB_Lower" DOUBLE PRECISION,
                "BB_Width" DOUBLE PRECISION
            );
            """
            with self.engine.begin() as conn:
                conn.execute(text(create_template_sql))
        except SQLAlchemyError as e:
            logger.error(f"Error ensuring template exists: {str(e)}")
            raise DatabaseError(f"Failed to create template table: {str(e)}")

    def _process_klines_data(self, klines: List) -> pd.DataFrame:
        """Process raw klines data into DataFrame with standardized column names and types"""
        try:
            # Create DataFrame with standard column names
            df = pd.DataFrame(
                klines,
                columns=[
                    'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume',
                    'close_time', 'quote_volume', 'trades', 'taker_base', 'taker_quote', 'ignore'
                ]
            )

            # Convert numeric columns
            numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Convert timestamp to datetime and set as index
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            # Keep only OHLCV data
            return df[numeric_columns]

        except Exception as e:
            logger.error(f"Error processing klines data: {str(e)}", exc_info=True)
            raise DataLoadError(f"Failed to process klines data: {str(e)}")


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
        """Get comprehensive market summary with standardized column names"""
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
                'volatility': df['Returns'].std() * 100 if 'Returns' in df else 0,
                'rsi': df['RSI'].iloc[-1] if 'RSI' in df else None,
                'trend': 'Bullish' if current_price > df['SMA_20'].iloc[-1] else 'Bearish'
            }

        except Exception as e:
            logger.error(f"Error getting market summary for {symbol}: {e}", exc_info=True)
            return {}

    def get_available_coins(self) -> Dict[str, str]:
        """Return dictionary of supported cryptocurrencies"""
        return self.supported_coins.copy()

    def _backup_table_data(self, table_name: str) -> bool:
        """Create a backup of table data before schema modifications"""
        try:
            backup_table = f"{table_name}_backup_{int(time.time())}"

            backup_sql = f"""
            CREATE TABLE {backup_table} AS 
            SELECT * FROM {table_name};
            """

            with self.engine.begin() as conn:
                conn.execute(text(backup_sql))

            logger.info(f"Successfully created backup table: {backup_table}")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Failed to create backup for {table_name}: {str(e)}")
            return False

    def _backup_all_market_data(self):
        """Backup all market data tables"""
        try:
            # Get list of market data tables
            table_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'market_data_%'
            AND table_name != 'market_data_template';
            """

            with self.engine.begin() as conn:
                result = conn.execute(text(table_query))
                tables = [row[0] for row in result]

            # Create backups
            backup_results = []
            for table in tables:
                success = self._backup_table_data(table)
                backup_results.append((table, success))

            # Log results
            for table, success in backup_results:
                status = "successful" if success else "failed"
                logger.info(f"Backup for {table} was {status}")

            return all(success for _, success in backup_results)

        except SQLAlchemyError as e:
            logger.error(f"Error during backup process: {str(e)}")
            return False

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
        """Get historical data with comprehensive error handling"""
        try:
            if not self.client and self.use_live_data:
                raise ValueError("Client not initialized")

            symbol = self._normalize_symbol(symbol)
            if symbol not in self.supported_coins:
                raise ValueError(f"Unsupported symbol: {symbol}")

            # Check cache
            cache_key = f"{symbol}_{period}_{interval}"
            cached_data = self._get_from_cache(cache_key, interval)
            if cached_data is not None:
                return cached_data

            logger.info(f"Fetching {symbol} data for period {period}")

            if not self.use_live_data:
                return self._get_mock_data(symbol, period, interval)

            # Fetch data with retry
            klines = None
            for attempt in range(self.RETRY_ATTEMPTS):
                try:
                    klines = self.client.get_klines(
                        symbol=symbol,
                        interval=interval,
                        startTime=self._get_start_time(period),
                        limit=1000
                    )
                    break
                except BinanceAPIException as e:
                    if attempt == self.RETRY_ATTEMPTS - 1:
                        raise DataLoadError(f"Failed to fetch klines data: {str(e)}")
                    time.sleep(self.RETRY_DELAY)

            if not klines:
                raise DataLoadError(f"No data received for {symbol}")

            df = self._process_klines_data(klines)

            # Add technical indicators
            df = self._add_technical_indicators(df)

            # Cache and save
            self._add_to_cache(cache_key, df)
            self._save_to_database(symbol, df)

            return df

        except Exception as e:
            error_msg = f"Error fetching data for {symbol}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DataLoadError(error_msg)

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

    async def preload_data(self, symbols: List[str], period: str = '30d') -> bool:
        """
        Preload historical data for specified symbols
        Args:
            symbols: List of symbols to preload
            period: Time period to load (default: 30 days)
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Preloading data for {len(symbols)} symbols")

            # Create tasks for each symbol
            tasks = []
            for symbol in symbols:
                if symbol in self.supported_coins:
                    tasks.append(
                        self.get_historical_data_async(
                            symbol=symbol,
                            period=period,
                            interval='1m'
                        )
                    )
                else:
                    logger.warning(f"Skipping unsupported symbol: {symbol}")

            # Execute all tasks concurrently
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Check results
                success_count = sum(1 for r in results if isinstance(r, pd.DataFrame))
                logger.info(f"Successfully preloaded data for {success_count}/{len(tasks)} symbols")

                return success_count > 0

            return False

        except Exception as e:
            logger.error(f"Error preloading data: {e}", exc_info=True)
            return False