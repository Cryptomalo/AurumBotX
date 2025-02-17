import logging
import asyncio
from datetime import datetime, timedelta

from utils.data_loader import CryptoDataLoader
from utils.ai_trading import AITrading
from utils.sentiment_analyzer import SentimentAnalyzer

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_trading_system():
    """Test completo del sistema di trading con AI"""
    try:
        logger.info("Inizializzazione componenti del sistema...")

        # Inizializza i componenti
        data_loader = CryptoDataLoader()
        sentiment_analyzer = SentimentAnalyzer()
        ai_trading = AITrading({
            'min_confidence': 0.7,
            'use_sentiment': True
        })

        # Test 1: Analisi dati storici
        logger.info("Test 1: Analisi dati storici")
        symbols = ["BTCUSDT", "ETHUSDT"]
        for symbol in symbols:
            market_data = await ai_trading.analyze_market(symbol)
            if market_data:
                logger.info(f"Analisi completata per {symbol}")
                logger.info(f"Dati mercato: {market_data.get('market_data', {})}")
                logger.info(f"Sentiment: {market_data.get('sentiment', {})}")

        # Test 2: Generazione segnali di trading
        logger.info("\nTest 2: Generazione segnali di trading")
        for symbol in symbols:
            signals = await ai_trading.generate_trading_signals(symbol)
            if signals:
                for signal in signals:
                    logger.info(f"\nSegnale generato per {symbol}:")
                    logger.info(f"Azione: {signal['action']}")
                    logger.info(f"Confidenza: {signal['confidence']:.2f}")
                    logger.info(f"Analisi: {signal['analysis']}")

        # Test 3: Validazione segnali
        logger.info("\nTest 3: Validazione segnali")
        test_signal = {
            'symbol': 'BTCUSDT',
            'action': 'buy',
            'confidence': 0.85,
            'price': 50000,
            'timestamp': datetime.now().isoformat(),
            'analysis': {
                'technical_score': 0.75,
                'sentiment_score': 0.8,
                'market_data': {
                    'rsi': 45,
                    'trend': 1
                }
            }
        }

        is_valid = await ai_trading.validate_signal(test_signal)
        logger.info(f"Segnale test valido: {is_valid}")

    except Exception as e:
        logger.error(f"Errore durante il test: {str(e)}", exc_info=True)

if __name__ == "__main__":
    logger.info("Avvio test del sistema di trading...")
    asyncio.run(test_trading_system())