from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MemeCoinStrategy:
    """Strategia ottimizzata per meme coin"""

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

    def analyze_market(self, market_data: Dict, sentiment_data: Optional[Dict] = None) -> List[Dict]:
        """Analisi ottimizzata del mercato per meme coin"""
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

            entry_points = self._calculate_entry_points(market_data, token_metrics)
            signals = [self._create_signal(market_data, entry) for entry in entry_points]

            logger.info(f"Generati {len(signals)} segnali di trading")
            return signals

        except Exception as e:
            logger.error(f"Errore nell'analisi del mercato: {e}")
            return []

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

    def _calculate_entry_points(self, market_data: Dict, metrics: Dict) -> List[Dict]:
        """Calcolo punti di ingresso"""
        try:
            price = metrics['price']
            momentum = metrics['momentum']

            confidence = min(
                0.7 + 
                (metrics['liquidity'] / 1000000) * 0.1 +
                momentum * 0.2,
                0.9
            )

            return [{
                'price': price,
                'stop_loss': price * 0.95,
                'take_profit': price * 1.3,
                'confidence': confidence
            }]

        except Exception as e:
            logger.error(f"Errore nel calcolo entry points: {e}")
            return []

    def _create_signal(self, market_data: Dict, entry: Dict) -> Dict:
        """Creazione segnale trading"""
        try:
            position_size = self._calculate_position_size(entry['price'])

            return {
                'action': 'BUY',
                'symbol': market_data['symbol'],
                'entry_price': entry['price'],
                'position_size': position_size,
                'stop_loss': entry['stop_loss'],
                'take_profit': entry['take_profit'],
                'confidence': entry['confidence'],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Errore nella creazione del segnale: {e}")
            return {}

    def _calculate_position_size(self, price: float) -> float:
        """Calcolo dimensione posizione"""
        try:
            base_size = self.risk_per_trade * price
            return min(base_size, self.config.get('max_position_size', float('inf')))
        except Exception as e:
            logger.error(f"Errore nel calcolo position size: {e}")
            return 0.0

    def validate_trade(self, signal: Dict[str, Any], portfolio: Dict[str, Any]) -> bool:
        """Validazione trade"""
        try:
            return (
                signal.get('confidence', 0) >= 0.7 and
                signal.get('position_size', 0) > 0 and
                signal.get('position_size') <= portfolio.get('available_balance', 0) and
                signal.get('position_size') <= portfolio.get('total_balance', 0) * self.risk_per_trade
            )
        except Exception as e:
            logger.error(f"Errore nella validazione trade: {e}")
            return False

    def execute_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Esecuzione trade"""
        try:
            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'entry_price': signal['entry_price'],
                'position_size': signal['position_size'],
                'symbol': signal['symbol']
            }
        except Exception as e:
            logger.error(f"Errore nell'esecuzione trade: {e}")
            return {'success': False, 'error': str(e)}