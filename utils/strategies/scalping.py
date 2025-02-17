import pandas as pd
from typing import Dict, Any, List, Optional
import numpy as np
from utils.strategies.base_strategy import BaseStrategy
import logging
import asyncio

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
        self.logger = logger

    async def analyze_market(
        self, 
        market_data: pd.DataFrame, 
        sentiment_data: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Analisi di mercato ultra-rapida con rilevamento anomalie"""
        try:
            if market_data is None or market_data.empty:
                return []

            # Standardizzazione colonne
            volume = market_data.get('Volume', market_data.get('volume'))
            close = market_data.get('Close', market_data.get('close'))
            high = market_data.get('High', market_data.get('high'))
            low = market_data.get('Low', market_data.get('low'))

            # Analisi volume avanzata
            volume_sma = volume.rolling(window=5).mean()
            volume_std = volume.rolling(window=5).std()
            volume_ratio = volume.iloc[-1] / volume_sma.iloc[-1]
            volume_anomaly = (volume.iloc[-1] - volume_sma.iloc[-1]) / volume_std.iloc[-1]
            volume_trend = volume.pct_change(3).mean()

            # Analisi volatilità e momentum
            volatility = close.pct_change().rolling(window=5).std().iloc[-1] * np.sqrt(288)
            momentum = close.pct_change(periods=3).iloc[-1]
            price_trend = close.pct_change(3).ewm(span=3).mean().iloc[-1]

            current_price = close.iloc[-1]

            # Calcolo livelli dinamici
            recent_high = high.rolling(window=12).max().iloc[-1]
            recent_low = low.rolling(window=12).min().iloc[-1]
            price_range = recent_high - recent_low

            # Take profit adattivo
            adaptive_profit_target = max(self.profit_target, volatility * 0.5)
            adaptive_stop_loss = min(self.initial_stop_loss, volatility * 0.3)

            # Integrazione sentiment
            sentiment_score = sentiment_data.get('sentiment_score', 0.5) if sentiment_data else 0.5

            analysis = [{
                'volume_24h': volume.iloc[-1],
                'volume_ratio': volume_ratio,
                'volume_trend': volume_trend,
                'volume_anomaly': volume_anomaly,
                'volatility': volatility,
                'momentum': momentum,
                'price_trend': price_trend,
                'current_price': current_price,
                'nearest_resistance': recent_high,
                'nearest_support': recent_low,
                'price_range': price_range,
                'adaptive_profit': adaptive_profit_target,
                'adaptive_stop': adaptive_stop_loss,
                'sentiment_score': sentiment_score
            }]

            return analysis

        except Exception as e:
            self.logger.error(f"Market analysis error: {str(e)}")
            return []

    def generate_signals(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generazione segnali ultra-veloce con conferme multiple"""
        try:
            signal = {
                'action': 'hold',
                'confidence': 0.0,
                'target_price': None,
                'stop_loss': None,
                'size_factor': 0.0
            }

            # Analisi volume anomalo
            volume_spike = analysis.get('volume_anomaly', 0) > 2.0
            volume_trend_positive = analysis.get('volume_trend', 0) > 0

            # Check volatilità e momentum
            volatility_ok = analysis.get('volatility', 0) > self.min_volatility * 0.7
            strong_momentum = abs(analysis.get('momentum', 0)) > self.min_volatility

            # Calcolo score trend con pesi
            trend_factors = [
                (1 if analysis.get('price_trend', 0) > 0 else -1) * 2.0,  # Maggior peso al trend
                (1 if analysis.get('momentum', 0) > 0 else -1) * 1.5,
                (1 if analysis.get('volume_trend', 0) > 0 else -1),
                (1 if analysis.get('sentiment_score', 0.5) > 0.6 else -1) * 1.2  # Integrazione sentiment
            ]

            trend_score = sum(trend_factors) / 5.7  # Normalizzato tra -1 e 1

            # Calcolo forza segnale con più indicatori
            signal_strength = min(1.0, (
                (analysis.get('volume_ratio', 1) - 1) * 0.15 +
                (analysis.get('volatility', 0) / self.min_volatility) * 0.15 +
                abs(analysis.get('momentum', 0)) * 0.2 +
                analysis.get('sentiment_score', 0.5) * 0.2
            ))

            # Generazione segnali con condizioni ottimizzate
            if (volume_spike or (volatility_ok and volume_trend_positive)) and strong_momentum:
                current_price = analysis.get('current_price', 0)
                adaptive_profit = analysis.get('adaptive_profit', self.profit_target)
                adaptive_stop = analysis.get('adaptive_stop', self.initial_stop_loss)

                # Determina azione basata su score trend
                if trend_score > 0.3:  # Soglia ridotta per più segnali
                    action = 'buy'
                    target_price = current_price * (1 + adaptive_profit)
                    stop_loss = current_price * (1 - adaptive_stop)
                elif trend_score < -0.3:
                    action = 'sell'
                    target_price = current_price * (1 - adaptive_profit)
                    stop_loss = current_price * (1 + adaptive_stop)
                else:
                    return signal

                # Verifica rapporto rischio/rendimento
                risk = abs(current_price - stop_loss)
                reward = abs(current_price - target_price)
                if reward / risk >= self.min_profit_factor:
                    signal.update({
                        'action': action,
                        'confidence': signal_strength,
                        'target_price': target_price,
                        'stop_loss': stop_loss,
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
        """Validates a potential scalping trade"""
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
            current_spread = portfolio.get('current_spread', 0.001)
            min_profit_after_fees = self.profit_target * 2

            return risk_per_trade <= max_risk and current_spread < min_profit_after_fees

        except Exception as e:
            self.logger.error(f"Trade validation error: {str(e)}")
            return False

    async def execute_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a scalping trade based on the signal"""
        try:
            if signal['action'] == 'hold':
                return {'success': False, 'reason': 'No trade signal'}

            # Simulate trade execution for testnet
            execution = {
                'success': True,
                'action': signal['action'],
                'price': signal.get('current_price', 0),
                'timestamp': pd.Timestamp.now().isoformat(),
                'size_factor': signal.get('size_factor', 0.0),
                'target_price': signal.get('target_price'),
                'stop_loss': signal.get('stop_loss'),
                'confidence': signal.get('confidence', 0.0)
            }

            # Update performance metrics
            self.update_performance(execution)

            return execution

        except Exception as e:
            self.logger.error(f"Trade execution error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': pd.Timestamp.now().isoformat()
            }