import logging
from datetime import datetime
from typing import Dict, Any
from utils.strategies.meme_coin_sniping import MemeCoinStrategy

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_meme_strategy():
    """Test della strategia meme coin"""
    try:
        logger.info("Inizializzazione test meme coin strategy")

        # Configurazione
        config = {
            'sentiment_threshold': 0.7,
            'viral_coefficient': 0.8,
            'min_liquidity': 5,
            'max_buy_tax': 10,
            'min_holders': 50,
            'risk_per_trade': 0.01
        }

        # Inizializza strategia
        strategy = MemeCoinStrategy(config)
        logger.info("Strategia inizializzata")

        # Dati di test
        market_data = {
            'symbol': 'PEPE/USDT',
            'price': 0.000001234,
            'volume_24h': 1000000,
            'liquidity': 500000,
        }

        sentiment_data = {
            'score': 0.85,
            'mentions': 1000,
            'social_volume': 5000,
            'trending_score': 0.9
        }

        logger.info("Analisi mercato...")
        signals = strategy.analyze_market(market_data, sentiment_data)

        if signals:
            logger.info(f"Generati {len(signals)} segnali")
            for signal in signals:
                logger.info(f"Segnale: {signal}")

                # Test validazione
                portfolio = {
                    'available_balance': 1000,
                    'total_balance': 10000
                }

                logger.info("Validazione trade...")
                is_valid = strategy.validate_trade(signal, portfolio)
                logger.info(f"Trade valido: {is_valid}")

                if is_valid:
                    logger.info("Esecuzione trade...")
                    result = strategy.execute_trade(signal)
                    logger.info(f"Risultato: {result}")
        else:
            logger.info("Nessun segnale generato")

    except Exception as e:
        logger.error(f"Errore nel test: {e}")
        raise

if __name__ == "__main__":
    test_meme_strategy()