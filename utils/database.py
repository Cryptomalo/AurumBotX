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
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

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
        self.Session = None
        self.max_retries = 5
        self.initial_delay = 1.0
        self.last_connection_attempt = 0
        self.connection_timeout = 30
        self.initialized = True

    def _parse_db_url(self, url: str) -> dict:
        """Parse database URL and extract SSL mode"""
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)

        # Default to require SSL if not specified
        ssl_mode = query_params.get('sslmode', ['prefer'])[0]

        # Remove SSL parameters from URL as they'll be handled separately
        cleaned_url = url.split('?')[0]

        return {
            'url': cleaned_url,
            'ssl_mode': ssl_mode
        }

    def initialize(self, connection_string: str) -> bool:
        """Initialize database connection with proper SSL handling"""
        db_config = self._parse_db_url(connection_string)

        try:
            self.engine = create_engine(
                db_config['url'],
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True,
                connect_args={
                    "sslmode": db_config['ssl_mode']
                }
            )

            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text('SELECT 1'))

            self.Session = sessionmaker(bind=self.engine)
            self.last_connection_attempt = time.time()
            logger.info("Database connection established successfully")
            return True

        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            return False

    def get_session(self) -> Session:
        """Get a database session with automatic reconnection"""
        if not self.Session:
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                raise ValueError("DATABASE_URL environment variable not set")

            if not self.initialize(db_url):
                raise SQLAlchemyError("Could not establish database connection")

        try:
            session = self.Session()
            return session
        except Exception as e:
            logger.error(f"Failed to create new session: {str(e)}")
            raise SQLAlchemyError(f"Failed to create database session: {str(e)}")

# Model definitions remain unchanged
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

def get_db() -> Generator[Session, None, None]:
    """Database session generator with proper error handling"""
    db_manager = DatabaseManager()
    session = None

    try:
        session = db_manager.get_session()
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        if session:
            session.rollback()
        raise
    finally:
        if session:
            session.close()

def init_db():
    """Initialize database tables with standardized schema"""
    try:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set")

        db_manager = DatabaseManager()
        if not db_manager.initialize(db_url):
            raise SQLAlchemyError("Failed to initialize database connection")

        # Create tables using the engine from DatabaseManager
        Base.metadata.create_all(bind=db_manager.engine)

        # Create standardized market data table template
        with db_manager.engine.begin() as conn:
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