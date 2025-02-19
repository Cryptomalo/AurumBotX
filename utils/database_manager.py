import logging
import os
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from utils.models import Base, TradingData

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

        self.engine = None
        self.Session = None
        self.initialized = True

    async def initialize(self) -> bool:
        """Initialize database connection asynchronously"""
        try:
            db_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://localhost/trading')

            self.engine = create_async_engine(
                db_url,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                echo=False
            )

            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            self.Session = sessionmaker(
                self.engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            logger.info("Database initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            return False

    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            if not self.engine:
                await self.initialize()

            async with self.engine.connect() as conn:
                await conn.execute("SELECT 1")
                logger.info("Database connection test successful")
                return True

        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False

    async def save_trading_data(self, data: Dict[str, Any]) -> bool:
        """Save trading data asynchronously"""
        try:
            if not self.Session:
                if not await self.initialize():
                    return False

            async with self.Session() as session:
                try:
                    trading_data = TradingData(**data)
                    session.add(trading_data)
                    await session.commit()
                    return True
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Error saving trading data: {str(e)}")
                    return False

        except Exception as e:
            logger.error(f"Database operation error: {str(e)}")
            return False

    async def cleanup(self):
        """Cleanup database resources"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database resources cleaned up")