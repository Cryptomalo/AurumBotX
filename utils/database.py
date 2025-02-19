import logging
import time
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, text, Index, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool
import os
from typing import Optional, Generator, Dict, Any
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncpg
import re

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
db_logger = logging.getLogger('sqlalchemy.engine')
db_logger.setLevel(logging.WARNING)

Base = declarative_base()

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
        self.async_engine = None
        self.Session = None
        self.AsyncSession = None
        self.pool_size = 5
        self.max_overflow = 10
        self.pool_timeout = 30
        self.pool_recycle = 1800
        self.initialized = True

    def _clean_db_url(self, url: str) -> str:
        """Clean database URL by removing unsupported parameters"""
        # Remove sslmode if present
        url = re.sub(r'\?sslmode=[^&]+', '', url)
        # Remove other SSL parameters if present
        url = re.sub(r'&ssl=[^&]+', '', url)
        return url

    async def initialize_async(self, connection_string: str) -> bool:
        """Initialize async database connection"""
        try:
            logger.info("Initializing async database connection...")

            # Clean the connection string
            clean_connection_string = self._clean_db_url(connection_string)

            # Convert SQLAlchemy URL to asyncpg format
            asyncpg_url = clean_connection_string.replace('postgresql://', 'postgresql+asyncpg://')

            self.async_engine = create_async_engine(
                asyncpg_url,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_recycle=self.pool_recycle,
                pool_pre_ping=True,
                echo=False
            )

            # Test connection
            async with self.async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

            self.AsyncSession = sessionmaker(
                self.async_engine, 
                class_=AsyncSession,
                expire_on_commit=False
            )

            logger.info("Async database connection established successfully")
            return True

        except Exception as e:
            logger.error(f"Async database initialization error: {str(e)}")
            self.async_engine = None
            self.AsyncSession = None
            raise

    def initialize(self, connection_string: str) -> bool:
        """Initialize synchronous database connection"""
        try:
            logger.info("Initializing synchronous database connection...")

            clean_connection_string = self._clean_db_url(connection_string)

            self.engine = create_engine(
                clean_connection_string,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_recycle=self.pool_recycle,
                pool_pre_ping=True,
                echo=False
            )

            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            self.Session = sessionmaker(bind=self.engine)
            logger.info("Synchronous database connection established successfully")
            return True

        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            self.engine = None
            self.Session = None
            raise

async def get_async_db() -> AsyncSession:
    """Async database session generator with improved error handling"""
    db_manager = DatabaseManager()
    db_url = os.getenv('DATABASE_URL')

    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")

    if not await db_manager.initialize_async(db_url):
        raise SQLAlchemyError("Could not establish async database connection")

    async with db_manager.AsyncSession() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Async session error: {str(e)}")
            raise
        finally:
            await session.close()

def get_db() -> Generator[Session, None, None]:
    """Synchronous database session generator with improved error handling"""
    db_manager = DatabaseManager()
    db_url = os.getenv('DATABASE_URL')

    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")

    if not db_manager.initialize(db_url):
        raise SQLAlchemyError("Could not establish database connection")

    session = db_manager.Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Session error: {str(e)}")
        raise
    finally:
        session.close()

class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("trading_strategies.id"))
    symbol = Column(String, index=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    initial_balance = Column(Float)
    final_balance = Column(Float)
    total_trades = Column(Integer)
    win_rate = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    strategy = relationship("TradingStrategy", back_populates="simulations")

class TradingStrategy(Base):
    __tablename__ = "trading_strategies"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    description = Column(String(1024))
    parameters = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'))
    is_public = Column(Boolean, default=False)
    performance_metrics = Column(JSON)

    __table_args__ = (
        Index('idx_trading_strategies_user', 'user_id'),
        Index('idx_strategies_recent', 'created_at', 'id'),
        Index('idx_strategies_perf_v2', 'created_at', 'id', 'name', 'description'),
        Index('idx_public_strategies', 'is_public', 'created_at', 'name', 'description',
              postgresql_where=text('is_public = true')),
    )

async def init_db():
    """Initialize database tables with proper error handling"""
    try:
        logger.info("Starting database initialization...")
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set")

        db_manager = DatabaseManager()
        if not await db_manager.initialize_async(db_url):
            raise SQLAlchemyError("Failed to initialize database")

        async with db_manager.async_engine.begin() as conn:
            logger.info("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database tables created successfully")
        return True

    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise

# Initialize database
try:
    import asyncio
    asyncio.run(init_db())
    logger.info("Database system initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database system: {e}")