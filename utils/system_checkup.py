
import logging
import asyncio
from datetime import datetime
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

async def run_system_checkup():
    """Run comprehensive system checkup"""
    logger.info("Starting system checkup...")
    
    # Test 1: Data Loading
    logger.info("Test 1: Data Loading")
    data_loader = CryptoDataLoader()
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    
    for symbol in symbols:
        data = await data_loader.get_historical_data(symbol, period='1d')
        if data is not None and not data.empty:
            logger.info(f"✓ Data loading successful for {symbol}: {len(data)} rows")
            logger.info(f"Latest price: {data['Close'].iloc[-1]:.2f}")
        else:
            logger.error(f"✗ Data loading failed for {symbol}")

    # Test 2: Sentiment Analysis
    logger.info("\nTest 2: Sentiment Analysis")
    sentiment_analyzer = SentimentAnalyzer()
    for symbol in symbols:
        sentiment = await sentiment_analyzer.analyze_sentiment(symbol)
        logger.info(f"Sentiment for {symbol}: {sentiment}")

    # Test 3: Prediction Model
    logger.info("\nTest 3: Prediction Model")
    prediction_model = PredictionModel()
    for symbol in symbols:
        data = await data_loader.get_historical_data(symbol, period='1d')
        if data is not None:
            prediction = await prediction_model.analyze_market_with_ai(data, {})
            logger.info(f"Prediction for {symbol}: {prediction}")

    # Test 4: Trading System
    logger.info("\nTest 4: Trading System")
    trading = AITrading()
    for symbol in symbols:
        signals = await trading.generate_trading_signals(symbol)
        logger.info(f"Generated signals for {symbol}: {signals}")

    # Test 5: Database Connection
    logger.info("\nTest 5: Database Connection")
    db = DatabaseManager()
    if await db.verify_connection():
        logger.info("✓ Database connection successful")
    else:
        logger.error("✗ Database connection failed")

    logger.info("\nSystem checkup completed")

if __name__ == "__main__":
    asyncio.run(run_system_checkup())
