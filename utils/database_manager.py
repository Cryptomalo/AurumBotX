import logging
import asyncio
import os
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import text
from urllib.parse import urlparse, parse_qs
from utils.models import Base, TradingData

class DatabaseManager:
    def __init__(self, max_retries: int = 3, retry_delay: int = 5):
        self.logger = logging.getLogger(__name__)
        self.engine: Optional[AsyncEngine] = None
        self.session_maker = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.is_connected = False

    async def initialize(self, database_url: Optional[str] = None) -> bool:
        """Initialize database connection with optimized pooling and retry logic"""
        self.logger.info("Initializing database connection...")
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                if not database_url:
                    database_url = os.environ.get('DATABASE_URL')
                    if not database_url:
                        raise ValueError("DATABASE_URL not set")

                # Convert to async URL if needed
                if not database_url.startswith('postgresql+asyncpg://'):
                    database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')

                self.engine = create_async_engine(
                    database_url,
                    echo=False,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,
                    pool_recycle=3600
                )

                self.session_maker = async_sessionmaker(
                    self.engine,
                    expire_on_commit=False,
                    class_=AsyncSession
                )

                # Create tables if they don't exist
                async with self.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                # Verify connection
                if await self.verify_connection():
                    self.is_connected = True
                    self.logger.info("Database connection established successfully")
                    return True

                retry_count += 1
                if retry_count < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** retry_count))
                else:
                    self.logger.error("Failed to establish database connection after all retries")
                    return False

            except Exception as e:
                self.logger.error(f"Database initialization error: {str(e)}")
                retry_count += 1
                if retry_count < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** retry_count))
                else:
                    return False

        return False

    async def save_trading_data(self, trading_data: TradingData) -> bool:
        """Save trading data to database with retry logic"""
        if not self.is_connected:
            self.logger.error("Database not connected")
            return False

        for attempt in range(self.max_retries):
            try:
                async with self.session_maker() as session:
                    async with session.begin():
                        session.add(trading_data)
                    await session.commit()
                return True
            except Exception as e:
                self.logger.error(f"Error saving trading data (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                return False

    async def verify_connection(self) -> bool:
        """Verify database connection with retries"""
        if not self.session_maker:
            return False

        for attempt in range(self.max_retries):
            try:
                async with self.session_maker() as session:
                    await session.execute(text("SELECT 1"))
                    return True
            except Exception as e:
                self.logger.warning(f"Connection verification failed (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    return False
        return False

    async def get_session(self) -> AsyncSession:
        """Get a database session with automatic reconnection"""
        if not self.session_maker:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.session_maker()

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a query with retry logic"""
        for attempt in range(self.max_retries):
            try:
                async with await self.get_session() as session:
                    result = await session.execute(text(query), params or {})
                    await session.commit()
                    return result

            except Exception as e:
                self.logger.error(f"Query execution failed (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise

    async def cleanup(self):
        """Cleanup database resources"""
        if self.engine:
            await self.engine.dispose()
            self.logger.info("Database connection closed")