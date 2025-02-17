from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from utils.learning_module import LearningModule

logger = logging.getLogger(__name__)

class MemeCoinStrategy:
    """Strategia ottimizzata per meme coin con machine learning"""

    def __init__(self, config: Dict[str, Any]):
        self.name = "Meme Coin Strategy"
        self.config = config
        self.sentiment_threshold = config.get('sentiment_threshold', 0.7)
        self.viral_coefficient = config.get('viral_coefficient', 0.8)
        self.min_liquidity = config.get('min_liquidity', 5)
        self.max_buy_tax = config.get('max_buy_tax', 10)
        self.min_holders = config.get('min_holders', 50)
        self.risk_per_trade = config.get('risk_per_trade', 0.01)
        self._token_cache = {}
        self._cache_duration = timedelta(minutes=5)

        # Inizializza il modulo di machine learning
        self.learning_module = LearningModule()
        self.min_prediction_confidence = config.get('min_prediction_confidence', 0.7)

    def analyze_market(self, market_data: Dict, sentiment_data: Optional[Dict] = None) -> List[Dict]:
        """Analisi ottimizzata del mercato per meme coin con predizioni ML"""
        try:
            if not market_data or not sentiment_data:
                logger.info("Dati di mercato o sentiment mancanti")
                return []

            if not self._validate_basic_requirements(market_data, sentiment_data):
                logger.info("Requisiti base non soddisfatti")
                return []

            token_metrics = self._calculate_token_metrics(market_data)
            if not token_metrics['valid']:
                logger.info("Metriche token non valide")
                return []

            # Prepara features per predizione ML
            ml_features = self._prepare_ml_features(market_data, sentiment_data, token_metrics)
            success_probability = self.learning_module.predict_success_probability(ml_features)

            if success_probability < self.min_prediction_confidence:
                logger.info(f"Probabilità di successo troppo bassa: {success_probability:.2f}")
                return []

            entry_points = self._calculate_entry_points(market_data, token_metrics, success_probability)
            signals = [self._create_signal(market_data, entry, success_probability) 
                      for entry in entry_points]

            logger.info(f"Generati {len(signals)} segnali di trading")
            return signals

        except Exception as e:
            logger.error(f"Errore nell'analisi del mercato: {e}")
            return []

    def _prepare_ml_features(self, market_data: Dict, sentiment_data: Dict, 
                           token_metrics: Dict) -> Dict[str, float]:
        """Prepara features per il modello ML"""
        try:
            return {
                'price': float(market_data.get('price', 0)),
                'volume': token_metrics.get('volume', 0),
                'volatility': market_data.get('volatility', 0),
                'rsi': market_data.get('indicators', {}).get('rsi', 50),
                'macd': market_data.get('indicators', {}).get('macd', 0),
                'sentiment_score': sentiment_data.get('score', 0.5),
                'viral_score': sentiment_data.get('viral_coefficient', 0.5),
                'holder_count': token_metrics.get('estimated_holders', 0),
                'liquidity': token_metrics.get('liquidity', 0),
                'momentum': token_metrics.get('momentum', 0),
                'confidence': min(
                    sentiment_data.get('confidence', 0.5),
                    market_data.get('technical_confidence', 0.5)
                )
            }
        except Exception as e:
            logger.error(f"Errore nella preparazione features ML: {e}")
            return {}

    def _validate_basic_requirements(self, market_data: Dict, sentiment_data: Dict) -> bool:
        """Validazione requisiti base"""
        try:
            sentiment_score = sentiment_data.get('score', 0)
            liquidity = market_data.get('liquidity', 0)

            if sentiment_score < self.sentiment_threshold:
                logger.info(f"Sentiment score troppo basso: {sentiment_score}")
                return False

            if liquidity < self.min_liquidity * 1000:
                logger.info(f"Liquidità troppo bassa: {liquidity}")
                return False

            return True

        except Exception as e:
            logger.error(f"Errore nella validazione: {e}")
            return False

    def _calculate_token_metrics(self, market_data: Dict) -> Dict[str, Any]:
        """Calcolo ottimizzato metriche token"""
        try:
            volume = float(market_data.get('volume_24h', 0))
            liquidity = float(market_data.get('liquidity', 0))
            price = float(market_data.get('price', 0))

            if not all([volume, liquidity, price]):
                return {'valid': False}

            return {
                'valid': True,
                'volume': volume,
                'liquidity': liquidity,
                'price': price,
                'momentum': min(volume / (liquidity + 1) * 0.5, 1.0),
                'estimated_holders': min(int((volume * 0.1 + liquidity * 0.2) / 1000), 10000)
            }

        except Exception as e:
            logger.error(f"Errore nel calcolo metriche: {e}")
            return {'valid': False}

    def _calculate_entry_points(self, market_data: Dict, metrics: Dict, 
                              ml_confidence: float) -> List[Dict]:
        """Calcolo punti di ingresso con ML confidence"""
        try:
            price = metrics['price']
            momentum = metrics['momentum']

            # Combina confidence ML con altre metriche
            confidence = min(
                0.7 + 
                (metrics['liquidity'] / 1000000) * 0.1 +
                momentum * 0.2 +
                ml_confidence * 0.3,  # Peso maggiore alla predizione ML
                0.95  # Cap massimo
            )

            return [{
                'price': price,
                'stop_loss': price * (0.95 + (1 - ml_confidence) * 0.03),  # Stop loss dinamico
                'take_profit': price * (1.3 + ml_confidence * 0.2),  # Take profit dinamico
                'confidence': confidence
            }]

        except Exception as e:
            logger.error(f"Errore nel calcolo entry points: {e}")
            return []

    def _create_signal(self, market_data: Dict, entry: Dict, ml_confidence: float) -> Dict:
        """Creazione segnale trading con ML insights"""
        try:
            position_size = self._calculate_position_size(entry['price'], ml_confidence)

            return {
                'action': 'BUY',
                'symbol': market_data['symbol'],
                'entry_price': entry['price'],
                'position_size': position_size,
                'stop_loss': entry['stop_loss'],
                'take_profit': entry['take_profit'],
                'confidence': entry['confidence'],
                'ml_confidence': ml_confidence,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Errore nella creazione del segnale: {e}")
            return {}

    def _calculate_position_size(self, price: float, ml_confidence: float) -> float:
        """Calcolo dimensione posizione basata su ML confidence"""
        try:
            # Aumenta position size in base alla confidenza ML
            base_size = self.risk_per_trade * price
            adjusted_size = base_size * (1 + (ml_confidence - 0.5))
            return min(adjusted_size, self.config.get('max_position_size', float('inf')))
        except Exception as e:
            logger.error(f"Errore nel calcolo position size: {e}")
            return 0.0

    def validate_trade(self, signal: Dict[str, Any], portfolio: Dict[str, Any]) -> bool:
        """Validazione trade con ML insights"""
        try:
            return (
                signal.get('confidence', 0) >= 0.7 and
                signal.get('ml_confidence', 0) >= self.min_prediction_confidence and
                signal.get('position_size', 0) > 0 and
                signal.get('position_size') <= portfolio.get('available_balance', 0) and
                signal.get('position_size') <= portfolio.get('total_balance', 0) * self.risk_per_trade
            )
        except Exception as e:
            logger.error(f"Errore nella validazione trade: {e}")
            return False

    def execute_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Esecuzione trade con tracking ML performance"""
        try:
            result = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'entry_price': signal['entry_price'],
                'position_size': signal['position_size'],
                'symbol': signal['symbol'],
                'ml_confidence': signal.get('ml_confidence', 0)
            }

            # Aggiungi risultato al training set
            self.learning_module.add_trade_result({
                **signal,
                'success': True,
                'price': signal['entry_price'],
                'volume': signal.get('volume', 0),
                'indicators': {
                    'rsi': signal.get('rsi', 50),
                    'macd': signal.get('macd', 0)
                }
            })

            return result

        except Exception as e:
            logger.error(f"Errore nell'esecuzione trade: {e}")
            return {'success': False, 'error': str(e)}