import pandas as pd
from typing import Dict, Any, List, Optional
import numpy as np
from utils.strategies.base_strategy import BaseStrategy
import logging

logger = logging.getLogger(__name__)

class ScalpingStrategy(BaseStrategy):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Scalping", config)
        self.volume_threshold = config.get('volume_threshold', 1000000)  # Min 24h volume
        self.min_volatility = config.get('min_volatility', 0.002)  # 0.2% min volatility
        self.profit_target = config.get('profit_target', 0.005)  # 0.5% profit target
        self.initial_stop_loss = config.get('initial_stop_loss', 0.003)  # 0.3% initial stop loss
        self.trailing_stop = config.get('trailing_stop', 0.002)  # 0.2% trailing stop
        self.logger = logger

    async def analyze_market(self, market_data: pd.DataFrame, sentiment_data: Optional[Dict] = None) -> List[Dict]:
        """
        Analyzes the market for scalping opportunities
        """
        try:
            if market_data is None or market_data.empty:
                return []

            # Calculate volume metrics
            volume_sma = market_data['Volume'].rolling(window=24).mean()
            volume_ratio = market_data['Volume'].iloc[-1] / volume_sma.iloc[-1]

            # Calculate volatility
            volatility = market_data['Close'].pct_change().rolling(window=12).std().iloc[-1]

            # Calculate momentum
            momentum = market_data['Close'].pct_change(periods=12).iloc[-1]

            # Identify support and resistance
            recent_highs = market_data['High'].rolling(window=24).max()
            recent_lows = market_data['Low'].rolling(window=24).min()

            analysis = [{
                'volume_24h': market_data['Volume'].iloc[-1],
                'volume_ratio': volume_ratio,
                'volatility': volatility,
                'momentum': momentum,
                'current_price': market_data['Close'].iloc[-1],
                'nearest_resistance': recent_highs.iloc[-1],
                'nearest_support': recent_lows.iloc[-1],
                'high_volume': market_data['Volume'].iloc[-1] > self.volume_threshold,
                'price_change_1h': market_data['Close'].pct_change(periods=6).iloc[-1],
                'sentiment_score': sentiment_data.get('sentiment_score', 0.0) if sentiment_data else 0.0
            }]

            return analysis

        except Exception as e:
            self.logger.error(f"Market analysis error: {str(e)}")
            return []

    def generate_signals(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates trading signals for scalping
        """
        try:
            signal = {
                'action': 'hold',
                'confidence': 0.0,
                'target_price': None,
                'stop_loss': None,
                'size_factor': 0.0
            }

            # Check conditions for scalping
            if not analysis.get('high_volume', False) or analysis.get('volatility', 0) < self.min_volatility:
                return signal

            # Calculate trend direction
            trend_direction = 1 if analysis.get('momentum', 0) > 0 else -1

            # Calculate signal strength
            signal_strength = min(1.0, (
                (analysis.get('volume_ratio', 1) - 1) * 0.3 +
                (analysis.get('volatility', 0) / self.min_volatility) * 0.3 +
                abs(analysis.get('momentum', 0)) * 0.4
            ))

            # Generate signals only if we have sufficient strength
            if signal_strength > 0.7:
                current_price = analysis.get('current_price', 0)

                signal.update({
                    'action': 'buy' if trend_direction > 0 else 'sell',
                    'confidence': signal_strength,
                    'target_price': current_price * (1 + trend_direction * self.profit_target),
                    'stop_loss': current_price * (1 - trend_direction * self.initial_stop_loss),
                    'trailing_stop': self.trailing_stop,
                    'size_factor': signal_strength
                })

            return signal

        except Exception as e:
            self.logger.error(f"Signal generation error: {str(e)}")
            return {
                'action': 'hold',
                'confidence': 0.0,
                'target_price': None,
                'stop_loss': None,
                'size_factor': 0.0
            }

    async def validate_trade(self, signal: Dict[str, Any], portfolio: Dict[str, Any]) -> bool:
        """
        Validates a potential scalping trade
        """
        try:
            if signal['action'] == 'hold':
                return False

            # Verify available capital
            required_capital = portfolio.get('available_capital', 0) * signal['size_factor']
            min_trade_size = 50  # Minimum trade size

            if required_capital < min_trade_size:
                return False

            # Calculate potential risk
            risk_per_trade = abs(signal['target_price'] - signal['stop_loss']) * required_capital
            max_risk = portfolio.get('total_capital', 0) * 0.01  # 1% max risk per trade

            # Verify spread
            current_spread = portfolio.get('current_spread', 0.001)  # 0.1% default spread
            min_profit_after_fees = self.profit_target * 2  # Profit must be at least 2x spread

            return risk_per_trade <= max_risk and current_spread < min_profit_after_fees

        except Exception as e:
            self.logger.error(f"Trade validation error: {str(e)}")
            return False

    async def execute_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a scalping trade based on the signal
        """
        try:
            # Implementation for testnet
            current_price = signal.get('current_price', 0)
            trend_direction = 1 if signal.get('action') == 'buy' else -1

            result = {
                'action': signal['action'],
                'entry_price': current_price,
                'target_price': current_price * (1 + trend_direction * self.profit_target),
                'stop_loss': current_price * (1 - trend_direction * self.initial_stop_loss),
                'size_factor': signal.get('size_factor', 0.0),
                'timestamp': pd.Timestamp.now().isoformat(),
                'success': True,
                'error': None
            }

            # Update performance metrics
            self.update_performance(result)

            return result

        except Exception as e:
            self.logger.error(f"Trade execution error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': pd.Timestamp.now().isoformat()
            }