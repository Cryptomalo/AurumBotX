import logging
import time
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.exc import SQLAlchemyError
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

    def _parse_connection_args(self, connection_string: str) -> tuple:
        """Parse connection string and extract SSL mode"""
        parsed = urlparse(connection_string)
        query = parse_qs(parsed.query)

        # Extract SSL mode if present, default to prefer
        ssl_mode = query.get('sslmode', ['prefer'])[0]

        # Remove SSL parameters from connection string
        base_url = connection_string.split('?')[0]

        connect_args = {
            'sslmode': ssl_mode,
        }

        return base_url, connect_args

    def initialize(self, connection_string: str) -> bool:
        """Initialize database connection with improved error handling"""
        try:
            # Parse connection string and get SSL configuration
            base_url, connect_args = self._parse_connection_args(connection_string)

            # Configure the engine with proper pooling settings and SSL
            self.engine = create_engine(
                base_url,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True,
                connect_args=connect_args
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
            # Test the session
            session.execute(text('SELECT 1'))
            return session
        except Exception as e:
            logger.error(f"Failed to create new session: {str(e)}")
            raise SQLAlchemyError(f"Failed to create database session: {str(e)}")

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
    """Initialize database tables"""
    try:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set")

        db_manager = DatabaseManager()
        if not db_manager.initialize(db_url):
            raise SQLAlchemyError("Failed to initialize database connection")

        Base.metadata.create_all(bind=db_manager.engine)
        logger.info("Database tables initialized successfully")

    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

# Initialize database on module import
try:
    init_db()
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")