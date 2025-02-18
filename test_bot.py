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
from utils.dex_trading import DexSniper
from utils.strategies.dex_sniping import DexSnipingStrategy
from utils.strategies.meme_coin_sniping import MemeCoinStrategy

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

async def test_dex_sniping():
    """Test DEX sniping functionality"""
    try:
        logger.info("Testing DEX sniping strategy...")

        # Initialize DEX sniper in testnet mode
        dex_sniper = DexSniper(testnet=True)

        # Test pair analysis
        analysis = await dex_sniper.analyze_opportunity(
            token_address="0x1234567890abcdef",
            pair_address="0xabcdef1234567890"
        )

        if not analysis:
            logger.error("DEX analysis failed")
            return False

        logger.info(f"DEX analysis successful: {analysis}")

        # Test trade execution
        trade_result = await dex_sniper.execute_trade(
            token_address="0x1234567890abcdef",
            amount=0.1,
            slippage=0.01
        )

        if not trade_result.get('success'):
            logger.error(f"Trade execution failed: {trade_result.get('error')}")
            return False

        logger.info(f"Trade execution successful: {trade_result}")
        return True

    except Exception as e:
        logger.error(f"DEX sniping test failed: {str(e)}")
        return False

async def test_meme_coin_strategy():
    """Test meme coin strategy"""
    try:
        logger.info("Testing meme coin strategy...")

        config = {
            'sentiment_threshold': 0.7,
            'min_liquidity': 5,
            'max_buy_tax': 10,
            'min_holders': 50,
            'risk_per_trade': 0.01,
            'testnet': True
        }

        strategy = MemeCoinStrategy(config)
        await strategy.initialize()

        # Test market analysis
        market_data = {
            'price': 1.0,
            'volume_24h': 100000,
            'liquidity': 50000,
            'holders': 100,
            'indicators': {
                'rsi': 55,
                'macd': 0.1
            }
        }

        sentiment_data = {
            'score': 0.8,
            'confidence': 0.75,
            'viral_coefficient': 0.9
        }

        signals = strategy.analyze_market(market_data, sentiment_data)

        if not signals:
            logger.error("Meme coin strategy analysis failed")
            return False

        logger.info(f"Meme coin strategy analysis successful: {signals}")
        return True

    except Exception as e:
        logger.error(f"Meme coin strategy test failed: {str(e)}")
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

        # Test DEX sniping functionality
        if not await test_dex_sniping():
            logger.error("DEX sniping tests failed")
            return False
        logger.info("DEX sniping tests passed")

        # Test meme coin strategy
        if not await test_meme_coin_strategy():
            logger.error("Meme coin strategy tests failed")
            return False
        logger.info("Meme coin strategy tests passed")

        logger.info("All basic tests completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error in basic tests: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting basic functionality tests...")
    success = asyncio.run(run_basic_tests())
    sys.exit(0 if success else 1)