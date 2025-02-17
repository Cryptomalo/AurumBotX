import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from utils.strategies.meme_coin_sniping import MemeCoinStrategy

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_meme_strategy():
    try:
        # Configurazione di test
        config = {
            'sentiment_threshold': 0.7,
            'viral_coefficient': 0.8,
            'min_liquidity': 5,
            'max_buy_tax': 10,
            'min_holders': 50,
            'risk_per_trade': 0.01,
            'rpc_url': 'https://api.mainnet-beta.solana.com'
        }

        # Inizializza strategia
        strategy = MemeCoinStrategy(config)
        logger.info("Strategia meme coin inizializzata")

        # Dati di mercato di test
        market_data = {
            'symbol': 'PEPE/USDT',
            'price': 0.000001234,
            'volume_24h': 1000000,
            'liquidity': 500000,
            'address': '0x123...',
            'holders': 1000
        }

        # Dati sentiment di test
        sentiment_data = {
            'score': 0.85,
            'mentions': 1000,
            'social_volume': 5000,
            'trending_score': 0.9
        }

        # Test analisi mercato
        risk_score = 0.3
        signals = await strategy.analyze_market(market_data, sentiment_data, risk_score)
        
        if signals:
            logger.info(f"Segnali generati: {signals}")
            
            # Test validazione trade
            portfolio = {'available_balance': 1000, 'total_balance': 10000}
            for signal in signals:
                is_valid = await strategy.validate_trade(signal, portfolio)
                logger.info(f"Validazione trade: {is_valid}")
                
                if is_valid:
                    # Test esecuzione trade
                    result = await strategy.execute_trade(signal)
                    logger.info(f"Risultato esecuzione: {result}")
        else:
            logger.info("Nessun segnale generato")

    except Exception as e:
        logger.error(f"Errore nel test della strategia: {e}")

if __name__ == "__main__":
    asyncio.run(test_meme_strategy())
