import pandas as pd
from typing import Dict, Any
import numpy as np
from utils.strategies.base_strategy import BaseStrategy
from openai import OpenAI
import os
import logging

logger = logging.getLogger(__name__)

class SwingTradingStrategy(BaseStrategy):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Swing Trading", config)
        self.trend_period = config.get('trend_period', 20)
        self.profit_target = config.get('profit_target', 0.15)
        self.stop_loss = config.get('stop_loss', 0.10)
        self.min_trend_strength = config.get('min_trend_strength', 0.6)
        self.max_position_size = config.get('max_position_size', 0.2)  # 20% del portfolio
        self.risk_per_trade = config.get('risk_per_trade', 0.02)  # 2% risk per trade

        # Parametri tecnici avanzati
        self.rsi_period = config.get('rsi_period', 14)
        self.volume_ma_period = config.get('volume_ma_period', 20)
        self.atr_period = config.get('atr_period', 14)

        # Initialize OpenAI client with fallback
        try:
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            self.has_sentiment = True
        except Exception as e:
            logger.warning(f"OpenAI initialization failed: {str(e)}")
            self.has_sentiment = False

    def analyze_market(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analizza il mercato per swing trading con indicatori avanzati"""
        try:
            # Calcola indicatori tecnici base
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['EMA_21'] = df['Close'].ewm(span=21).mean()

            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # ATR per volatilità
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            df['ATR'] = true_range.rolling(window=self.atr_period).mean()

            # Volume analysis
            df['Volume_MA'] = df['Volume'].rolling(window=self.volume_ma_period).mean()
            volume_trend = df['Volume'].rolling(window=self.trend_period).mean().iloc[-1]
            volume_ratio = df['Volume'].iloc[-1] / volume_trend

            # Trend analysis
            trend_direction = 1 if df['SMA_20'].iloc[-1] > df['SMA_50'].iloc[-1] else -1
            trend_strength = abs(df['SMA_20'].iloc[-1] - df['SMA_50'].iloc[-1]) / df['SMA_50'].iloc[-1]

            # Momentum indicators
            df['MACD'] = df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()
            df['Signal'] = df['MACD'].ewm(span=9).mean()

            # Support and Resistance
            resistance = df['High'].rolling(window=20).max().iloc[-1]
            support = df['Low'].rolling(window=20).min().iloc[-1]

            analysis = {
                'trend_direction': trend_direction,
                'trend_strength': trend_strength,
                'volume_ratio': volume_ratio,
                'rsi': df['RSI'].iloc[-1],
                'atr': df['ATR'].iloc[-1],
                'macd': df['MACD'].iloc[-1],
                'macd_signal': df['Signal'].iloc[-1],
                'current_price': df['Close'].iloc[-1],
                'resistance': resistance,
                'support': support,
                'volatility': df['ATR'].iloc[-1] / df['Close'].iloc[-1]
            }

            # Aggiungi sentiment se disponibile
            if self.has_sentiment:
                sentiment_score = self._analyze_market_sentiment()
                analysis['sentiment_score'] = sentiment_score
            else:
                analysis['sentiment_score'] = self._technical_sentiment(df)

            return analysis

        except Exception as e:
            logger.error(f"Error in market analysis: {str(e)}")
            return {}

    def generate_signals(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Genera segnali di trading con criteri multipli"""
        signal = {
            'action': 'hold',
            'confidence': 0.0,
            'target_price': None,
            'stop_loss': None,
            'size_factor': 0.0
        }

        try:
            if not analysis:
                return signal

            # Score calculation
            trend_score = min(1.0, analysis['trend_strength'])
            rsi_score = self._calculate_rsi_score(analysis['rsi'])
            volume_score = min(1.0, analysis['volume_ratio'])
            macd_score = self._calculate_macd_score(analysis)

            # Weighted score calculation
            total_score = (
                trend_score * 0.3 +
                rsi_score * 0.2 +
                volume_score * 0.2 +
                macd_score * 0.2 +
                analysis['sentiment_score'] * 0.1
            )

            # Dynamic thresholds based on market conditions
            confidence_threshold = 0.7 * (1 + analysis['volatility'])

            if total_score > confidence_threshold:
                current_price = analysis['current_price']
                volatility_factor = analysis['volatility']

                # Dynamic targets based on volatility
                profit_target = self.profit_target * (1 + volatility_factor)
                stop_loss_level = self.stop_loss * (1 + volatility_factor * 0.5)

                # Position sizing based on risk
                size_factor = self._calculate_position_size(
                    current_price,
                    stop_loss_level,
                    total_score
                )

                action = 'buy' if analysis['trend_direction'] > 0 else 'sell'

                signal.update({
                    'action': action,
                    'confidence': total_score,
                    'target_price': current_price * (1 + (profit_target * analysis['trend_direction'])),
                    'stop_loss': current_price * (1 - (stop_loss_level * analysis['trend_direction'])),
                    'size_factor': size_factor
                })

            return signal

        except Exception as e:
            logger.error(f"Error generating signals: {str(e)}")
            return signal

    def _calculate_position_size(self, price: float, stop_loss_pct: float, confidence: float) -> float:
        """Calcola dimensione posizione basata su risk management avanzato"""
        try:
            # Calcola rischio monetario per trade
            account_risk = self.risk_per_trade

            # Ajusta per confidence
            risk_adjusted = account_risk * confidence

            # Calcola size basata su stop loss
            position_size = risk_adjusted / stop_loss_pct

            # Applica limiti di posizione
            return min(position_size, self.max_position_size)

        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0.0

    def _calculate_rsi_score(self, rsi: float) -> float:
        """Calcola score RSI normalizzato"""
        if rsi > 70:
            return 0.2  # Overbought
        elif rsi < 30:
            return 0.8  # Oversold
        else:
            return 0.5  # Neutral

    def _calculate_macd_score(self, analysis: Dict[str, Any]) -> float:
        """Calcola score MACD"""
        try:
            macd = analysis['macd']
            signal = analysis['macd_signal']

            if macd > signal and macd > 0:
                return 0.8  # Strong buy
            elif macd > signal:
                return 0.6  # Buy
            elif macd < signal and macd < 0:
                return 0.2  # Strong sell
            elif macd < signal:
                return 0.4  # Sell

            return 0.5

        except Exception as e:
            logger.error(f"Error calculating MACD score: {str(e)}")
            return 0.5

    def validate_trade(self, signal: Dict[str, Any], portfolio: Dict[str, Any]) -> bool:
        """Valida il trade con criteri multipli"""
        try:
            if signal['action'] == 'hold':
                return False

            # Verifica capitale disponibile
            required_capital = portfolio.get('available_capital', 0) * signal['size_factor']
            if required_capital < portfolio.get('min_trade_size', 100):
                logger.info("Trade rejected: Insufficient capital")
                return False

            # Verifica rischio massimo
            max_risk = portfolio.get('total_capital', 0) * self.risk_per_trade
            potential_loss = abs(signal['target_price'] - signal['stop_loss']) * required_capital
            if potential_loss > max_risk:
                logger.info("Trade rejected: Risk too high")
                return False

            # Verifica spread
            current_spread = portfolio.get('current_spread', 0.001)
            min_profit = abs(signal['target_price'] - signal['stop_loss']) * 2
            if current_spread > min_profit:
                logger.info("Trade rejected: Spread too high")
                return False

            return True

        except Exception as e:
            logger.error(f"Error in trade validation: {str(e)}")
            return False

    def _technical_sentiment(self, df: pd.DataFrame) -> float:
        """Calcola sentiment basato su analisi tecnica quando OpenAI non è disponibile"""
        try:
            # Calcola trend di lungo periodo
            long_trend = (
                df['Close'].rolling(window=50).mean().diff().rolling(window=20).mean().iloc[-1]
            )

            # Volume trend
            volume_trend = (
                df['Volume'].rolling(window=50).mean().diff().rolling(window=20).mean().iloc[-1]
            )

            # RSI per momentum
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # Combina indicatori per sentiment score
            trend_score = 0.5 + (np.sign(long_trend) * min(0.5, abs(long_trend)))
            volume_score = 0.5 + (np.sign(volume_trend) * min(0.5, abs(volume_trend)))
            rsi_score = rsi.iloc[-1] / 100

            final_score = (trend_score * 0.4 + volume_score * 0.3 + rsi_score * 0.3)
            return max(0, min(1, final_score))

        except Exception as e:
            logger.error(f"Error in technical sentiment calculation: {str(e)}")
            return 0.5

    def _analyze_market_sentiment(self) -> float:
        """Analizza il sentiment del mercato usando OpenAI"""
        try:
            if not self.has_sentiment:
                return 0.5

            response = self.client.chat.completions.create(
                model="gpt-4",  # Latest stable model
                messages=[{
                    "role": "system",
                    "content": "Analyze the current market sentiment for long-term crypto trading and provide a sentiment score between 0 and 1."
                }],
                response_format={"type": "json_object"}
            )
            result = response.choices[0].message.content
            return float(result.get('sentiment_score', 0.5))
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return 0.5