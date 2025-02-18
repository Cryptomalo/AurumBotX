import logging
import asyncio
from datetime import datetime
import os
from utils.database import DatabaseManager
from utils.dex_trading import DexSniper

# Setup logging
log_filename = f'test_bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ])
logger = logging.getLogger(__name__)

async def test_database():
    """Test database connectivity"""
    try:
        logger.info("Testing database connection...")
        db_manager = DatabaseManager()

        # Initialize with DATABASE_URL
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL not set")
            return False

        if db_manager.initialize(db_url):
            logger.info("Database connection successful")
            return True
        else:
            logger.error("Failed to initialize database")
            return False

    except Exception as e:
        logger.error(f"Database test failed: {str(e)}")
        return False

async def test_dex_sniper():
    """Test DEX sniper functionality"""
    try:
        logger.info("Testing DEX sniper...")
        sniper = DexSniper(testnet=True)

        # Test analysis
        result = await sniper.analyze_opportunity(
            token_address="0xtest",
            pair_address="0xpair"
        )

        if result:
            logger.info("DEX sniper analysis successful")
            return True
        else:
            logger.error("DEX sniper analysis failed")
            return False

    except Exception as e:
        logger.error(f"DEX sniper test failed: {str(e)}")
        return False

async def run_tests():
    """Run all tests"""
    try:
        # Test database
        if not await test_database():
            logger.error("Database tests failed")
            return False

        # Test DEX sniper
        if not await test_dex_sniper():
            logger.error("DEX sniper tests failed")
            return False

        logger.info("All tests completed successfully")
        return True

    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    exit(0 if success else 1)