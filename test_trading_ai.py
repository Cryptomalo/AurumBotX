import logging
import asyncio
from datetime import datetime, timedelta

from utils.data_loader import CryptoDataLoader
from utils.ai_trading import AITradingSystem
from utils.learning_module import LearningModule
from utils.sentiment_analyzer import SentimentAnalyzer
from utils.strategies.strategy_manager import StrategyManager

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
        strategy_manager = StrategyManager()
        ai_trading = AITradingSystem({
            'min_confidence': 0.7,
            'risk_threshold': 0.8,
            'default_timeframe': '1h',
            'use_sentiment': True,
            'max_positions': 3
        })

        # Test 1: Caricamento e analisi dati storici
        logger.info("Test 1: Analisi dati storici")
        symbols = ["BTCUSDT", "ETHUSDT"]
        for symbol in symbols:
            market_data = await ai_trading.analyze_market(symbol)
            if market_data:
                logger.info(f"Analisi completata per {symbol}")
                logger.info(f"Indicatori tecnici: {market_data.get('market_data', {})}")
                logger.info(f"Sentiment: {market_data.get('sentiment', {})}")

        # Test 2: Generazione segnali di trading
        logger.info("\nTest 2: Generazione segnali di trading")
        for symbol in symbols:
            signals = await ai_trading.generate_trading_signals(symbol)
            if signals:
                for signal in signals:
                    logger.info(f"\nSegnale generato per {symbol}:")
                    logger.info(f"Azione: {signal['action']}")
                    logger.info(f"Confidence: {signal['confidence']:.2f}")
                    logger.info(f"Risk Score: {signal['analysis']['risk_score']:.2f}")

        # Test 3: Backtesting
        logger.info("\nTest 3: Backtesting della strategia")
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        for symbol in symbols:
            results = await ai_trading.backtest_strategy(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )

            if 'error' not in results:
                logger.info(f"\nRisultati backtesting per {symbol}:")
                logger.info(f"Numero segnali: {len(results['signals'])}")
                logger.info(f"Valore finale: {results['final_value']:.2f}")
                logger.info(f"Trades totali: {results['total_trades']}")

        # Test 4: Validazione segnali
        logger.info("\nTest 4: Validazione segnali")
        test_signal = {
            'symbol': 'BTCUSDT',
            'action': 'buy',
            'confidence': 0.85,
            'price': 50000,
            'timestamp': datetime.now().isoformat(),
            'analysis': {
                'technical_score': 0.75,
                'sentiment_score': 0.8,
                'risk_score': 0.4,
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