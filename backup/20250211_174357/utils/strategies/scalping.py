import pandas as pd
from typing import Dict, Any, List, Optional
import numpy as np
from utils.strategies.base_strategy import BaseStrategy
import logging

logger = logging.getLogger(__name__)

class ScalpingStrategy(BaseStrategy):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Scalping", config)
        self.volume_threshold = config.get('volume_threshold', 1000000)  # Volume minimo 24h
        self.min_volatility = config.get('min_volatility', 0.002)  # 0.2% volatilità minima
        self.profit_target = config.get('profit_target', 0.005)  # 0.5% target di profitto
        self.initial_stop_loss = config.get('initial_stop_loss', 0.003)  # 0.3% stop loss iniziale
        self.trailing_stop = config.get('trailing_stop', 0.002)  # 0.2% trailing stop

    async def analyze_market(
        self,
        market_data: pd.DataFrame,
        sentiment_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Analizza il mercato per opportunità di scalping
        """
        try:
            if market_data is None or market_data.empty:
                return []

            # Calcola metriche di volume
            volume_sma = market_data['Volume'].rolling(window=24).mean()
            volume_ratio = float(market_data['Volume'].iloc[-1] / volume_sma.iloc[-1])

            # Calcola volatilità
            volatility = float(market_data['Close'].pct_change().rolling(window=12).std().iloc[-1])

            # Calcola momentum
            momentum = float(market_data['Close'].pct_change(periods=12).iloc[-1])

            # Identifica supporti e resistenze
            recent_highs = market_data['High'].rolling(window=24).max()
            recent_lows = market_data['Low'].rolling(window=24).min()

            analysis = {
                'volume_24h': float(market_data['Volume'].iloc[-1]),
                'volume_ratio': volume_ratio,
                'volatility': volatility,
                'momentum': momentum,
                'current_price': float(market_data['Close'].iloc[-1]),
                'nearest_resistance': float(recent_highs.iloc[-1]),
                'nearest_support': float(recent_lows.iloc[-1]),
                'high_volume': market_data['Volume'].iloc[-1] > self.volume_threshold,
                'price_change_1h': float(market_data['Close'].pct_change(periods=6).iloc[-1])
            }

            signal = await self.generate_signals(analysis)
            return [signal] if signal['action'] != 'hold' else []

        except Exception as e:
            logger.error(f"Error in market analysis: {str(e)}")
            return []

    async def generate_signals(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera segnali di trading per scalping
        """
        signal = {
            'action': 'hold',
            'confidence': 0.0,
            'target_price': None,
            'stop_loss': None,
            'size_factor': 0.0
        }

        # Verifica condizioni per scalping
        if not analysis['high_volume'] or analysis['volatility'] < self.min_volatility:
            return signal

        # Calcola la direzione del trend
        trend_direction = 1 if analysis['momentum'] > 0 else -1

        # Calcola la forza del segnale
        signal_strength = min(1.0, float(
            (analysis['volume_ratio'] - 1) * 0.3 +
            (analysis['volatility'] / self.min_volatility) * 0.3 +
            abs(analysis['momentum']) * 0.4
        ))

        # Genera segnali solo se abbiamo una forza sufficiente
        if signal_strength > 0.7:
            current_price = analysis['current_price']

            signal.update({
                'action': 'buy' if trend_direction > 0 else 'sell',
                'confidence': signal_strength,
                'target_price': current_price * (1 + trend_direction * self.profit_target),
                'stop_loss': current_price * (1 - trend_direction * self.initial_stop_loss),
                'trailing_stop': self.trailing_stop,
                'size_factor': signal_strength
            })

        return signal

    async def validate_trade(self, signal: Dict[str, Any], portfolio: Dict[str, Any]) -> bool:
        """
        Valida un potenziale trade di scalping
        """
        try:
            if signal['action'] == 'hold':
                return False

            # Verifica il capitale disponibile
            required_capital = portfolio.get('available_capital', 0) * signal['size_factor']
            min_trade_size = 50  # Dimensione minima trade

            if required_capital < min_trade_size:
                return False

            # Calcola il rischio potenziale
            risk_per_trade = abs(signal['target_price'] - signal['stop_loss']) * required_capital
            max_risk = portfolio.get('total_capital', 0) * 0.01  # 1% rischio massimo per trade

            # Verifica spread
            current_spread = portfolio.get('current_spread', 0.001)  # 0.1% spread di default
            min_profit_after_fees = self.profit_target * 2  # Il profitto deve essere almeno 2x lo spread

            return risk_per_trade <= max_risk and current_spread < min_profit_after_fees

        except Exception as e:
            logger.error(f"Error validating trade: {str(e)}")
            return False

    async def execute_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Esegue un trade basato sul segnale
        """
        try:
            if signal['action'] == 'hold':
                return {'success': False, 'reason': 'No valid signal'}

            return {
                'success': True,
                'action': signal['action'],
                'price': signal.get('current_price', 0),
                'size_factor': signal.get('size_factor', 0),
                'target_price': signal.get('target_price'),
                'stop_loss': signal.get('stop_loss'),
                'trailing_stop': signal.get('trailing_stop'),
                'timestamp': pd.Timestamp.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': pd.Timestamp.now().isoformat()
            }