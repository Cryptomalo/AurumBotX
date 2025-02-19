import os
import logging
import sys
import asyncio
from datetime import datetime, timedelta
from utils.database import DatabaseManager, get_db, get_async_db
from utils.websocket_handler import WebSocketHandler
from utils.prediction_model import PredictionModel
from utils.data_loader import CryptoDataLoader
from utils.strategies.scalping import ScalpingStrategy
import pandas as pd

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

async def test_database():
    """Test database connectivity and operations"""
    try:
        logger.info("Test 1: Database Connection")
        db_manager = DatabaseManager()

        # Test sync connection
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL not set")
            return False

        sync_result = db_manager.initialize(db_url)
        if not sync_result:
            logger.error("Sync database connection failed")
            return False
        logger.info("✅ Sync database connection successful")

        # Test async connection
        async_result = await db_manager.initialize_async(db_url)
        if not async_result:
            logger.error("Async database connection failed")
            return False
        logger.info("✅ Async database connection successful")

        return True

    except Exception as e:
        logger.error(f"Database test error: {str(e)}")
        return False

async def test_websocket():
    """Test WebSocket connection and data streaming"""
    try:
        logger.info("Test 2: WebSocket Connection")
        ws_handler = WebSocketHandler()

        # Test connection
        if not await ws_handler.initialize():
            logger.error("WebSocket initialization failed")
            return False

        # Test connection status
        if not ws_handler.is_connected():
            logger.error("WebSocket not connected")
            return False

        logger.info("✅ WebSocket connection successful")

        # Test message sending
        test_message = {"type": "subscribe", "symbol": "BTCUSDT"}
        if not await ws_handler.send_message(test_message):
            logger.error("Failed to send test message")
            return False

        logger.info("✅ WebSocket message sending successful")
        await ws_handler.cleanup()
        return True

    except Exception as e:
        logger.error(f"WebSocket test error: {str(e)}")
        return False

async def test_prediction_model():
    """Test prediction model with real market data"""
    try:
        logger.info("Test 3: Prediction Model")
        model = PredictionModel()
        data_loader = CryptoDataLoader()

        # Get real market data
        market_data = await data_loader.get_historical_data("BTCUSDT", "1h", limit=100)
        if market_data.empty:
            logger.error("Failed to load market data")
            return False

        # Test model training
        metrics = await model.train_async(market_data)
        if not metrics:
            logger.error("Model training failed")
            return False
        logger.info("✅ Model training successful")

        # Test prediction
        prediction = await model.predict_async(market_data)
        if not prediction:
            logger.error("Prediction failed")
            return False

        logger.info(f"✅ Prediction successful: {prediction}")
        return True

    except Exception as e:
        logger.error(f"Prediction model test error: {str(e)}")
        return False

async def test_trading_strategy():
    """Test trading strategy with real market data"""
    try:
        logger.info("Test 4: Trading Strategy")
        strategy = ScalpingStrategy({
            'volume_threshold': 500000,
            'min_volatility': 0.001,
            'profit_target': 0.003,
            'initial_stop_loss': 0.002,
            'trailing_stop': 0.001,
            'testnet': True
        })

        data_loader = CryptoDataLoader()

        # Get recent market data
        market_data = await data_loader.get_historical_data("BTCUSDT", "1m", limit=100)
        if market_data.empty:
            logger.error("Failed to load strategy test data")
            return False

        # Test strategy signals
        signals = await strategy.generate_signals(market_data)
        if not signals:
            logger.error("Strategy signal generation failed")
            return False

        logger.info(f"✅ Strategy signals generated successfully: {len(signals)} signals")
        return True

    except Exception as e:
        logger.error(f"Trading strategy test error: {str(e)}")
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

        # Prediction model test
        if not await test_prediction_model():
            logger.error("❌ Prediction model tests failed")
            return
        logger.info("✅ All prediction model tests passed")

        # Trading strategy test
        if not await test_trading_strategy():
            logger.error("❌ Trading strategy tests failed")
            return
        logger.info("✅ All trading strategy tests passed")

        logger.info("✅ All system tests completed successfully")

    except Exception as e:
        logger.error(f"System test error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())