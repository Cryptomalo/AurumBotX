import logging
from datetime import datetime
from typing import Dict, Any
from utils.strategies.meme_coin_sniping import MemeCoinStrategy
import numpy as np

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
            'risk_per_trade': 0.01,
            'phone_number': '+1234567890'  # Test phone number
        }

        # Inizializza strategia
        strategy = MemeCoinStrategy(config)
        logger.info("Strategia inizializzata")

        # Dati storici di training per il modello ML
        historical_trades = []
        logger.info("Generazione dati storici di training...")

        np.random.seed(42)  # Per riproducibilità

        # Funzione per generare dati più realistici
        def generate_trade_data(index: int) -> Dict[str, Any]:
            # Base price con trend e volatilità
            base_price = 0.000001234 * (1 + 0.0001 * index + np.random.normal(0, 0.2))

            # Volume con trend e stagionalità
            base_volume = 1000000 * (1 + np.sin(index/10) + np.random.normal(0, 0.5))

            # Indicatori tecnici correlati
            rsi = 50 + 20 * np.sin(index/5) + np.random.normal(0, 10)
            rsi = max(0, min(100, rsi))

            macd = 0.0001 * np.sin(index/7) + np.random.normal(0, 0.0001)

            # Sentiment e viralità correlati
            sentiment = 0.7 + 0.2 * np.sin(index/8) + np.random.normal(0, 0.1)
            sentiment = max(0, min(1, sentiment))

            viral = 0.8 + 0.15 * np.sin(index/6) + np.random.normal(0, 0.1)
            viral = max(0, min(1, viral))

            # Momentum basato su prezzo e volume
            momentum = (1 + np.sin(index/9)) * 0.5 + np.random.normal(0, 0.1)
            momentum = max(0, min(1, momentum))

            # Success probability based on indicators
            success_probability = (
                0.3 * (rsi - 30) / 70 +  # RSI contribution
                0.2 * (sentiment - 0.5) / 0.5 +  # Sentiment contribution
                0.2 * (viral - 0.5) / 0.5 +  # Viral contribution
                0.3 * momentum  # Momentum contribution
            )
            is_successful = np.random.random() < success_probability

            return {
                'price': max(0.000000001, base_price),
                'volume': max(100, base_volume),
                'volatility': max(0.01, min(1.0, abs(np.random.normal(0.15, 0.05)))),
                'rsi': rsi,
                'macd': macd,
                'sentiment_score': sentiment,
                'viral_score': viral,
                'holder_count': int(np.random.uniform(100, 10000)),
                'liquidity': max(10000, np.random.uniform(100000, 2000000)),
                'momentum': momentum,
                'confidence': max(0, min(1, 0.5 + 0.3 * np.random.normal(0, 1))),
                'success': 1 if is_successful else 0
            }

        for i in range(100):  # Generate 100 sample trades
            trade = generate_trade_data(i)
            historical_trades.append(trade)
            if i % 20 == 0:
                logger.info(f"Generati {i+1} trade storici")

        # Addestra il modello ML
        logger.info("Addestramento modello ML...")
        for trade in historical_trades:
            strategy.learning_module.add_trade_result(trade)

        success = strategy.learning_module.train_model()
        if not success:
            logger.error("Errore nell'addestramento del modello ML")
            return

        # Stampa metriche di performance
        metrics = strategy.learning_module.get_model_metrics()
        logger.info("Performance del modello ML:")
        logger.info(f"Random Forest - Precision: {metrics['rf_metrics']['precision']:.2f}, "
                   f"Recall: {metrics['rf_metrics']['recall']:.2f}, "
                   f"F1: {metrics['rf_metrics']['f1']:.2f}")
        logger.info(f"Gradient Boosting - Precision: {metrics['gb_metrics']['precision']:.2f}, "
                   f"Recall: {metrics['gb_metrics']['recall']:.2f}, "
                   f"F1: {metrics['gb_metrics']['f1']:.2f}")

        # Feature importance
        important_features = strategy.learning_module.get_important_features(top_n=5)
        logger.info("Top 5 feature più importanti:")
        for feature in important_features:
            logger.info(f"{feature['feature']}: {feature['importance']:.3f}")

        logger.info("Modello ML addestrato con successo")

        # Salva il modello addestrato
        try:
            strategy.learning_module.save_model('meme_strategy_model.joblib')
            logger.info("Modello salvato con successo")
        except Exception as e:
            logger.error(f"Errore nel salvataggio del modello: {e}")

        # Dati di test più realistici basati sulla stessa distribuzione
        test_data = generate_trade_data(101)  # Nuovo trade fuori dal training set

        market_data = {
            'symbol': 'PEPE/USDT',
            'price': test_data['price'],
            'volume_24h': test_data['volume'],
            'liquidity': test_data['liquidity'],
            'volatility': test_data['volatility'],
            'indicators': {
                'rsi': test_data['rsi'],
                'macd': test_data['macd']
            },
            'momentum': test_data['momentum']
        }

        sentiment_data = {
            'score': test_data['sentiment_score'],
            'confidence': test_data['confidence'],
            'mentions': 1000,
            'social_volume': 5000,
            'trending_score': test_data['viral_score'],
            'viral_coefficient': test_data['viral_score']
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