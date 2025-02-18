import logging
import time
import random
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError, InterfaceError
import os
from typing import Optional, Generator

logger = logging.getLogger(__name__)

Base = declarative_base()

class Database:
    def __init__(self, connection_string: str, max_retries: int = 5, initial_delay: float = 1.0):
        """
        Initialize database connection manager with enhanced retry mechanism
        """
        self.connection_string = connection_string
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.engine = None
        self.Session = None
        self.last_connection_attempt = 0
        self.connection_timeout = 30  # seconds

    def connect(self) -> bool:
        """Initialize database connection with enhanced retry mechanism"""
        retry_count = 0
        retry_delay = self.initial_delay

        while retry_count < self.max_retries:
            try:
                if self.engine and self._test_connection():
                    return True

                self.engine = create_engine(
                    self.connection_string,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                    pool_recycle=1800,
                    pool_pre_ping=True
                )

                # Test connection
                with self.engine.connect() as conn:
                    conn.execute(text('SELECT 1'))

                self.Session = sessionmaker(bind=self.engine)
                self.last_connection_attempt = time.time()

                logger.info("Database connection established successfully")
                return True

            except (OperationalError, InterfaceError) as e:
                retry_count += 1
                logger.error(f"Database connection attempt {retry_count}/{self.max_retries} failed: {str(e)}")

                if retry_count < self.max_retries:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.critical("All connection attempts failed")
                    raise SQLAlchemyError(f"Failed to establish database connection after {self.max_retries} attempts")

        return False

    def _test_connection(self) -> bool:
        """Test if current connection is valid"""
        try:
            if not self.engine:
                return False

            with self.engine.connect() as conn:
                conn.execute(text('SELECT 1')).scalar()
            return True
        except Exception as e:
            logger.warning(f"Connection test failed: {str(e)}")
            return False

    def get_session(self) -> Session:
        """Get a new database session with automatic reconnection"""
        if not self.Session:
            if not self.connect():
                raise SQLAlchemyError("Could not establish database connection for new session")

        try:
            session = self.Session()
            return session
        except Exception as e:
            logger.error(f"Failed to create new session: {str(e)}")
            raise SQLAlchemyError(f"Failed to create database session: {str(e)}")

def get_db() -> Generator[Session, None, None]:
    """Database session generator with proper error handling"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")

    db = Database(db_url)
    session = None

    try:
        session = db.get_session()
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        if session:
            session.rollback()
        raise
    finally:
        if session:
            session.close()

# Model definitions
class TradingStrategy(Base):
    __tablename__ = "trading_strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    parameters = Column(String)  # JSON string of strategy parameters
    created_at = Column(DateTime, default=datetime.utcnow)
    simulations = relationship("SimulationResult", back_populates="strategy")

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

def init_db():
    """Initialize database tables with standardized schema"""
    try:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set")

        engine = create_engine(db_url)

        # Create standardized market data table template
        with engine.begin() as conn:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS market_data_template (
                timestamp TIMESTAMP PRIMARY KEY,
                "Open" DOUBLE PRECISION,
                "High" DOUBLE PRECISION,
                "Low" DOUBLE PRECISION,
                "Close" DOUBLE PRECISION,
                "Volume" DOUBLE PRECISION,
                "Returns" DOUBLE PRECISION,
                "Volatility" DOUBLE PRECISION,
                "Volume_MA" DOUBLE PRECISION,
                "Volume_Ratio" DOUBLE PRECISION,
                "SMA_20" DOUBLE PRECISION,
                "SMA_50" DOUBLE PRECISION,
                "SMA_200" DOUBLE PRECISION,
                "EMA_20" DOUBLE PRECISION,
                "EMA_50" DOUBLE PRECISION,
                "EMA_200" DOUBLE PRECISION,
                "MACD" DOUBLE PRECISION,
                "MACD_Signal" DOUBLE PRECISION,
                "MACD_Hist" DOUBLE PRECISION,
                "RSI" DOUBLE PRECISION,
                "ATR" DOUBLE PRECISION,
                "BB_Middle" DOUBLE PRECISION,
                "BB_Upper" DOUBLE PRECISION,
                "BB_Lower" DOUBLE PRECISION,
                "BB_Width" DOUBLE PRECISION
            ) PARTITION BY RANGE (timestamp);
            """))

            # Create partitioned indexes for performance
            conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_market_data_template_timestamp 
            ON market_data_template (timestamp);

            CREATE INDEX IF NOT EXISTS idx_market_data_template_close_timestamp 
            ON market_data_template ("Close", timestamp);
            """))

        logger.info("Database tables initialized successfully")

    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise