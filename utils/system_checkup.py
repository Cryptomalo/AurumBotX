import logging
import asyncio
import psutil
import os
from datetime import datetime
from utils.database_manager import DatabaseManager
from utils.websocket_handler import WebSocketHandler
from utils.data_loader import CryptoDataLoader
from utils.sentiment_analyzer import SentimentAnalyzer
from utils.prediction_model import PredictionModel
from utils.ai_trading import AITrading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=f'system_checkup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)
logger = logging.getLogger(__name__)

async def check_memory_usage() -> bool:
    """Monitor memory usage of the application"""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / 1024 / 1024
        logger.info(f"Memory usage: {memory_usage_mb:.2f} MB")
        return memory_usage_mb < 1000  # Warning if over 1GB
    except Exception as e:
        logger.error(f"Memory check failed: {str(e)}")
        return False

async def check_database_connection() -> bool:
    """Verify database connection"""
    try:
        db = DatabaseManager()
        connected = await db.initialize()
        if connected:
            logger.info("Database connection test successful")
            await db.cleanup()
            return True
        logger.error("Database connection test failed")
        return False
    except Exception as e:
        logger.error(f"Database check failed: {str(e)}")
        return False

async def check_websocket_connection() -> bool:
    """Verify WebSocket connection"""
    try:
        handler = WebSocketHandler()
        connected = await handler.connect_websocket()
        if connected:
            logger.info("WebSocket connection test successful")
            await handler.cleanup()
            return True
        logger.error("WebSocket connection test failed")
        return False
    except Exception as e:
        logger.error(f"WebSocket check failed: {str(e)}")
        return False

async def run_system_checkup() -> bool:
    """Run comprehensive system checkup"""
    logger.info("Starting system checkup...")

    checks = {
        "Memory Usage": await check_memory_usage(),
        "Database Connection": await check_database_connection(),
        "WebSocket Connection": await check_websocket_connection()
    }

    # Test 1: Data Loading
    logger.info("Test 1: Data Loading")
    data_loader = CryptoDataLoader()
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

    for symbol in symbols:
        try:
            data = await data_loader.get_historical_data(symbol, period='1d')
            if data is not None and not data.empty:
                logger.info(f"✓ Data loading successful for {symbol}: {len(data)} rows")
                logger.info(f"Latest price: {data['Close'].iloc[-1]:.2f}")
                checks[f"Data Loading {symbol}"] = True
            else:
                logger.error(f"✗ Data loading failed for {symbol}")
                checks[f"Data Loading {symbol}"] = False
        except Exception as e:
            logger.error(f"Error loading data for {symbol}: {str(e)}")
            checks[f"Data Loading {symbol}"] = False

    # Test 3: Sentiment Analysis
    logger.info("\nTest 3: Sentiment Analysis")
    sentiment_analyzer = SentimentAnalyzer()
    for symbol in symbols:
        try:
            sentiment = await sentiment_analyzer.analyze_sentiment(symbol)
            logger.info(f"Sentiment for {symbol}: {sentiment}")
            checks[f"Sentiment Analysis {symbol}"] = True
        except Exception as e:
            logger.error(f"Sentiment analysis failed for {symbol}: {str(e)}")
            checks[f"Sentiment Analysis {symbol}"] = False

    # Test 4: Prediction Model
    logger.info("\nTest 4: Prediction Model")
    prediction_model = PredictionModel()
    for symbol in symbols:
        try:
            data = await data_loader.get_historical_data(symbol, period='1d')
            if data is not None:
                prediction = await prediction_model.analyze_market_with_ai(data, {})
                logger.info(f"Prediction for {symbol}: {prediction}")
                checks[f"Prediction {symbol}"] = True
            else:
                logger.error(f"Prediction failed for {symbol}: No data available")
                checks[f"Prediction {symbol}"] = False
        except Exception as e:
            logger.error(f"Prediction failed for {symbol}: {str(e)}")
            checks[f"Prediction {symbol}"] = False

    # Test 5: Trading System
    logger.info("\nTest 5: Trading System")
    trading = AITrading()
    for symbol in symbols:
        try:
            signals = await trading.generate_trading_signals(symbol)
            logger.info(f"Generated signals for {symbol}: {signals}")
            checks[f"Trading Signals {symbol}"] = True
        except Exception as e:
            logger.error(f"Signal generation failed for {symbol}: {str(e)}")
            checks[f"Trading Signals {symbol}"] = False

    # Report results
    logger.info("\nSystem Checkup Results:")
    all_passed = all(checks.values())
    if all_passed:
        logger.info("All system checks passed successfully")
    else:
        failed_checks = [name for name, passed in checks.items() if not passed]
        logger.error(f"System checks failed: {', '.join(failed_checks)}")

    return all_passed

if __name__ == "__main__":
    asyncio.run(run_system_checkup())