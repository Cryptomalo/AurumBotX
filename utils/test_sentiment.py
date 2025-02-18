import os
import sys
import asyncio
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.sentiment_analyzer import SentimentAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'sentiment_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

async def test_sentiment_analysis():
    """Test the sentiment analyzer with error handling and fallbacks"""
    try:
        analyzer = SentimentAnalyzer()
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]  # Test multiple symbols
        results = []

        logger.info("Starting sentiment analysis tests...")

        for symbol in symbols:
            try:
                logger.info(f"Testing sentiment analysis for {symbol}")
                result = await analyzer.analyze_sentiment(symbol)

                # Validate result structure
                if not isinstance(result, dict):
                    logger.error(f"Invalid result type for {symbol}: {type(result)}")
                    continue

                if "error" in result:
                    logger.warning(f"Analysis returned error for {symbol}: {result['error']}")
                else:
                    logger.info(f"Sentiment analysis result for {symbol}: {result}")

                results.append({
                    "symbol": symbol,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })

            except Exception as symbol_e:
                logger.error(f"Error analyzing {symbol}: {str(symbol_e)}")
                continue

        # Print summary
        logger.info("\nTest Summary:")
        logger.info(f"Total symbols tested: {len(symbols)}")
        logger.info(f"Successful analyses: {len(results)}")
        logger.info(f"Failed analyses: {len(symbols) - len(results)}")

        return len(results) > 0

    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        asyncio.run(test_sentiment_analysis())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")