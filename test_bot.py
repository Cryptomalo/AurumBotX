import asyncio
import logging
from datetime import datetime
import os
from utils.trading_bot import WebSocketHandler
from utils.strategies.strategy_manager import StrategyManager
from utils.sentiment_analyzer import SentimentAnalyzer
from utils.database import Database

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=f'test_bot_{datetime.now().strftime("%Y%m%d")}.log'
)
logger = logging.getLogger(__name__)

async def test_bot():
    """Test delle componenti principali del bot"""
    try:
        logger.info("Inizializzazione test trading bot")

        # Inizializzazione database
        db = Database(os.environ.get('DATABASE_URL'))
        if not db.connect():
            raise Exception("Errore connessione database")

        # Test componenti
        strategy_manager = StrategyManager()
        sentiment_analyzer = SentimentAnalyzer()

        # Test WebSocket
        websocket_handler = WebSocketHandler(logger, db)
        ws_status = await websocket_handler.connect_websocket()
        if not ws_status:
            logger.error("Errore connessione WebSocket")
            return False

        logger.info("Connessione WebSocket stabilita")

        # Test strategia DEX
        config = {
            'rpc_url': 'https://bsc-dataseed.binance.org/',
            'min_liquidity': 5,
            'max_buy_tax': 10,
            'min_holders': 50
        }

        try:
            await strategy_manager.activate_strategy('dex_sniping', config)
            logger.info("Strategia DEX attivata con successo")
        except Exception as e:
            logger.error(f"Errore attivazione strategia: {e}")
            return False

        # Test sentiment analysis
        try:
            sentiment_data = await sentiment_analyzer.analyze_social_sentiment("BTC")
            if sentiment_data:
                logger.info(f"Sentiment score: {sentiment_data.get('score', 0)}")
        except Exception as e:
            logger.error(f"Errore analisi sentiment: {e}")
            return False

        logger.info("Test completato con successo")
        return True

    except Exception as e:
        logger.error(f"Test fallito: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bot())
    print(f"Test completato: {'Successo' if success else 'Fallito'}")