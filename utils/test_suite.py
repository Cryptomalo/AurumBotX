import os
import logging
import sys
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to Python path if not already added
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from utils.database import DatabaseManager, get_db, get_async_db
from utils.websocket_handler import WebSocketHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('system_test.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_database():
    """Test database connectivity and operations"""
    try:
        logger.info("Test 1: Database Connection")
        db_manager = DatabaseManager()

        # Test database URL
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL not set")
            return False

        # Initialize async database
        try:
            if not await db_manager.initialize_async(db_url):
                logger.error("Async database connection failed")
                return False
            logger.info("✅ Async database connection successful")

            # Test query execution
            async with db_manager.pool.acquire() as conn:
                await conn.execute('SELECT 1')
                logger.info("✅ Database query test successful")

        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            return False

        return True

    except Exception as e:
        logger.error(f"Database test error: {str(e)}")
        return False

@pytest.mark.asyncio
async def test_websocket():
    """Test WebSocket connection and data streaming"""
    try:
        logger.info("Test 2: WebSocket Connection")
        ws_handler = WebSocketHandler()

        # Initialize WebSocket with retry
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                if await ws_handler.initialize():
                    logger.info("✅ WebSocket connection successful")
                    break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"WebSocket connection attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error("WebSocket initialization failed after all retries")
                    return False

        # Test basic functionality
        try:
            test_message = {"type": "subscribe", "symbol": "BTCUSDT"}
            if await ws_handler.send_message(test_message):
                logger.info("✅ WebSocket message sending successful")
                return True
            else:
                logger.error("Failed to send test message")
                return False
        except Exception as e:
            logger.error(f"WebSocket message test error: {str(e)}")
            return False
        finally:
            await ws_handler.cleanup()

    except Exception as e:
        logger.error(f"WebSocket test error: {str(e)}")
        return False

async def main():
    """Run all system tests"""
    try:
        logger.info("Starting system tests...")

        # Database test
        if not await test_database():
            logger.error("❌ Database tests failed")
            return
        logger.info("✅ All database tests passed")

        # WebSocket test
        if not await test_websocket():
            logger.error("❌ WebSocket tests failed")
            return
        logger.info("✅ All WebSocket tests passed")

        logger.info("✅ All system tests completed successfully")

    except Exception as e:
        logger.error(f"System test error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())