import streamlit as st
import logging
import sys
import asyncio
from utils.trading_bot import WebSocketHandler
from utils.database import Database
from utils.strategies.strategy_manager import StrategyManager
from utils.sentiment_analyzer import SentimentAnalyzer
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('aurumbot_test.log')
    ]
)
logger = logging.getLogger(__name__)

async def test_components():
    """Test delle componenti principali del bot"""
    try:
        st.title("AurumBot Test Dashboard")
        st.write("Verifica delle componenti...")

        # Inizializzazione componenti
        db = Database(os.environ['DATABASE_URL'])
        strategy_manager = StrategyManager()
        sentiment_analyzer = SentimentAnalyzer()

        # Test WebSocket
        websocket_handler = WebSocketHandler(logger, db)
        ws_status = await websocket_handler.connect_websocket()

        if ws_status:
            st.success("✅ WebSocket connesso correttamente")
        else:
            st.error("❌ Errore nella connessione WebSocket")

        # Test Strategie
        st.write("Test strategie di trading...")
        try:
            await strategy_manager.activate_strategy('dex_sniping', {
                'rpc_url': 'https://bsc-dataseed.binance.org/',
                'min_liquidity': 5,
                'max_buy_tax': 10,
                'min_holders': 50
            })
            st.success("✅ Strategie inizializzate correttamente")
        except Exception as e:
            st.error(f"❌ Errore nell'inizializzazione strategie: {str(e)}")

        # Test Sentiment Analysis
        st.write("Test analisi sentiment...")
        try:
            sentiment = await sentiment_analyzer.analyze_social_sentiment("BTC")
            if sentiment:
                st.success(f"✅ Sentiment Analysis funzionante: {sentiment['score']}")
            else:
                st.warning("⚠️ Nessun dato sentiment disponibile")
        except Exception as e:
            st.error(f"❌ Errore nell'analisi sentiment: {str(e)}")

    except Exception as e:
        st.error(f"Errore generale: {str(e)}")
        logger.error(f"Test fallito: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_components())