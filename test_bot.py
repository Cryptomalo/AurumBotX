import logging
from datetime import datetime
import time
from utils.auto_trader import AutoTrader
from utils.data_loader import CryptoDataLoader
from utils.strategies.strategy_manager import StrategyManager
from utils.sentiment_analyzer import SentimentAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=f'test_bot_{datetime.now().strftime("%Y%m%d")}.log'
)
logger = logging.getLogger(__name__)

async def test_bot():
    try:
        logger.info("Inizializzazione test trading bot")

        # Test componenti
        strategy_manager = StrategyManager()
        sentiment_analyzer = SentimentAnalyzer()
        data_loader = CryptoDataLoader()

        # Verifica connessione dati
        logger.info("Test connessione dati...")
        df = data_loader.get_historical_data("BTC-USD", period='1d')
        if df is None or df.empty:
            raise Exception("Impossibile ottenere dati storici")

        # Test strategia DEX
        logger.info("Test strategia DEX...")
        config = {
            'rpc_url': 'https://bsc-dataseed.binance.org/',
            'min_liquidity': 5,
            'max_buy_tax': 10,
            'min_holders': 50
        }

        await strategy_manager.activate_strategy('dex_sniping', config)

        # Test sentiment analysis
        logger.info("Test analisi sentiment...")
        sentiment_data = await sentiment_analyzer.analyze_social_sentiment("BTC")
        if sentiment_data:
            logger.info(f"Sentiment score: {sentiment_data.get('score', 0)}")

        # Test trading signals
        signals = await strategy_manager.execute_strategies(df)
        if signals:
            logger.info(f"Segnali generati: {len(signals)}")
            for signal in signals:
                logger.info(f"Segnale: {signal}")

        return True

    except Exception as e:
        logger.error(f"Test fallito: {str(e)}")
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_bot())
    print(f"Test completato: {'Successo' if success else 'Fallito'}")