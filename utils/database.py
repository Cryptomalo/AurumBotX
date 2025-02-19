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
import logging
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
        # Handle both postgresql:// and postgresql+asyncpg:// formats
        pattern = r'postgres(?:ql)?(?:\+(?:asyncpg|psycopg2))?:\/\/([^:]+):([^@]+)@([^:]+):(\d+)\/([^?]+)'
        match = re.match(pattern, url)

        if not match:
            raise ValueError(f"Invalid database URL format. Expected format: postgresql[+driver]://user:password@host:port/dbname")

        return {
            'user': match.group(1),
            'password': match.group(2),
            'host': match.group(3),
            'port': match.group(4),
            'database': match.group(5)
        }

    def _clean_db_url(self, url: str) -> str:
        """Clean database URL by removing unsupported parameters"""
        # Remove SSL parameters
        url = re.sub(r'\?.*$', '', url)
        return url

    async def initialize_async(self, connection_string: str) -> bool:
        """Initialize async database connection"""
        try:
            logger.info("Initializing async database connection...")

            # Parse the connection string
            try:
                db_params = self._parse_db_url(connection_string)
                logger.info(f"Successfully parsed database URL. Host: {db_params['host']}, Database: {db_params['database']}")
            except ValueError as e:
                logger.error(f"Failed to parse database URL: {str(e)}")
                raise

            # Create asyncpg pool
            try:
                self.pool = await asyncpg.create_pool(
                    user=db_params['user'],
                    password=db_params['password'],
                    database=db_params['database'],
                    host=db_params['host'],
                    port=db_params['port'],
                    min_size=self.pool_size,
                    max_size=self.pool_size + self.max_overflow
                )

                # Test connection
                async with self.pool.acquire() as conn:
                    await conn.execute('SELECT 1')

                logger.info("Async database connection established successfully")
                return True

            except Exception as e:
                logger.error(f"Failed to create connection pool: {str(e)}")
                raise

        except Exception as e:
            logger.error(f"Async database initialization error: {str(e)}")
            self.pool = None
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

async def get_async_db():
    """Get async database connection from pool"""
    db = DatabaseManager()
    if not db.pool:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set")
        await db.initialize_async(db_url)

    async with db.pool.acquire() as conn:
        try:
            yield conn
        except Exception as e:
            logger.error(f"Async database error: {str(e)}")
            raise

def get_db() -> Generator[Session, None, None]:
    """Get synchronous database session"""
    db = DatabaseManager()
    if not db.Session:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set")
        db.initialize(db_url)

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

# Initialize database
async def init_db():
    """Initialize database schema"""
    try:
        logger.info("Starting database initialization...")
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set")

        db = DatabaseManager()

        # Initialize async connection first
        if not await db.initialize_async(db_url):
            raise SQLAlchemyError("Failed to initialize async database connection")

        # Initialize sync connection for table creation
        if not db.initialize(db_url):
            raise SQLAlchemyError("Failed to initialize sync database connection")

        Base.metadata.create_all(db.engine)
        logger.info("Database tables created successfully")
        return True

    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
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