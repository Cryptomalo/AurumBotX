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
    """Enhanced data loader with improved error handling and caching"""

    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 1  # seconds
    BATCH_SIZE = 500  # optimized batch size for database operations

    def __init__(self, use_live_data: bool = True, testnet: bool = True):
        self.use_live_data = use_live_data
        self.testnet = testnet
        self.retry_handler = RetryHandler()
        self.data_validator = DataValidator()
        self.client = self._setup_binance_client()
        self._cache = {}
        self._cache_duration = {
            '1M': 60,
            '5M': 300,
            '15M': 900,
            '1H': 3600,
            '4H': 14400,
            '1D': 86400
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
        # Initialize database connection here
        database_url = os.getenv('DATABASE_URL')
        if database_url:
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
            logger.info("Database connection established successfully during DataLoader init")
        else:
            logger.warning("DATABASE_URL not found, CryptoDataLoader running without persistent storage")
    
    def _setup_binance_client(self):
        """Setup client Binance con API keys"""
        try:
            # Carica API keys dalle variabili ambiente
            api_key = os.environ.get('BINANCE_API_KEY')
            secret_key = os.environ.get('BINANCE_SECRET_KEY')
            
            if api_key and secret_key:
                # Crea client Binance
                client = Client(
                    api_key=api_key,
                    api_secret=secret_key,
                    testnet=self.testnet
                )
                
                logger.info(f"✅ Client Binance inizializzato (testnet={self.testnet})")
                return client
            else:
                logger.warning("❌ API Keys non trovate - client non inizializzato")
                return None
                
        except Exception as e:
            logger.error(f"❌ Errore setup client Binance: {e}")
            return None

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

        except Exception as e:
            logger.error(f"Initialization error: {e}", exc_info=True)
            raise

    def _setup_client(self):
        """Setup Binance client with enhanced error handling"""
        try:
            # Per testnet, usa le stesse variabili d'ambiente ma con endpoint testnet
            api_key = os.getenv('BINANCE_API_KEY')
            api_secret = os.getenv('BINANCE_SECRET_KEY')

            if not api_key or not api_secret:
                logger.warning("API credentials not found. Mock data will be used instead.")
                self.use_live_data = False
                return

            self.client = Client(
                api_key,
                api_secret,
                testnet=self.testnet
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
        period: str = '1D',
        interval: str = '1M',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """Get historical data with improved error handling and validation"""
        try:
            # Inizializza il client se non è ancora stato fatto
            if self.use_live_data and self.client is None:
                await self.initialize()
            
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
                            '1D': timedelta(days=1),
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
            for col_name, new_name in numeric_columns.items():
                df[new_name] = pd.to_numeric(df[col_name])

            # Set timestamp as index
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            return df[list(numeric_columns.values())]

        except Exception as e:
            logger.error(f"Error processing klines data: {e}")
            return pd.DataFrame()

    def _get_mock_data(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        """Generate mock data for testing"""
        logger.info(f"Generating mock data for {symbol}")
        dates = pd.date_range(start="2023-01-01", periods=100)
        data = {
            'Open': [100 + i for i in range(100)],
            'High': [105 + i for i in range(100)],
            'Low': [95 + i for i in range(100)],
            'Close': [100 + i for i in range(100)],
            'Volume': [1000 + i * 10 for i in range(100)]
        }
        df = pd.DataFrame(data, index=dates)
        return df

    def _add_to_cache(self, key: str, data: pd.DataFrame):
        """Add data to cache with timestamp"""
        self._cache[key] = {
            'data': data,
            'timestamp': time.time()
        }

    def _get_from_cache(self, key: str, interval: str) -> Optional[pd.DataFrame]:
        """Get data from cache if not expired"""
        if key in self._cache:
            cache_entry = self._cache[key]
            if time.time() - cache_entry['timestamp'] < self._cache_duration.get(interval, 60):
                return cache_entry['data']
        return None

    async def _save_to_database(self, symbol: str, df: pd.DataFrame):
        """Save data to database asynchronously"""
        if not self.async_session:
            return

        async with self.async_session() as session:
            try:
                for _, row in df.iterrows():
                    stmt = text("""
                        INSERT INTO historical_data (symbol, timestamp, open, high, low, close, volume)
                        VALUES (:symbol, :timestamp, :open, :high, :low, :close, :volume)
                        ON CONFLICT (symbol, timestamp) DO NOTHING;
                    """)
                    await session.execute(stmt, {
                        'symbol': symbol,
                        'timestamp': row.name,
                        'open': row['Open'],
                        'high': row['High'],
                        'low': row['Low'],
                        'close': row['Close'],
                        'volume': row['Volume']
                    })
                await session.commit()
            except SQLAlchemyError as e:
                logger.error(f"Database save error: {e}")
                await session.rollback()

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the DataFrame"""
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # Calculate RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # Add more indicators as needed
        return df











    async def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Ottiene il prezzo più recente per un simbolo con retry automatico
        
        Args:
            symbol: Simbolo della coppia (es. 'BTCUSDT')
            
        Returns:
            Prezzo corrente o None se errore
        """
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                if True:  # Force real data
                    self._setup_client()
                
                # Usa ticker price per ottenere prezzo corrente
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                price = float(ticker['price'])
                
                if price > 0:  # Validazione prezzo
                    return price
                else:
                    logger.warning(f"Prezzo invalido ricevuto per {symbol}: {price}")
                    
            except Exception as e:
                logger.warning(f"Tentativo {attempt + 1}/{max_retries} fallito per {symbol}: {str(e)}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                    logger.error(f"Errore ottenimento prezzo {symbol} dopo {max_retries} tentativi: {str(e)}")
        
        return None
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Alias per get_latest_price"""
        return await self.get_latest_price(symbol)
    def aggregate_3m_to_6m(self, df_3m: pd.DataFrame) -> pd.DataFrame:
        """
        Aggrega dati 3m in 6m
        
        Args:
            df_3m: DataFrame con dati 3 minuti
            
        Returns:
            DataFrame con dati 6 minuti
        """
        try:
            if df_3m.empty:
                return df_3m
            
            # Raggruppa ogni 2 candele 3m per fare 6m
            df_6m = df_3m.groupby(df_3m.index // 2).agg({
                'Open': 'first',
                'High': 'max', 
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            })
            
            # Ricostruisci index temporale
            df_6m.index = df_3m.index[::2]  # Ogni 2 candele
            
            return df_6m
            
        except Exception as e:
            logger.error(f"Errore aggregazione 3m->6m: {e}")
            return pd.DataFrame()

    async def get_6m_data(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """
        Ottiene dati 6 minuti tramite aggregazione da 3m
        
        Args:
            symbol: Simbolo trading (es. 'BTCUSDT')
            period: Periodo (es. '1D', '7d')
            
        Returns:
            DataFrame con dati 6 minuti
        """
        try:
            # Ottieni dati 3m (doppia quantità per aggregazione)
            period_multiplier = {'1D': '2d', '7d': '14d', '30d': '60d'}
            extended_period = period_multiplier.get(period, period)
            
            df_3m = await self.get_historical_data(symbol, extended_period, '3m')
            
            if df_3m is None or df_3m.empty:
                return None
                
            # Aggrega a 6m
            df_6m = self.aggregate_3m_to_6m(df_3m)
            
            # Taglia al periodo richiesto
            if period == '1D':
                df_6m = df_6m.tail(240)  # 24h * 10 candele/h = 240
            elif period == '7d':
                df_6m = df_6m.tail(1680)  # 7 * 240 = 1680
            elif period == '30d':
                df_6m = df_6m.tail(7200)  # 30 * 240 = 7200
                
            return df_6m
            
        except Exception as e:
            logger.error(f"Errore get_6m_data: {e}")
            return None

