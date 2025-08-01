import pandas as pd
from typing import Dict, Any, List, Optional
import numpy as np
from utils.strategies.base_strategy import BaseStrategy
import logging
import asyncio
from cachetools import TTLCache
from datetime import datetime

logger = logging.getLogger(__name__)

class ScalpingStrategy(BaseStrategy):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Scalping", config)
        # Parametri ottimizzati per scalping ultra-veloce
        self.volume_threshold = config.get('volume_threshold', 300000)
        self.min_volatility = config.get('min_volatility', 0.0008)
        self.profit_target = config.get('profit_target', 0.002)
        self.initial_stop_loss = config.get('initial_stop_loss', 0.0015)
        self.trailing_stop = config.get('trailing_stop', 0.0008)
        self.rsi_oversold = config.get('rsi_oversold', 35)
        self.rsi_overbought = config.get('rsi_overbought', 65)
        self.volume_anomaly_threshold = 2.0
        self.min_profit_factor = 1.5
        self.max_position_size = config.get('max_position_size', 0.2)  # 20% del portfolio
        self.risk_per_trade = config.get('risk_per_trade', 0.02)  # 2% risk per trade

        # Cache configuration
        self._indicator_cache = TTLCache(maxsize=100, ttl=60)  # 1 minute cache
        self._analysis_cache = TTLCache(maxsize=50, ttl=30)    # 30 seconds cache

    async def analyze_market(
        self,
        market_data: Dict[str, Any],
        sentiment_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Analisi di mercato ultra-rapida con rilevamento anomalie e caching"""
        try:
            if not market_data:
                logger.warning("Dati di mercato mancanti")
                return []

            # Convert market data to DataFrame if needed
            if isinstance(market_data, dict):
                df = pd.DataFrame([market_data])
            elif isinstance(market_data, pd.DataFrame):
                df = market_data
            else:
                logger.error("Formato dati di mercato non valido")
                return []

            if df.empty:
                return []

            # Check cache first
            cache_key = f"{df.index[-1]}"
            cached_analysis = self._analysis_cache.get(cache_key)
            if cached_analysis:
                return cached_analysis

            # Calculate technical indicators
            indicators = await self._calculate_indicators(df)
            if not indicators:
                return []

            current_price = float(df['Close'].iloc[-1])

            analysis = [{
                'volume_24h': float(df['Volume'].iloc[-1]),
                'volume_ratio': indicators['volume_ratio'],
                'volume_trend': indicators['volume_trend'],
                'volume_anomaly': indicators['volume_anomaly'],
                'volatility': indicators['volatility'],
                'momentum': indicators['momentum'],
                'price_trend': indicators['price_trend'],
                'current_price': current_price,
                'nearest_resistance': indicators['recent_high'],
                'nearest_support': indicators['recent_low'],
                'price_range': indicators['price_range'],
                'adaptive_profit': max(self.profit_target, indicators['volatility'] * 0.5),
                'adaptive_stop': min(self.initial_stop_loss, indicators['volatility'] * 0.3),
                'sentiment_score': sentiment_data.get('sentiment_score', 0.5) if sentiment_data else 0.5
            }]

            # Cache the results
            self._analysis_cache[cache_key] = analysis
            return analysis

        except Exception as e:
            logger.error(f"Market analysis error: {str(e)}")
            return []

    async def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calcolo ottimizzato degli indicatori tecnici con caching"""
        try:
            cache_key = f"{df.index[-1]}"
            cached_indicators = self._indicator_cache.get(cache_key)
            if cached_indicators:
                return cached_indicators

            volume = df['Volume']
            close = df['Close']
            high = df['High']
            low = df['Low']

            # Calculate indicators
            volume_sma = volume.rolling(window=5).mean()
            volume_std = volume.rolling(window=5).std()

            indicators = {
                'volume_ratio': float(volume.iloc[-1] / volume_sma.iloc[-1]),
                'volume_anomaly': float((volume.iloc[-1] - volume_sma.iloc[-1]) / volume_std.iloc[-1]),
                'volume_trend': float(volume.pct_change(3).mean()),
                'volatility': float(close.pct_change().rolling(window=5).std().iloc[-1] * np.sqrt(288)),
                'momentum': float(close.pct_change(periods=3).iloc[-1]),
                'price_trend': float(close.pct_change(3).ewm(span=3).mean().iloc[-1]),
                'recent_high': float(high.rolling(window=12).max().iloc[-1]),
                'recent_low': float(low.rolling(window=12).min().iloc[-1])
            }

            indicators['price_range'] = indicators['recent_high'] - indicators['recent_low']

            # Cache the results
            self._indicator_cache[cache_key] = indicators
            return indicators

        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            return {}

    def generate_signals(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generazione segnali ultra-veloce con validazione migliorata"""
        try:
            if not analysis:
                return self._get_default_signal()

            # Validazione input
            required_fields = ['volume_anomaly', 'volatility', 'momentum', 'current_price']
            if not all(field in analysis for field in required_fields):
                self.logger.warning("Missing required fields in analysis")
                return self._get_default_signal()

            # Score calculation with weights
            weights = {
                'volume': 0.3,
                'volatility': 0.2,
                'momentum': 0.25,
                'sentiment': 0.25
            }

            scores = {
                'volume': min(1.0, analysis['volume_ratio'] if analysis.get('volume_ratio', 0) > 0 else 0),
                'volatility': min(1.0, analysis['volatility'] / self.min_volatility if analysis['volatility'] > 0 else 0),
                'momentum': min(1.0, abs(analysis['momentum']) * 2),
                'sentiment': analysis.get('sentiment_score', 0.5)
            }

            signal_strength = sum(score * weights[key] for key, score in scores.items())

            if signal_strength > 0.6:  # Threshold for signal generation
                return self._generate_trade_signal(analysis, signal_strength)

            return self._get_default_signal()

        except Exception as e:
            self.logger.error(f"Signal generation error: {str(e)}")
            return self._get_default_signal()

    def _generate_trade_signal(self, analysis: Dict[str, Any], strength: float) -> Dict[str, Any]:
        """Generate optimized trade signal"""
        current_price = analysis['current_price']
        adaptive_profit = analysis['adaptive_profit']
        adaptive_stop = analysis['adaptive_stop']

        # Determine trade direction
        if analysis['momentum'] > 0:
            action = 'buy'
            target_price = current_price * (1 + adaptive_profit)
            stop_loss = current_price * (1 - adaptive_stop)
        else:
            action = 'sell'
            target_price = current_price * (1 - adaptive_profit)
            stop_loss = current_price * (1 + adaptive_stop)

        # Calculate position size based on risk and confidence
        position_size = min(
            strength * self.max_position_size,  # Scale by signal strength
            self.risk_per_trade / (adaptive_stop)  # Limit by risk
        )

        return {
            'action': action,
            'confidence': strength,
            'target_price': target_price,
            'stop_loss': stop_loss,
            'trailing_stop': self.trailing_stop,
            'size_factor': position_size  # Now properly calculated
        }

    def _get_default_signal(self) -> Dict[str, Any]:
        """Return default hold signal"""
        return {
            'action': 'hold',
            'confidence': 0.0,
            'target_price': None,
            'stop_loss': None,
            'size_factor': 0.0
        }

    async def validate_trade(self, signal: Dict[str, Any], portfolio: Dict[str, Any]) -> bool:
        """Validates a potential scalping trade with enhanced risk management"""
        try:
            if signal.get('action') == 'hold':
                return False

            # Input validation
            required_fields = ['action', 'confidence', 'target_price', 'stop_loss', 'size_factor']
            if not all(field in signal for field in required_fields):
                logger.warning("Invalid signal format")
                return False

            # Portfolio validation
            required_capital = portfolio.get('available_capital', 0) * signal['size_factor']
            min_trade_size = portfolio.get('min_trade_size', 50)

            if required_capital < min_trade_size:
                logger.info(f"Insufficient capital for minimum trade size: {min_trade_size}")
                return False

            # Risk management
            risk_per_trade = abs(signal['target_price'] - signal['stop_loss']) * required_capital
            max_risk = portfolio.get('total_capital', 0) * self.risk_per_trade

            # Market condition validation
            current_spread = portfolio.get('current_spread', 0.001)
            min_profit_after_fees = self.profit_target * 2

            if risk_per_trade > max_risk:
                logger.info(f"Trade risk {risk_per_trade} exceeds maximum allowed {max_risk}")
                return False

            if current_spread >= min_profit_after_fees:
                logger.info(f"Spread {current_spread} too high compared to target profit {min_profit_after_fees}")
                return False

            return True

        except Exception as e:
            logger.error(f"Trade validation error: {str(e)}")
            return False

    async def _calculate_position_size(self, price: float, confidence: float) -> float:
        """Calculate position size based on price and confidence"""
        try:
            base_size = self.risk_per_trade * price
            confidence_factor = 0.5 + (confidence * 0.5)  # Scale between 50-100% based on confidence
            adjusted_size = base_size * confidence_factor

            # Apply maximum position limit
            return min(adjusted_size, self.max_position_size * price)

        except Exception as e:
            logger.error(f"Position size calculation error: {str(e)}")
            return 0.0

    async def execute_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a scalping trade with performance tracking"""
        try:
            if signal.get('action') == 'hold':
                return {'success': False, 'reason': 'No trade signal'}

            execution = {
                'success': True,
                'action': signal['action'],
                'price': signal.get('current_price', 0),
                'timestamp': datetime.now().isoformat(),
                'size_factor': signal.get('size_factor', 0.0),
                'target_price': signal.get('target_price'),
                'stop_loss': signal.get('stop_loss'),
                'confidence': signal.get('confidence', 0.0)
            }

            # Update performance metrics
            await self.update_performance(execution)
            return execution

        except Exception as e:
            logger.error(f"Trade execution error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }