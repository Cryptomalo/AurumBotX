import logging
import time
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, text, Index, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool
from sqlalchemy import event
import os
from typing import Optional, Generator
from contextlib import contextmanager
import functools

logger = logging.getLogger(__name__)

# Configure logging for database operations
logging.basicConfig(level=logging.INFO)
db_logger = logging.getLogger('sqlalchemy.engine')
db_logger.setLevel(logging.WARNING)

Base = declarative_base()

def retry_on_exception(retries=3, delay=1):
    """Decorator for retrying database operations"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except SQLAlchemyError as e:
                    last_exception = e
                    if attempt < retries - 1:
                        logger.warning(f"Retry attempt {attempt + 1} after error: {str(e)}")
                        time.sleep(delay * (attempt + 1))
                    continue
            raise last_exception
        return wrapper
    return decorator

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
        self.retry_delay = 1
        self.pool_size = 5
        self.max_overflow = 10
        self.pool_timeout = 30
        self.pool_recycle = 1800
        self.initialized = True
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'failed_connections': 0,
            'slow_queries': 0,
            'query_times': []
        }

    @retry_on_exception(retries=5, delay=1)
    def initialize(self, connection_string: str) -> bool:
        """Initialize database connection with improved connection pooling and monitoring"""
        try:
            if self.engine and self.engine.connect():
                return True

            self.engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_recycle=self.pool_recycle,
                pool_pre_ping=True
            )

            # Add event listeners for connection monitoring
            @event.listens_for(self.engine, 'checkout')
            def receive_checkout(dbapi_connection, connection_record, connection_proxy):
                self.connection_stats['active_connections'] += 1

            @event.listens_for(self.engine, 'checkin')
            def receive_checkin(dbapi_connection, connection_record):
                self.connection_stats['active_connections'] -= 1

            @event.listens_for(self.engine, 'before_cursor_execute')
            def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                conn.info.setdefault('query_start_time', []).append(time.time())

            @event.listens_for(self.engine, 'after_cursor_execute')
            def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                total_time = time.time() - conn.info['query_start_time'].pop()
                self.connection_stats['query_times'].append(total_time)
                if total_time > 1.0:
                    self.connection_stats['slow_queries'] += 1
                    logger.warning(f"Slow query detected: {total_time:.2f} seconds\nQuery: {statement}")

            # Test connection with timeout
            with self.engine.connect() as conn:
                conn.execute(text('SELECT 1'))

            self.Session = sessionmaker(bind=self.engine)
            logger.info("Database connection established successfully")
            self.connection_stats['total_connections'] += 1
            return True

        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            self.connection_stats['failed_connections'] += 1
            return False

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup and monitoring"""
        if not self.Session:
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                raise ValueError("DATABASE_URL environment variable not set")

            if not self.initialize(db_url):
                raise SQLAlchemyError("Could not establish database connection")

        session = self.Session()
        start_time = time.time()
        try:
            yield session
            session.commit()
            duration = time.time() - start_time
            if duration > 1.0:
                logger.warning(f"Slow database operation detected: {duration:.2f} seconds")
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {str(e)}")
            raise
        finally:
            session.close()

    def get_connection_stats(self) -> dict:
        """Get current database connection statistics"""
        stats = {
            **self.connection_stats,
            'pool_status': {
                'size': self.pool_size,
                'overflow': self.max_overflow,
                'timeout': self.pool_timeout,
                'recycle': self.pool_recycle
            }
        }

        if self.connection_stats['query_times']:
            stats['query_performance'] = {
                'avg_time': sum(self.connection_stats['query_times']) / len(self.connection_stats['query_times']),
                'max_time': max(self.connection_stats['query_times']),
                'min_time': min(self.connection_stats['query_times']),
                'slow_queries': self.connection_stats['slow_queries']
            }

        return stats

class TradingStrategy(Base):
    __tablename__ = "trading_strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String(1024))
    parameters = Column(JSON)  # Using JSON type for better performance
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, index=True)
    is_public = Column(Boolean, default=False)
    performance_metrics = Column(JSON)  # Using JSON type for metrics

    # Optimized indexes
    __table_args__ = (
        # Composite index for efficient user-specific strategy queries
        Index('idx_user_strategies', user_id, is_public),

        # Index for chronological listing with included columns to avoid table lookups
        Index('idx_strategies_recent', created_at.desc()),

        # Composite index for user-specific strategy name uniqueness
        Index('idx_user_strategy_name', user_id, name, unique=True),

        # GIN indexes for JSON columns
        Index('idx_strategy_params', parameters, postgresql_using='gin'),
        Index('idx_strategy_metrics', performance_metrics, postgresql_using='gin'),

        # Partial index for public strategies
        Index('idx_public_strategies', is_public, postgresql_where=is_public.is_(True))
    )

def get_db() -> Generator[Session, None, None]:
    """Database session generator with improved error handling and monitoring"""
    db_manager = DatabaseManager()
    with db_manager.get_session() as session:
        yield session

@retry_on_exception(retries=3, delay=1)
def init_db():
    """Initialize database tables with improved error handling and validation"""
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

# Initialize database on module import with proper error handling
try:
    init_db()
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")