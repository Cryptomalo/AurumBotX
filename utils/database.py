import logging
import time
import random
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError, InterfaceError
import os
from utils.db_maintenance import setup_maintenance
import threading
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

def clean_database_url(url):
    """Clean database URL by removing incompatible parameters"""
    parsed = urlparse(url)
    # Extract query parameters
    params = parse_qs(parsed.query)

    # Remove problematic parameters for asyncpg
    params.pop('sslmode', None)

    # Rebuild query string
    query = '&'.join(f"{k}={''.join(v)}" for k, v in params.items())

    # Reconstruct URL
    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if query:
        clean_url = f"{clean_url}?{query}"

    return clean_url

class Database:
    def __init__(self, connection_string, max_retries=5, initial_delay=1.0):
        """
        Initialize database connection manager with enhanced retry mechanism

        Args:
            connection_string (str): Database connection URL
            max_retries (int): Maximum number of connection attempts
            initial_delay (float): Initial delay between retries in seconds
        """
        logger.info("Initializing Database with max_retries=%d", max_retries)
        self.db_url = clean_database_url(connection_string)
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.engine = None
        self.Session = None
        self.last_connection_attempt = 0
        self.connection_timeout = 30  # seconds

        # Initialize maintenance
        self.maintenance = setup_maintenance(self.db_url)

        # Start maintenance thread
        self.maintenance_thread = threading.Thread(
            target=self._maintenance_loop,
            daemon=True
        )
        self.maintenance_thread.start()

        if not self._connect():
            raise SQLAlchemyError("Failed to establish initial database connection")

    def _get_retry_delay(self, attempt):
        """Calculate retry delay with exponential backoff and jitter"""
        delay = min(self.initial_delay * (2 ** attempt), 60)  # Cap at 60 seconds
        jitter = random.uniform(0, 0.1 * delay)  # 10% jitter
        return delay + jitter

    def _test_connection(self):
        """Test if current connection is valid"""
        try:
            if not self.engine:
                return False

            # Simple query to test connection
            with self.engine.connect() as conn:
                conn.execute(text('SELECT 1')).scalar()
            return True
        except Exception as e:
            logger.warning(f"Connection test failed: {str(e)}")
            return False

    def _connect(self) -> bool:
        """Initialize database connection with enhanced retry mechanism and detailed logging"""
        logger.info("Attempting database connection...")

        # Check if we already have a valid connection
        if self._test_connection():
            logger.debug("Existing connection is valid")
            return True

        # Reset connection objects
        self.engine = None
        self.Session = None

        for attempt in range(self.max_retries):
            try:
                logger.info("Connection attempt %d/%d", attempt + 1, self.max_retries)

                # Create engine with pool settings
                self.engine = create_engine(
                    self.db_url,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                    pool_recycle=1800,
                    pool_pre_ping=True
                )

                # Test connection
                with self.engine.connect() as conn:
                    conn.execute(text('SELECT 1'))
                    logger.debug("Connection test successful")

                # Create tables if they don't exist
                Base.metadata.create_all(bind=self.engine)

                # Create session maker
                self.Session = sessionmaker(bind=self.engine)
                self.last_connection_attempt = time.time()

                logger.info("Database connection established successfully")
                return True

            except (OperationalError, InterfaceError) as e:
                retry_delay = self._get_retry_delay(attempt)
                logger.error("Database connection attempt %d/%d failed: %s. Retrying in %.2f seconds...",
                           attempt + 1, self.max_retries, str(e), retry_delay)

                if attempt < self.max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.critical("All connection attempts failed")
                    raise SQLAlchemyError(f"Failed to establish database connection after {self.max_retries} attempts: {str(e)}")

            except SQLAlchemyError as e:
                logger.critical(f"Unrecoverable database error: {str(e)}")
                raise

        return False

    def get_session(self) -> Session:
        """Get a new database session with automatic reconnection"""
        logger.debug("Requesting new database session")

        # Check connection age and reconnect if necessary
        if time.time() - self.last_connection_attempt > self.connection_timeout:
            logger.info("Connection age exceeded timeout, reconnecting...")
            self._connect()

        if not self.Session:
            logger.info("No session maker available, attempting to reconnect...")
            if not self._connect():
                raise SQLAlchemyError("Could not establish database connection for new session")

        try:
            session = self.Session()
            logger.debug("New database session created successfully")
            return session
        except Exception as e:
            logger.error("Failed to create new session: %s", str(e))
            raise SQLAlchemyError(f"Failed to create database session: {str(e)}")

    def _maintenance_loop(self):
        """Background thread for periodic maintenance"""
        while True:
            try:
                self.maintenance.perform_maintenance()
                # Sleep for 1 hour before next check
                time.sleep(3600)
            except Exception as e:
                logger.error(f"Error in maintenance loop: {e}")
                time.sleep(300)  # Wait 5 minutes on error

# Define Base first before any models
Base = declarative_base()

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

# Function to get database session - this is what most code should use
def get_db():
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