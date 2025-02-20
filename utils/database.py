import logging
import time
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, text, Index, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import os
import re
from typing import Optional, Generator, Dict, Any
import asyncpg

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
        self.pool = None
        self.pool_size = 5
        self.max_overflow = 10
        self.pool_timeout = 30
        self.pool_recycle = 1800
        self.initialized = True

    def _parse_db_url(self, url: str) -> Dict[str, str]:
        """Parse database URL into components"""
        try:
            # Remove query parameters but keep them for later
            base_url = url.split('?')[0]
            params = url.split('?')[1] if '?' in url else ''

            # Parse the base URL
            if 'postgres' not in base_url.lower():
                raise ValueError("URL must start with postgresql:// or postgres://")

            patterns = [
                r'(?:postgresql|postgres)(?:\+(?:asyncpg|psycopg2))?:\/\/([^:]+):([^@]+)@([^:]+):(\d+)\/([^?]+)',  # With port
                r'(?:postgresql|postgres)(?:\+(?:asyncpg|psycopg2))?:\/\/([^:]+):([^@]+)@([^\/]+)\/([^?]+)'  # Without port
            ]

            for pattern in patterns:
                match = re.match(pattern, base_url)
                if match:
                    groups = match.groups()
                    return {
                        'user': groups[0],
                        'password': groups[1],
                        'host': groups[2],
                        'port': groups[3] if len(groups) > 4 else '5432',
                        'database': groups[-1],
                        'params': params
                    }

            raise ValueError("Could not parse database URL")

        except Exception as e:
            logger.error(f"Error parsing database URL: {str(e)}")
            raise ValueError(f"Invalid database URL format: {str(e)}")

    def initialize(self, connection_string: Optional[str] = None) -> bool:
        """Initialize synchronous database connection"""
        try:
            logger.info("Initializing synchronous database connection...")

            # Get connection string from env if not provided
            db_url = connection_string or os.getenv('DATABASE_URL')
            if not db_url:
                raise ValueError("DATABASE_URL environment variable not set")

            try:
                db_params = self._parse_db_url(db_url)
                logger.info(f"Successfully parsed database URL for database: {db_params['database']}")
            except ValueError as e:
                logger.error(f"Database URL parsing failed: {str(e)}")
                return False

            # Reconstruct URL without query params for SQLAlchemy
            clean_url = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"

            self.engine = create_engine(
                clean_url,
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
                logger.info("Database connection test successful")

            self.Session = sessionmaker(bind=self.engine)
            return True

        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            self.engine = None
            self.Session = None
            return False

    async def initialize_async(self, connection_string: Optional[str] = None) -> bool:
        """Initialize async database connection"""
        try:
            logger.info("Initializing async database connection...")

            # Get connection string from env if not provided
            db_url = connection_string or os.getenv('DATABASE_URL')
            if not db_url:
                raise ValueError("DATABASE_URL environment variable not set")

            try:
                db_params = self._parse_db_url(db_url)
                logger.info(f"Successfully parsed database URL for async connection: {db_params['database']}")
            except ValueError as e:
                logger.error(f"Async database URL parsing failed: {str(e)}")
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
                    logger.info("Async database connection test successful")
                return True

            except Exception as e:
                logger.error(f"Failed to create async connection pool: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"Async database initialization error: {str(e)}")
            self.pool = None
            return False

# Initialize database
async def init_db():
    """Initialize database schema"""
    try:
        logger.info("Starting database initialization...")
        db = DatabaseManager()

        # Initialize async connection first
        if not await db.initialize_async():
            raise SQLAlchemyError("Failed to initialize async database connection")

        # Initialize sync connection for table creation
        if not db.initialize():
            raise SQLAlchemyError("Failed to initialize sync database connection")

        Base.metadata.create_all(db.engine)
        logger.info("Database tables created successfully")
        return True

    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise

def get_db() -> Generator[Session, None, None]:
    """Get synchronous database session"""
    db = DatabaseManager()
    if not db.Session:
        if not db.initialize():
            raise ValueError("Failed to initialize database connection")

    session = db.Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Session error: {str(e)}")
        raise
    finally:
        session.close()

async def get_async_db():
    """Get async database connection from pool"""
    db = DatabaseManager()
    if not db.pool:
        if not await db.initialize_async():
            raise ValueError("Failed to initialize async database connection")

    async with db.pool.acquire() as conn:
        try:
            yield conn
        except Exception as e:
            logger.error(f"Async database error: {str(e)}")
            raise

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

# Initialize database
try:
    import asyncio
    asyncio.run(init_db())
    logger.info("Database system initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database system: {e}")