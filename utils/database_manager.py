import logging
import asyncio
import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from utils.models import Base, TradingData

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    async def initialize(self) -> bool:
        """Initialize database connection with retry logic"""
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                # Use environment variables for connection string
                db_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://user:pass@localhost/dbname')

                self.engine = create_async_engine(
                    db_url,
                    poolclass=AsyncAdaptedQueuePool,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                    pool_recycle=1800
                )

                self.SessionLocal = sessionmaker(
                    self.engine, class_=AsyncSession, expire_on_commit=False
                )

                # Test connection
                async with self.SessionLocal() as session:
                    await session.execute("SELECT 1")

                logger.info("Database connection established successfully")
                return True

            except Exception as e:
                retry_count += 1
                logger.error(f"Database connection attempt {retry_count} failed: {str(e)}")
                if retry_count < self.max_retries:
                    await asyncio.sleep(self.retry_delay * retry_count)
                continue

        logger.error("Failed to establish database connection after all retries")
        return False

    async def cleanup(self):
        """Cleanup database resources"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")

    def get_session(self) -> AsyncSession:
        """Get a database session"""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()

    async def execute_with_retry(self, operation, max_retries: int = 3):
        """Execute database operation with retry logic"""
        for attempt in range(max_retries):
            try:
                async with self.get_session() as session:
                    result = await operation(session)
                    await session.commit()
                    return result
            except Exception as e:
                logger.error(f"Database operation failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise

    async def save_trading_data(self, trading_data: TradingData) -> bool:
        async def _save_trading_data(session):
            session.add(trading_data)
            return True
        return await self.execute_with_retry(_save_trading_data)

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        async def _execute_query(session):
            result = await session.execute(text(query), params or {})
            return result
        return await self.execute_with_retry(_execute_query)