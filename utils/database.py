import logging
import time
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.exc import SQLAlchemyError
import os
from typing import Optional, Generator

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
        self.connection_timeout = 30
        self.initialized = True

    def initialize(self, connection_string: str) -> bool:
        """Initialize database connection"""
        try:
            if self.engine and self.engine.connect():
                return True

            self.engine = create_engine(
                connection_string,
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
            logger.info("Database connection established successfully")
            return True

        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            return False

    def get_session(self) -> Session:
        """Get a database session"""
        if not self.Session:
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                raise ValueError("DATABASE_URL environment variable not set")

            if not self.initialize(db_url):
                raise SQLAlchemyError("Could not establish database connection")

        return self.Session()

class TradingStrategy(Base):
    __tablename__ = "trading_strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    parameters = Column(String)  # JSON string of strategy parameters
    created_at = Column(DateTime, default=datetime.utcnow)

def get_db() -> Generator[Session, None, None]:
    """Database session generator"""
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