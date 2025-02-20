import logging
import os
import re
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from utils.models import Base, TradingData
import asyncpg

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
            # Handle both postgresql:// and postgres:// formats
            if not url.startswith(('postgresql://', 'postgres://')):
                raise ValueError("URL must start with postgresql:// or postgres://")

            # Remove SSL mode if present
            url = re.sub(r'\?.*$', '', url)

            # Support various URL formats
            patterns = [
                # Standard format: postgresql://user:pass@host:port/dbname
                r'(?:postgresql|postgres):\/\/([^:]+):([^@]+)@([^:]+):(\d+)\/(.+)',
                # Format without port: postgresql://user:pass@host/dbname
                r'(?:postgresql|postgres):\/\/([^:]+):([^@]+)@([^\/]+)\/(.+)',
                # Format with parameters: postgresql://user:pass@host:port/dbname?param=value
                r'(?:postgresql|postgres):\/\/([^:]+):([^@]+)@([^:]+):(\d+)\/([^?]+)'
            ]

            for pattern in patterns:
                match = re.match(pattern, url)
                if match:
                    groups = match.groups()
                    if len(groups) == 4:  # Format without port
                        return {
                            'user': groups[0],
                            'password': groups[1],
                            'host': groups[2],
                            'port': '5432',  # Default PostgreSQL port
                            'database': groups[3]
                        }
                    return {
                        'user': groups[0],
                        'password': groups[1],
                        'host': groups[2],
                        'port': groups[3],
                        'database': groups[4]
                    }

            raise ValueError("Could not parse database URL")

        except Exception as e:
            logger.error(f"Error parsing database URL: {str(e)}")
            raise ValueError(f"Invalid database URL format: {str(e)}")

    async def initialize(self) -> bool:
        """Initialize database connection asynchronously"""
        try:
            logger.info("Initializing database connection...")
            db_url = os.getenv('DATABASE_URL')

            if not db_url:
                raise ValueError("DATABASE_URL environment variable not set")

            # Parse connection parameters
            try:
                db_params = self._parse_db_url(db_url)
                logger.info(f"Successfully parsed database URL for database: {db_params['database']}")
            except ValueError as e:
                logger.error(f"Database URL parsing failed: {str(e)}")
                return False

            # Create connection pool
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

    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            if not self.pool:
                return await self.initialize()

            async with self.pool.acquire() as conn:
                await conn.execute('SELECT 1')
                logger.info("Database connection test successful")
                return True

        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
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