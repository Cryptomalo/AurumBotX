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

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
db_logger = logging.getLogger("sqlalchemy.engine")
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
        self.Session = None
        self.initialized = False # Set to False initially

    def initialize(self, connection_string: Optional[str] = None) -> bool:
        """Initialize synchronous database connection"""
        try:
            logger.info("Initializing synchronous database connection...")

            db_url = connection_string or os.getenv("DATABASE_URL")
            if not db_url:
                # Default to SQLite if DATABASE_URL is not set
                db_url = "sqlite:///aurumbotx_trading.db"
                logger.info(f"DATABASE_URL not set, defaulting to {db_url}")

            if db_url.startswith("sqlite:///"):
                # Ensure the directory for the SQLite database exists
                db_path = db_url.replace("sqlite:///", "")
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                self.engine = create_engine(db_url, echo=False)
            elif db_url.startswith("postgresql://") or db_url.startswith("postgres://"):
                self.engine = create_engine(
                    db_url,
                    poolclass=QueuePool,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                    pool_recycle=1800,
                    echo=False
                )
            else:
                raise ValueError(f"Unsupported database type for URL: {db_url}")

            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database connection test successful")

            self.Session = sessionmaker(bind=self.engine)
            Base.metadata.create_all(self.engine) # Create tables if they don't exist
            self.initialized = True
            return True

        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            self.engine = None
            self.Session = None
            self.initialized = False
            return False

# Initialize database
def init_db():
    """Initialize database schema"""
    try:
        logger.info("Starting database initialization...")
        db = DatabaseManager()
        if not db.initialized:
            if not db.initialize():
                raise SQLAlchemyError("Failed to initialize sync database connection")
        logger.info("Database tables created successfully")
        return True

    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise

def get_db() -> Generator[Session, None, None]:
    """Get synchronous database session"""
    db = DatabaseManager()
    if not db.initialized:
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
    user_id = Column(Integer, ForeignKey("users.id"))
    is_public = Column(Boolean, default=False)
    performance_metrics = Column(JSON)

    __table_args__ = (
        Index("idx_trading_strategies_user", "user_id"),
        Index("idx_strategies_recent", "created_at", "id"),
        Index("idx_strategies_perf_v2", "created_at", "id", "name", "description"),
    )

# Initialize database
try:
    init_db()
    logger.info("Database system initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database system: {e}")


