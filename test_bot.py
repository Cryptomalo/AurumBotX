import logging
import asyncio
from datetime import datetime
import os
import signal
import sys
from typing import Optional, Dict, Any
from utils.database_manager import DatabaseManager

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

class TestBot:
    def __init__(self):
        logger.info("Initializing TestBot...")
        self.db_manager = None
        self.should_run = True
        self.setup_signal_handlers()
        logger.info("TestBot initialized successfully")

    def setup_signal_handlers(self) -> None:
        """Configure signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        logger.info("Signal handlers configured")

    def handle_shutdown(self, signum: int, frame: Any) -> None:
        """Handle graceful shutdown"""
        logger.info("Received shutdown signal...")
        self.should_run = False

    async def initialize_components(self) -> bool:
        """Initialize components with retry"""
        try:
            logger.info("Initializing components...")
            # Initialize database connection
            self.db_manager = DatabaseManager()
            if not await self.db_manager.initialize():
                logger.error("Database initialization failed")
                return False

            logger.info("All components initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error initializing components: {str(e)}")
            return False

    async def run_tests(self) -> bool:
        """Run all tests"""
        try:
            logger.info("Starting test suite...")

            # Initialize components
            if not await self.initialize_components():
                logger.error("Component initialization failed")
                return False

            # Test database queries
            try:
                test_query = "SELECT current_timestamp"
                await self.db_manager.execute_query(test_query)
                logger.info("Database query test passed")
            except Exception as e:
                logger.error(f"Database query test failed: {str(e)}")
                return False

            logger.info("All tests completed successfully")
            return True

        except Exception as e:
            logger.error(f"Test execution failed: {str(e)}")
            return False
        finally:
            if self.db_manager:
                await self.db_manager.cleanup()

async def main():
    bot = TestBot()
    success = await bot.run_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())