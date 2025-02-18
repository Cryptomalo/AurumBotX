import logging
import asyncio
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import text
from urllib.parse import urlparse, parse_qs

class DatabaseManager:
    def __init__(self, max_retries: int = 3, retry_delay: int = 5):
        self.logger = logging.getLogger(__name__)
        self.engine: Optional[AsyncEngine] = None
        self.session_maker = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.is_connected = False

    async def initialize(self, database_url: str) -> bool:
        """Initialize database connection with optimized pooling"""
        self.logger.info("Initializing database connection with connection pooling...")

        try:
            # Parse database URL and handle SSL parameters
            parsed_url = urlparse(database_url)
            query_params = parse_qs(parsed_url.query)

            # Convert to async URL and handle SSL
            base_url = database_url.split('?')[0].replace('postgresql://', 'postgresql+asyncpg://')

            # Configure SSL parameters correctly for asyncpg
            ssl_mode = None
            if 'sslmode' in query_params:
                ssl_mode = query_params['sslmode'][0]
                self.logger.debug(f"SSL mode configured: {ssl_mode}")

            # Create engine with proper configuration
            connect_args = {}
            if ssl_mode:
                connect_args['ssl'] = ssl_mode == 'require'

            self.engine = create_async_engine(
                base_url,
                echo=False,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args=connect_args
            )

            # Create session maker
            self.session_maker = async_sessionmaker(
                self.engine,
                expire_on_commit=False,
                class_=AsyncSession
            )

            # Verify connection
            if await self.verify_connection():
                self.is_connected = True
                self.logger.info("Database connection established successfully")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Database initialization error: {str(e)}")
            self.logger.debug(f"Full error details: {repr(e)}")
            return False

    async def verify_connection(self) -> bool:
        """Verify database connection with retries"""
        for attempt in range(self.max_retries):
            try:
                async with self.session_maker() as session:
                    await session.execute(text("SELECT 1"))
                    await session.commit()
                    return True

            except Exception as e:
                self.logger.warning(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    self.logger.error("All connection attempts failed")
                    return False

        return False

    async def get_session(self) -> AsyncSession:
        """Get a database session with automatic reconnection"""
        if not self.is_connected:
            await self.verify_connection()
        return self.session_maker()

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a query with retry logic"""
        for attempt in range(self.max_retries):
            try:
                async with await self.get_session() as session:
                    result = await session.execute(text(query), params or {})
                    await session.commit()
                    return result

            except Exception as e:
                self.logger.error(f"Query execution failed (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise

    async def cleanup(self):
        """Cleanup database resources"""
        if self.engine:
            await self.engine.dispose()
            self.logger.info("Database connection closed")