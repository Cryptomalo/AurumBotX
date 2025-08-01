import pandas as pd
import numpy as np
import logging
import asyncio
from typing import Dict, Any, List, Optional
from utils.strategies.base_strategy import BaseStrategy
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

class SwingTradingStrategy(BaseStrategy):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Swing Trading", config)
        self.trend_period = config.get('trend_period', 20)
        self.profit_target = config.get('profit_target', 0.15)
        self.stop_loss = config.get('stop_loss', 0.10)
        self.min_trend_strength = config.get('min_trend_strength', 0.6)

        # Initialize OpenAI client with fallback
        try:
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            self.has_sentiment = True
        except Exception as e:
            logger.error(f"OpenAI initialization failed: {str(e)}")
            self.has_sentiment = False

    async def analyze_market(
        self, 
        market_data: Dict[str, Any],
        sentiment_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Analyze market for swing trading opportunities"""
        try:
            if not market_data:
                logger.warning("No market data provided")
                return []

            # Convert market data to DataFrame if needed
            df = market_data if isinstance(market_data, pd.DataFrame) else pd.DataFrame(market_data)

            if df.empty:
                logger.warning("Empty market data")
                return []

            # Calculate technical indicators
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()

            # Calculate trend
            trend_direction = 1 if df['SMA_20'].iloc[-1] > df['SMA_50'].iloc[-1] else -1
            trend_strength = abs(df['SMA_20'].iloc[-1] - df['SMA_50'].iloc[-1]) / df['SMA_50'].iloc[-1]

            # Calculate volatility
            volatility = df['Close'].pct_change().rolling(window=self.trend_period).std().iloc[-1]

            # Volume analysis
            volume_trend = df['Volume'].rolling(window=self.trend_period).mean().iloc[-1]
            volume_ratio = df['Volume'].iloc[-1] / volume_trend

            # Sentiment analysis with fallback
            sentiment_score = await self._analyze_market_sentiment() if self.has_sentiment else await self._technical_sentiment(df)

            # Generate signals based on analysis
            signal = self._generate_signals({
                'trend_direction': trend_direction,
                'trend_strength': trend_strength,
                'volatility': volatility,
                'volume_ratio': volume_ratio,
                'sentiment_score': sentiment_score,
                'current_price': df['Close'].iloc[-1]
            })

            return [{
                **signal,
                'sma_20': df['SMA_20'].iloc[-1],
                'sma_50': df['SMA_50'].iloc[-1],
                'timestamp': pd.Timestamp.now().isoformat()
            }]

        except Exception as e:
            logger.error(f"Error in market analysis: {str(e)}")
            return []

    async def validate_trade(self, signal: Dict[str, Any], portfolio: Dict[str, Any]) -> bool:
        """Validate a potential swing trade"""
        try:
            if signal['action'] == 'hold':
                return False

            # Verify available capital
            required_capital = portfolio.get('available_capital', 0) * signal['size_factor']
            min_trade_size = 500  # Minimum size for swing trading

            if required_capital < min_trade_size:
                return False

            # Verify risk
            risk_amount = abs(signal['target_price'] - signal['stop_loss']) * required_capital
            max_risk = portfolio.get('total_capital', 0) * 0.05  # 5% max risk per trade

            # Verify market timing
            market_conditions_favorable = (
                signal['confidence'] > 0.8 and
                portfolio.get('market_trend', 0) * (
                    1 if signal['action'] == 'buy' else -1
                ) > 0
            )

            return risk_amount <= max_risk and market_conditions_favorable

        except Exception as e:
            logger.error(f"Error validating trade: {str(e)}")
            return False

    async def execute_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trade based on signal"""
        try:
            if signal['action'] == 'hold':
                return {'success': False, 'reason': 'No trade signal'}

            # Execute trade logic here
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

            return execution

        except Exception as e:
            logger.error(f"Trade execution error: {str(e)}")
            return {
                'success': False, 
                'error': str(e),
                'timestamp': pd.Timestamp.now().isoformat()
            }

    def _generate_signals(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signals"""
        signal = {
            'action': 'hold',
            'confidence': 0.0,
            'target_price': None,
            'stop_loss': None,
            'size_factor': 0.0
        }

        try:
            # Verify trend strength
            if analysis['trend_strength'] < self.min_trend_strength:
                return signal

            # Calculate overall score
            trend_score = min(1.0, analysis['trend_strength'])
            sentiment_score = analysis['sentiment_score']
            volume_score = min(1.0, analysis['volume_ratio'])

            total_score = (
                trend_score * 0.4 +
                sentiment_score * 0.3 +
                volume_score * 0.3
            )

            # Generate signal if score is sufficient
            if total_score > 0.7:
                current_price = analysis['current_price']

                if analysis['trend_direction'] > 0 and sentiment_score > 0.6:
                    signal.update({
                        'action': 'buy',
                        'confidence': total_score,
                        'target_price': current_price * (1 + self.profit_target),
                        'stop_loss': current_price * (1 - self.stop_loss),
                        'size_factor': total_score
                    })
                elif analysis['trend_direction'] < 0 and sentiment_score < 0.4:
                    signal.update({
                        'action': 'sell',
                        'confidence': total_score,
                        'target_price': current_price * (1 - self.profit_target),
                        'stop_loss': current_price * (1 + self.stop_loss),
                        'size_factor': total_score
                    })

            return signal

        except Exception as e:
            logger.error(f"Error generating signals: {str(e)}")
            return signal

    async def _analyze_market_sentiment(self) -> float:
        """Analyze market sentiment using OpenAI"""
        try:
            if not self.has_sentiment:
                return 0.5

            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4",
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

    async def _technical_sentiment(self, df: pd.DataFrame) -> float:
        """Calculate sentiment based on technical analysis when OpenAI is unavailable"""
        try:
            # Calculate long-term trend
            long_trend = (
                df['Close'].rolling(window=50).mean().diff().rolling(window=20).mean().iloc[-1]
            )

            # Volume trend
            volume_trend = (
                df['Volume'].rolling(window=50).mean().diff().rolling(window=20).mean().iloc[-1]
            )

            # RSI for momentum
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # Combine indicators for sentiment score
            trend_score = 0.5 + (np.sign(long_trend) * min(0.5, abs(float(long_trend))))
            volume_score = 0.5 + (np.sign(volume_trend) * min(0.5, abs(float(volume_trend))))
            rsi_score = float(rsi.iloc[-1]) / 100

            final_score = (trend_score * 0.4 + volume_score * 0.3 + rsi_score * 0.3)
            return max(0.0, min(1.0, float(final_score)))

        except Exception as e:
            logger.error(f"Error in technical sentiment: {str(e)}")
            return 0.5