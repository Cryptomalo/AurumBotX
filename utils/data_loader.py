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
            'PEPE-USDT': 'Pepe',
            'WEN-USDT': 'Wen',
            'BONK-USDT': 'Bonk',
            'WOJAK-USDT': 'Wojak',
            'MEME-USDT': 'Memecoin',
            'DOGE-USDT': 'Dogecoin',
            'SHIB-USDT': 'Shiba Inu'
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
        self.market_exchange = None  # Default exchange (e.g., Binance)
        self.alt_exchanges = {}     # Alternative exchanges
        self._setup_exchange()
        self._setup_database()

    def _setup_exchange(self):
        """Setup ccxt exchange connection"""
        try:
            # Configurazione degli exchange alternativi
            exchange_configs = {
                'photon': {
                    'url': os.getenv('PHOTON_API_URL', 'https://api.photon.bullx.io'),
                    'api_key': os.getenv('PHOTON_API_KEY'),
                    'secret': os.getenv('PHOTON_SECRET')
                },
                'pumpfun': {
                    'url': os.getenv('PUMPFUN_API_URL', 'https://api.pump.fun'),
                    'api_key': os.getenv('PUMPFUN_API_KEY'),
                    'secret': os.getenv('PUMPFUN_SECRET')
                }
            }

            # Setup default exchange first as fallback
            api_key = os.getenv('BINANCE_API_KEY')
            api_secret = os.getenv('BINANCE_API_SECRET')

            if api_key and api_secret:
                self.market_exchange = ccxt.binance({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'future',
                        'adjustForTimeDifference': True
                    }
                })
                logger.info("Default exchange initialized successfully")

            # Try to initialize alternative exchanges
            self.alt_exchanges = {}
            for name, config in exchange_configs.items():
                if config['api_key'] and config['secret']:
                    try:
                        if name == 'photon':
                            self.alt_exchanges[name] = ccxt.bullx({
                                'apiKey': config['api_key'],
                                'secret': config['secret'],
                                'urls': {'api': config['url']},
                                'enableRateLimit': True
                            })
                        elif name == 'pumpfun':
                            self.alt_exchanges[name] = ccxt.pumpfun({
                                'apiKey': config['api_key'],
                                'secret': config['secret'],
                                'urls': {'api': config['url']},
                                'enableRateLimit': True
                            })
                        logger.info(f"Alternative exchange {name} initialized successfully")
                    except Exception as e:
                        logger.error(f"Failed to initialize {name} exchange: {e}")

        except Exception as e:
            logger.error(f"Exchange setup error: {e}")
            self.market_exchange = None
            self.alt_exchanges = {}

    async def _fetch_data_from_exchanges(self, symbol: str, timeframe: str, since: Optional[int]) -> Optional[List]:
        """Fetch data from multiple exchanges with failover"""
        ohlcv = await self._fetch_alternative_data(symbol, timeframe, since)
        if ohlcv:
            return ohlcv
        if self.market_exchange:
            try:
                logger.info(f"Attempting to fetch data from default exchange for {symbol}")
                ohlcv = await self._fetch_ohlcv_with_retry(self.market_exchange, symbol, timeframe, since)
                if ohlcv:
                    logger.info(f"Successfully fetched data from default exchange")
                    return ohlcv
            except Exception as e:
                logger.warning(f"Failed to fetch data from default exchange: {e}")

        logger.warning(f"No data available from any exchange for {symbol}")
        return None

    async def _fetch_alternative_data(self, symbol: str, timeframe: str, since: Optional[int]) -> Optional[List]:
        """Try to fetch data from alternative exchanges"""
        for name, exchange in self.alt_exchanges.items():
            try:
                logger.info(f"Attempting to fetch data from {name} for {symbol}")
                if name == 'photon':
                    data = await self._fetch_photon_data(exchange, symbol, timeframe, since)
                elif name == 'pumpfun':
                    data = await self._fetch_pumpfun_data(exchange, symbol, timeframe, since)
                else:
                    continue

                if data:
                    logger.info(f"Successfully fetched data from {name}")
                    return data
            except Exception as e:
                logger.warning(f"Failed to fetch data from {name}: {e}")
                continue
        return None

    async def _fetch_ohlcv_with_retry(self, exchange, symbol: str, timeframe: str, since: Optional[int], max_retries: int = 3) -> List:
        """Fetch OHLCV data with retry logic"""
        for attempt in range(max_retries):
            try:
                if hasattr(exchange, 'fetch_ohlcv'):
                    return exchange.fetch_ohlcv(
                        symbol,
                        timeframe=timeframe,
                        since=since,
                        limit=1000
                    )
                else:
                    # Implementa logica custom per exchange che non supportano fetch_ohlcv
                    return await self._custom_fetch_ohlcv(exchange, symbol, timeframe, since)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Retry {attempt + 1}/{max_retries} for {symbol}: {e}")
                await asyncio.sleep(1)

    async def _custom_fetch_ohlcv(self, exchange, symbol: str, timeframe: str, since: Optional[int]) -> List:
        """Custom implementation for exchanges without standard OHLCV endpoint"""
        # Implementa la logica specifica per ogni exchange
        if exchange.id == 'photon':
            return await self._fetch_photon_data(exchange, symbol, timeframe, since)
        elif exchange.id == 'pumpfun':
            return await self._fetch_pumpfun_data(exchange, symbol, timeframe, since)
        # Aggiungi altri exchange quando necessario
        return []

    async def _fetch_photon_data(self, exchange, symbol: str, timeframe: str, since: Optional[int]) -> Optional[List]:
        """Custom implementation for Photon exchange"""
        try:
            # Use exchange specific endpoint if available
            if hasattr(exchange, 'fetch_ohlcv'):
                return await exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
            # Fallback to custom API call if needed
            endpoint = f"/v1/klines?symbol={symbol}&interval={timeframe}"
            if since:
                endpoint += f"&startTime={since}"
            response = await exchange.fetch(endpoint)
            # Transform response to OHLCV format if needed
            return response
        except Exception as e:
            logger.error(f"Error fetching Photon data: {e}")
            return None

    async def _fetch_pumpfun_data(self, exchange, symbol: str, timeframe: str, since: Optional[int]) -> Optional[List]:
        """Custom implementation for Pump.fun exchange"""
        try:
            if hasattr(exchange, 'fetch_ohlcv'):
                return await exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
            endpoint = f"/market/history/kline?symbol={symbol}&period={timeframe}"
            if since:
                endpoint += f"&since={since}"
            response = await exchange.fetch(endpoint)
            return response
        except Exception as e:
            logger.error(f"Error fetching Pump.fun data: {e}")
            return None

    async def get_historical_data(
        self,
        symbol: str,
        period: str = '1d',
        interval: str = '1m'
    ) -> Optional[pd.DataFrame]:
        """Fetch historical data using alternative exchanges first, then fallback to default"""
        try:
            symbol = self._normalize_symbol(symbol)
            if symbol not in self.supported_coins:
                logger.warning(f"Unsupported symbol: {symbol}")
                return None

            cache_key = f"{symbol}_{period}_{interval}"
            cached_data = self._get_from_cache(cache_key, interval)
            if cached_data is not None:
                return cached_data

            logger.info(f"Fetching {symbol} data for period {period}")

            # Convert period and interval to timestamps
            since = None
            if period == '1d':
                since = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)
            elif period == '7d':
                since = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
            elif period == '30d':
                since = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)

            # Try alternative exchanges first
            ohlcv = await self._fetch_alternative_data(symbol, interval, since)

            # Fallback to default exchange if no data from alternatives
            if not ohlcv and self.market_exchange:
                try:
                    logger.info("Falling back to default exchange")
                    ohlcv = await self.market_exchange.fetch_ohlcv(
                        symbol,
                        timeframe=interval,
                        since=since,
                        limit=1000
                    )
                except Exception as e:
                    logger.error(f"Default exchange error: {e}")

            # If no live data available, use simulation
            if not ohlcv:
                logger.warning(f"No live data available for {symbol}, using simulation")
                return await self._get_simulated_data(symbol, period, interval)

            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            # Add technical indicators and cache
            df = await self._add_technical_indicators(df)
            self._add_to_cache(cache_key, df)
            await self._save_to_database(symbol, df)

            return df

        except Exception as e:
            logger.error(f"Error in get_historical_data for {symbol}: {e}")
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

        return await self._add_technical_indicators(df)

    async def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators"""
        try:
            df = df.copy()

            # Basic indicators
            df['Returns'] = df['Close'].pct_change()
            df['Volatility'] = df['Returns'].rolling(window=20).std()
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']

            # Moving averages e crossovers
            for period in [9, 20, 50, 200]:
                df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
                df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()

            # MACD
            exp12 = df['Close'].ewm(span=12, adjust=False).mean()
            exp26 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp12 - exp26
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Hist'] = df['MACD'] - df['Signal']

            # RSI
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # Bollinger Bands
            df['BB_Middle'] = df['Close'].rolling(window=20).mean()
            bb_std = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + 2 * bb_std
            df['BB_Lower'] = df['BB_Middle'] - 2 * bb_std
            df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']

            # Stochastic Oscillator
            low_min = df['Low'].rolling(window=14).min()
            high_max = df['High'].rolling(window=14).max()
            df['Stoch_K'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
            df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()

            # Average True Range (ATR)
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            df['ATR'] = true_range.rolling(window=14).mean()

            # Volume Profile
            df['VP_by_Price'] = df['Volume'] * df['Close']
            df['VWAP'] = df['VP_by_Price'].cumsum() / df['Volume'].cumsum()

            # Momentum
            df['ROC'] = df['Close'].pct_change(periods=10) * 100
            df['MFI'] = (
                df['VP_by_Price'].rolling(window=14).mean() /
                df['Volume'].rolling(window=14).mean()
            )

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
            table_name = f"market_data_{symbol.lower().replace('/', '_').replace('-', '_')}"
            df.to_sql(
                table_name,
                self.engine,
                if_exists='append',
                index=True
            )
            logger.debug(f"Saved {len(df)} rows to database for {symbol}")
        except Exception as e:
            logger.error(f"Database error for {symbol}: {e}", exc_info=True)

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for exchange"""
        # Standardize separator
        normalized = symbol.replace('-', '/').replace('_', '/')

        # Handle USDT pairs consistently
        if normalized.endswith('/USDT'):
            base = normalized.split('/')[0]
            return f"{base}-USDT"  # Format expected by exchange
        elif normalized.endswith('/USD'):
            base = normalized.split('/')[0]
            return f"{base}-USD"

        return normalized

    def get_available_coins(self) -> Dict[str, str]:
        """Return dictionary of supported cryptocurrencies with both formats"""
        base_coins = self.supported_coins.copy()
        alternative_format = {}

        # Add alternative format for each symbol
        for symbol, name in base_coins.items():
            if '-' in symbol:
                alt_symbol = symbol.replace('-', '/')
            else:
                alt_symbol = symbol.replace('/', '-')
            alternative_format[alt_symbol] = name

        # Merge both formats
        base_coins.update(alternative_format)
        return base_coins

    async def get_market_summary(self, symbol: str) -> Dict[str, Union[float, str]]:
        """Get market summary using simulated or live data"""
        try:
            symbol = self._normalize_symbol(symbol)
            df = await self.get_historical_data(symbol, period='1d')

            if df is None or df.empty:
                logger.warning(f"No data available for market summary of {symbol}")
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
                'trend': 'Bullish' if price_change > 0 else 'Bearish'
            }

        except Exception as e:
            logger.error(f"Error getting market summary for {symbol}: {e}")
            return {}
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