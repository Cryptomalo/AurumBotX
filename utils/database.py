import logging
import time
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.exc import SQLAlchemyError
import os
from utils.db_maintenance import setup_maintenance
import threading

logger = logging.getLogger(__name__)

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

class Database:
    def __init__(self, connection_string, max_retries=5):
        logger.info("Initializing Database with max_retries=%d", max_retries)
        self.db_url = connection_string
        self.max_retries = max_retries
        self.engine = None
        self.Session = None
        self.maintenance = setup_maintenance(connection_string)

        # Start maintenance thread
        self.maintenance_thread = threading.Thread(
            target=self._maintenance_loop,
            daemon=True
        )
        self.maintenance_thread.start()

        if not self._connect():
            raise SQLAlchemyError("Failed to establish initial database connection")

    def _connect(self) -> bool:
        """Initialize database connection with retry mechanism and detailed logging"""
        logger.info("Attempting database connection...")
        retry_delay = 5

        if self.engine:
            logger.debug("Connection already exists, testing it...")
            try:
                with self.engine.connect() as conn:
                    conn.execute(text('SELECT 1'))
                    logger.debug("Existing connection is valid")
                    return True
            except Exception:
                logger.warning("Existing connection failed, attempting reconnection...")
                self.engine = None
                self.Session = None

        for attempt in range(self.max_retries):
            try:
                logger.info("Connection attempt %d/%d", attempt + 1, self.max_retries)
                self.engine = create_engine(
                    self.db_url,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                    pool_recycle=1800
                )

                # Test connection
                with self.engine.connect() as conn:
                    conn.execute(text('SELECT 1'))
                    logger.debug("Connection test successful")

                # Create tables if they don't exist
                Base.metadata.create_all(bind=self.engine)

                # Only create Session maker after successful connection
                self.Session = sessionmaker(bind=self.engine)
                logger.info("Database connection established successfully")
                return True

            except SQLAlchemyError as e:
                logger.error("Database connection attempt %d/%d failed: %s",
                           attempt + 1, self.max_retries, str(e))
                if attempt < self.max_retries - 1:
                    logger.info("Waiting %d seconds before next attempt...", retry_delay)
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error("All connection attempts failed")
                    raise

        logger.error("Failed to connect to database after %d attempts", self.max_retries)
        return False

    def get_session(self) -> Session:
        """Get a new database session, reconnecting if necessary"""
        logger.debug("Requesting new database session")
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

        #Base.metadata.create_all(bind=engine) #This line is already in the _connect method. Removing to avoid redundancy.
        logger.info("Database tables initialized successfully")

    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

# Improved database session generator
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