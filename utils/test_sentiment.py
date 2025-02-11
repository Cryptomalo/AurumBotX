import os
import asyncio
import logging
from utils.sentiment_analyzer import SentimentAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_sentiment_analysis():
    """Test the sentiment analyzer with the OpenAI assistant"""
    try:
        analyzer = SentimentAnalyzer()
        symbol = "BTC/USD"

        logger.info(f"Testing sentiment analysis for {symbol}")
        result = await analyzer.analyze_social_sentiment(symbol)

        if result.get("error"):
            logger.error(f"Error in sentiment analysis: {result['error']}")
            return False

        logger.info(f"Sentiment analysis result: {result}")
        return True

    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    # Add the project root to Python path
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    asyncio.run(test_sentiment_analysis())