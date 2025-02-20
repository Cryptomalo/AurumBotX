import logging
import os
import re
from typing import Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from utils.models import Base, TradingData
import asyncpg
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return

        self.pool = None
        self.pool_size = 5
        self.max_overflow = 10
        self.pool_timeout = 30
        self.pool_recycle = 1800
        self.initialized = True

    def _parse_db_url(self, url: str) -> Dict[str, str]:
        """Parse database URL into components"""
        try:
            if not url.startswith(('postgresql://', 'postgres://')):
                raise ValueError("URL must start with postgresql:// or postgres://")

            # Remove SSL mode and other parameters if present
            base_url = url.split('?')[0]

            # Standard format with port
            pattern1 = r'(?:postgresql|postgres):\/\/([^:]+):([^@]+)@([^:]+):(\d+)\/(.+)'
            # Format without port (use default 5432)
            pattern2 = r'(?:postgresql|postgres):\/\/([^:]+):([^@]+)@([^\/]+)\/(.+)'

            match = re.match(pattern1, base_url)
            if match:
                return {
                    'user': match.group(1),
                    'password': match.group(2),
                    'host': match.group(3),
                    'port': match.group(4),
                    'database': match.group(5)
                }

            match = re.match(pattern2, base_url)
            if match:
                return {
                    'user': match.group(1),
                    'password': match.group(2),
                    'host': match.group(3),
                    'port': '5432',
                    'database': match.group(4)
                }

            raise ValueError("Invalid database URL format")

        except Exception as e:
            logger.error(f"Error parsing database URL: {str(e)}")
            raise ValueError(f"Invalid database URL format: {str(e)}")

    async def save_trading_data(self, data: Union[Dict[str, Any], TradingData]) -> bool:
        """Save trading data to database"""
        try:
            if not self.pool:
                logger.error("Database connection not initialized")
                return False

            # Convert TradingData object to dictionary if necessary
            if isinstance(data, TradingData):
                data = data.to_dict()

            async with self.pool.acquire() as conn:
                # Create trading_data table if it doesn't exist
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS trading_data (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        price DECIMAL NOT NULL,
                        volume DECIMAL NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        side VARCHAR(10),
                        strategy VARCHAR(50),
                        profit_loss DECIMAL DEFAULT 0.0,
                        trade_metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Insert trading data
                await conn.execute('''
                    INSERT INTO trading_data (
                        symbol, price, volume, timestamp, side, 
                        strategy, profit_loss, trade_metadata, created_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ''', 
                data.get('symbol', 'UNKNOWN'),
                float(data.get('price', 0)),
                float(data.get('volume', 0)),
                datetime.fromtimestamp(float(data.get('timestamp', datetime.now().timestamp()))),
                data.get('side'),
                data.get('strategy'),
                float(data.get('profit_loss', 0.0)),
                json.dumps(data.get('trade_metadata', {})),
                datetime.now()
                )

                logger.info(f"Successfully saved trading data for {data.get('symbol')}")
                return True

        except Exception as e:
            logger.error(f"Error saving trading data: {str(e)}")
            return False

    async def initialize(self) -> bool:
        """Initialize database connection asynchronously"""
        try:
            logger.info("Initializing database connection...")
            db_url = os.getenv('DATABASE_URL')

            if not db_url:
                raise ValueError("DATABASE_URL environment variable not set")

            try:
                db_params = self._parse_db_url(db_url)
                logger.info(f"Successfully parsed database URL for database: {db_params['database']}")
            except ValueError as e:
                logger.error(f"Database URL parsing failed: {str(e)}")
                return False

            try:
                self.pool = await asyncpg.create_pool(
                    user=db_params['user'],
                    password=db_params['password'],
                    database=db_params['database'],
                    host=db_params['host'],
                    port=int(db_params['port']),
                    min_size=self.pool_size,
                    max_size=self.pool_size + self.max_overflow,
                    command_timeout=self.pool_timeout
                )

                # Test connection
                async with self.pool.acquire() as conn:
                    await conn.execute('SELECT 1')
                    logger.info("Database connection test successful")
                return True

            except Exception as e:
                logger.error(f"Failed to create connection pool: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            self.pool = None
            return False

    async def cleanup(self):
        """Cleanup database resources"""
        try:
            if self.pool:
                await self.pool.close()
                logger.info("Database connection pool closed")
            self.initialized = False
            logger.info("Database cleanup completed")
        except Exception as e:
            logger.error(f"Error during database cleanup: {str(e)}")