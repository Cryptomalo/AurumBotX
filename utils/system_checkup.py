import logging
import asyncio
from datetime import datetime
import psutil
import os
from utils.data_loader import CryptoDataLoader
from utils.sentiment_analyzer import SentimentAnalyzer 
from utils.prediction_model import PredictionModel
from utils.ai_trading import AITrading
from utils.database_manager import DatabaseManager
from utils.websocket_handler import WebSocketHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=f'system_checkup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)
logger = logging.getLogger(__name__)

async def check_memory_usage():
    """Monitor memory usage of the application"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    logger.info(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
    return memory_info.rss < 1024 * 1024 * 1000  # Warning if over 1GB

async def check_websocket_connections():
    """Verify WebSocket connections are properly managed"""
    handler = WebSocketHandler(logger)
    try:
        await handler.connect_websocket()
        connections = handler.get_active_connections()
        logger.info(f"Active WebSocket connections: {len(connections)}")
        await handler.cleanup()
        return True
    except Exception as e:
        logger.error(f"WebSocket check failed: {str(e)}")
        return False

async def run_system_checkup():
    """Run comprehensive system checkup"""
    logger.info("Starting system checkup...")

    checks = {
        "Memory Usage": await check_memory_usage(),
        "WebSocket Connections": await check_websocket_connections(),
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
            else:
                logger.error(f"✗ Data loading failed for {symbol}")
                checks[f"Data Loading {symbol}"] = False
        except Exception as e:
            logger.error(f"Error loading data for {symbol}: {str(e)}")
            checks[f"Data Loading {symbol}"] = False

    # Test 2: Database Connection
    logger.info("\nTest 2: Database Connection")
    db = DatabaseManager()
    try:
        if await db.verify_connection():
            logger.info("✓ Database connection successful")
            checks["Database Connection"] = True
        else:
            logger.error("✗ Database connection failed")
            checks["Database Connection"] = False
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        checks["Database Connection"] = False


    # Test 3: Sentiment Analysis
    logger.info("\nTest 3: Sentiment Analysis")
    sentiment_analyzer = SentimentAnalyzer()
    for symbol in symbols:
        try:
            sentiment = await sentiment_analyzer.analyze_sentiment(symbol)
            logger.info(f"Sentiment for {symbol}: {sentiment}")
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
        except Exception as e:
            logger.error(f"Signal generation failed for {symbol}: {str(e)}")
            checks[f"Trading Signals {symbol}"] = False

    # Report results
    logger.info("\nSystem Checkup Results:")
    for check, result in checks.items():
        logger.info(f"{check}: {'✓' if result else '✗'}")

    return all(checks.values())

if __name__ == "__main__":
    asyncio.run(run_system_checkup())