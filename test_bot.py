import logging
import asyncio
from datetime import datetime
import os
import signal
import sys
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from utils.database import Base, init_db

# Setup logging
log_filename = f'test_bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ])
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Test database connectivity"""
    try:
        logger.info("Testing database connection...")
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL not set")
            return False

        if 'sslmode=' in db_url:
            db_url = db_url.replace('?sslmode=require', '')

        engine = create_engine(db_url)

        # Initialize database tables
        try:
            logger.info("Initializing database tables...")
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            return False

        # Test connection with a simple query
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            logger.debug("Executing test query...")
            session.execute(text("SELECT 1"))
            session.commit()
            logger.info("Database connection test passed")
            return True
        except Exception as e:
            logger.error(f"Database query failed: {str(e)}")
            return False
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False

async def run_basic_tests():
    """Run basic functionality tests"""
    try:
        logger.info("Starting basic functionality tests...")

        # Initialize database schema
        try:
            # Initialize database tables directly instead of using init_db()
            if not await test_database_connection():
                logger.error("Database connection test failed")
                return False
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            return False

        logger.info("All basic tests completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error in basic tests: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting basic functionality tests...")
    success = asyncio.run(run_basic_tests())
    sys.exit(0 if success else 1)