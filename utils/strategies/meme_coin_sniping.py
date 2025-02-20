import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import asyncio
from utils.learning_module import LearningModule
from utils.notifications import NotificationManager, NotificationPriority, NotificationCategory
from utils.strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class MemeCoinStrategy(BaseStrategy):
    """Strategia ottimizzata per meme coin con machine learning"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("Meme Coin Strategy", config)
        self.sentiment_threshold = config.get('sentiment_threshold', 0.7)
        self.viral_coefficient = config.get('viral_coefficient', 0.8)
        self.min_liquidity = config.get('min_liquidity', 5)
        self.max_buy_tax = config.get('max_buy_tax', 10)
        self.min_holders = config.get('min_holders', 50)
        self.risk_per_trade = config.get('risk_per_trade', 0.01)
        self._token_cache = {}
        self._cache_duration = timedelta(minutes=5)

        # Initialize ML module and notifications
        self.learning_module = LearningModule()
        self.notifier = NotificationManager()
        self.min_prediction_confidence = config.get('min_prediction_confidence', 0.7)
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """Initialize strategy asynchronously"""
        if self.config.get('phone_number'):
            await self.notifier.setup(self.config['phone_number'])

    async def analyze_market(self, market_data: Dict, sentiment_data: Optional[Dict] = None) -> List[Dict]:
        """Analyze market for meme coins with ML predictions"""
        try:
            if not market_data:
                self.logger.warning("Missing market data")
                return []

            # Default sentiment data if not provided
            if not sentiment_data:
                sentiment_data = {
                    'score': 0.5,
                    'confidence': 0.5,
                    'viral_coefficient': 0.5
                }

            if not await self._validate_basic_requirements(market_data, sentiment_data):
                self.logger.info("Basic requirements not met")
                return []

            token_metrics = await self._calculate_token_metrics(market_data)
            if not token_metrics['valid']:
                self.logger.info("Invalid token metrics")
                return []

            # Prepare ML features
            ml_features = await self._prepare_ml_features(market_data, sentiment_data, token_metrics)
            success_probability = await self.learning_module.predict_success_probability(ml_features)

            if success_probability < self.min_prediction_confidence:
                self.logger.info(f"Success probability too low: {success_probability:.2f}")
                return []

            entry_points = await self._calculate_entry_points(market_data, token_metrics, success_probability)
            signals = [await self._create_signal(market_data, entry, success_probability)
                      for entry in entry_points]

            # Notify significant analysis
            if signals:
                notification_content = {
                    'type': 'analysis',
                    'symbol': market_data.get('symbol', 'Unknown'),
                    'data': {
                        'ml_confidence': success_probability,
                        'technical_score': token_metrics.get('momentum', 0),
                        'sentiment_score': sentiment_data.get('score', 0),
                        'viral_score': sentiment_data.get('viral_coefficient', 0)
                    }
                }
                await self.notifier.send_notification(
                    notification_content,
                    priority=NotificationPriority.HIGH,
                    category=NotificationCategory.MARKET
                )

            self.logger.info(f"Generated {len(signals)} trading signals")
            return signals

        except Exception as e:
            self.logger.error(f"Market analysis error: {e}")
            return []

    async def _validate_basic_requirements(self, market_data: Dict, sentiment_data: Dict) -> bool:
        """Validate basic requirements with improved error handling"""
        try:
            sentiment_score = float(sentiment_data.get('score', 0))
            liquidity = float(market_data.get('liquidity', 0))
            volume = float(market_data.get('volume_24h', 0))

            if sentiment_score < self.sentiment_threshold:
                self.logger.info(f"Sentiment score too low: {sentiment_score}")
                return False

            if liquidity < self.min_liquidity * 1000:
                self.logger.info(f"Liquidity too low: {liquidity}")
                return False

            if volume < 1000:  # Minimum daily volume
                self.logger.info(f"Volume too low: {volume}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return False

    async def _calculate_token_metrics(self, market_data: Dict) -> Dict[str, Any]:
        """Calculate optimized token metrics"""
        try:
            volume = float(market_data.get('volume_24h', 0))
            liquidity = float(market_data.get('liquidity', 0))
            price = float(market_data.get('price', 0))

            if not all([volume > 0, liquidity > 0, price > 0]):
                return {'valid': False}

            # Calculate optimized momentum
            momentum = await self._calculate_momentum(market_data)

            return {
                'valid': True,
                'volume': volume,
                'liquidity': liquidity,
                'price': price,
                'momentum': momentum,
                'estimated_holders': min(int((volume * 0.1 + liquidity * 0.2) / 1000), 10000)
            }

        except Exception as e:
            self.logger.error(f"Error calculating metrics: {e}")
            return {'valid': False}

    async def _calculate_momentum(self, market_data: Dict) -> float:
        """Calculate momentum based on multiple indicators"""
        try:
            volume = float(market_data.get('volume_24h', 0))
            liquidity = float(market_data.get('liquidity', 0))
            rsi = float(market_data.get('indicators', {}).get('rsi', 50))
            macd = float(market_data.get('indicators', {}).get('macd', 0))

            # Normalize components
            volume_score = min(volume / (liquidity + 1), 1.0) if liquidity > 0 else 0
            rsi_score = (rsi - 30) / 40 if 30 <= rsi <= 70 else 0
            macd_score = 1 / (1 + np.exp(-10 * macd)) if macd else 0.5

            # Weighted average
            momentum = (
                0.4 * volume_score +
                0.3 * rsi_score +
                0.3 * macd_score
            )

            return max(0, min(1, momentum))

        except Exception as e:
            self.logger.error(f"Error calculating momentum: {e}")
            return 0.5

    async def _prepare_ml_features(self, market_data: Dict, sentiment_data: Dict,
                                token_metrics: Dict) -> Dict[str, float]:
        """Prepare features for ML model"""
        try:
            price = float(market_data.get('price', 0))
            volume = float(token_metrics.get('volume', 0))
            momentum = float(token_metrics.get('momentum', 0))
            rsi = float(market_data.get('indicators', {}).get('rsi', 50))
            macd = float(market_data.get('indicators', {}).get('macd', 0))

            return {
                'price': price,
                'volume': volume,
                'volatility': float(market_data.get('volatility', 0.1)),
                'rsi': rsi,
                'macd': macd,
                'sentiment_score': float(sentiment_data.get('score', 0.5)),
                'viral_score': float(sentiment_data.get('viral_coefficient', 0.5)),
                'holder_count': float(token_metrics.get('estimated_holders', 100)),
                'liquidity': float(token_metrics.get('liquidity', 10000)),
                'momentum': momentum,
                'confidence': min(
                    float(sentiment_data.get('confidence', 0.5)),
                    float(market_data.get('technical_confidence', 0.5))
                )
            }
        except Exception as e:
            self.logger.error(f"Error preparing ML features: {e}")
            return {}

    async def _calculate_entry_points(self, market_data: Dict, metrics: Dict,
                                  ml_confidence: float) -> List[Dict]:
        """Calculate entry points with ML confidence"""
        try:
            price = metrics['price']
            momentum = metrics['momentum']

            # Combine ML confidence with other metrics
            confidence = min(
                0.7 +
                (metrics['liquidity'] / 1000000) * 0.1 +
                momentum * 0.2 +
                ml_confidence * 0.3,  # Higher weight for ML prediction
                0.95  # Maximum cap
            )

            # Dynamic stop loss and take profit based on confidence
            stop_loss_margin = 0.05 + (1 - ml_confidence) * 0.05
            take_profit_margin = 0.2 + ml_confidence * 0.3

            return [{
                'price': price,
                'stop_loss': price * (1 - stop_loss_margin),
                'take_profit': price * (1 + take_profit_margin),
                'confidence': confidence
            }]

        except Exception as e:
            self.logger.error(f"Error calculating entry points: {e}")
            return []

    async def _create_signal(self, market_data: Dict, entry: Dict, ml_confidence: float) -> Dict:
        """Create trading signal with ML insights"""
        try:
            position_size = await self._calculate_position_size(entry['price'], ml_confidence)

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
            self.logger.error(f"Error creating signal: {e}")
            return {}

    async def _calculate_position_size(self, price: float, ml_confidence: float) -> float:
        """Calculate position size based on ML confidence"""
        try:
            # Increase position size based on ML confidence
            base_size = self.risk_per_trade * price
            confidence_multiplier = 1 + (ml_confidence - 0.5)
            position_size = base_size * confidence_multiplier

            # Apply position size limits
            max_position = min(
                self.config.get('max_position_size', float('inf')),
                price * self.config.get('max_tokens', float('inf'))
            )

            return min(position_size, max_position)

        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0.0

    async def validate_trade(self, signal: Dict[str, Any], portfolio: Dict[str, Any]) -> bool:
        """Validate trade with ML insights"""
        try:
            return (
                signal.get('confidence', 0) >= 0.7 and
                signal.get('ml_confidence', 0) >= self.min_prediction_confidence and
                signal.get('position_size', 0) > 0 and
                signal.get('position_size') <= portfolio.get('available_balance', 0) and
                signal.get('position_size') <= portfolio.get('total_balance', 0) * self.risk_per_trade
            )
        except Exception as e:
            self.logger.error(f"Error validating trade: {e}")
            return False

    async def execute_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trade with ML performance tracking and notifications"""
        try:
            result = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'entry_price': signal['entry_price'],
                'position_size': signal['position_size'],
                'symbol': signal['symbol'],
                'ml_confidence': signal.get('ml_confidence', 0)
            }

            # Add result to training set
            await self.learning_module.add_trade_result({
                **signal,
                'success': True,
                'price': signal['entry_price'],
                'volume': signal.get('volume', 0),
                'rsi': signal.get('rsi', 50),
                'macd': signal.get('macd', 0),
                'momentum': signal.get('momentum', 0.5),
                'volatility': signal.get('volatility', 0.1),
                'sentiment_score': signal.get('sentiment_score', 0.5),
                'viral_score': signal.get('viral_score', 0.5),
                'holder_count': signal.get('holder_count', 100),
                'liquidity': signal.get('liquidity', 10000),
                'confidence': signal.get('confidence', 0.5)
            })

            # Send trade notification
            trade_notification = {
                'type': 'trade',
                'action': 'BUY',
                'symbol': signal['symbol'],
                'price': signal['entry_price'],
                'quantity': signal['position_size'],
                'ml_confidence': signal['ml_confidence']
            }
            await self.notifier.send_notification(
                trade_notification,
                priority=NotificationPriority.HIGH,
                category=NotificationCategory.TRADE
            )

            return result

        except Exception as e:
            error_msg = f"Trade execution error: {str(e)}"
            self.logger.error(error_msg)

            # Send error notification
            error_notification = {
                'type': 'error',
                'symbol': signal['symbol'],
                'message': error_msg
            }
            await self.notifier.send_notification(
                error_notification,
                priority=NotificationPriority.CRITICAL,
                category=NotificationCategory.SYSTEM
            )

            return {'success': False, 'error': error_msg}