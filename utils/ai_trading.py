import logging
import asyncio
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
from utils.prediction_model import PredictionModel
from utils.data_loader import CryptoDataLoader
from utils.sentiment_analyzer import SentimentAnalyzer
from utils.strategies.strategy_manager import StrategyManager

logger = logging.getLogger(__name__)

class AITradingSystem:
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize AI Trading System with configuration"""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.prediction_model = PredictionModel()
        self.data_loader = CryptoDataLoader()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.strategy_manager = StrategyManager()
        self.last_analysis = None
        self.min_confidence = 0.7

    async def analyze_market(self, symbol: str) -> Dict[str, Any]:
        """Analyze market conditions using multiple data sources"""
        try:
            # Get market data
            market_data = await self.data_loader.get_historical_data_async(symbol)
            if market_data is None or market_data.empty:
                self.logger.warning(f"No market data available for {symbol}")
                return {}

            # Get sentiment data
            sentiment_data = await self.sentiment_analyzer.analyze_sentiment(symbol)

            # Perform technical analysis
            technical_analysis = await self._analyze_technical_indicators(market_data)

            # Combine analyses
            analysis = {
                'market_data': technical_analysis,
                'sentiment': sentiment_data,
                'timestamp': datetime.now().isoformat()
            }

            return analysis

        except Exception as e:
            self.logger.error(f"Error in market analysis: {str(e)}")
            return {}

    async def generate_trading_signals(self, symbol: str) -> List[Dict[str, Any]]:
        """Generate trading signals using AI analysis"""
        try:
            analysis = await self.analyze_market(symbol)
            if not analysis:
                return []

            # Get AI predictions
            predictions = self.prediction_model.predict(analysis['market_data'])

            # Generate signals based on predictions and analysis
            signals = []

            if predictions['confidence'] >= self.min_confidence:
                signal = {
                    'symbol': symbol,
                    'action': 'buy' if predictions['prediction'] > 0.5 else 'sell',
                    'confidence': predictions['confidence'],
                    'price': analysis['market_data'].get('close', 0),
                    'timestamp': datetime.now().isoformat(),
                    'analysis': {
                        'technical_score': predictions['prediction'],
                        'sentiment_score': analysis['sentiment'].get('score', 0.5),
                        'risk_score': self._calculate_risk_score(analysis)
                    }
                }
                signals.append(signal)

            return signals

        except Exception as e:
            self.logger.error(f"Error generating trading signals: {str(e)}")
            return []

    async def _analyze_technical_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators for analysis"""
        try:
            # Calculate basic technical indicators
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            data['RSI'] = self._calculate_rsi(data['Close'])

            # Calculate MACD
            exp1 = data['Close'].ewm(span=12, adjust=False).mean()
            exp2 = data['Close'].ewm(span=26, adjust=False).mean()
            data['MACD'] = exp1 - exp2
            data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()

            # Return latest values
            return {
                'close': data['Close'].iloc[-1],
                'sma_20': data['SMA_20'].iloc[-1],
                'sma_50': data['SMA_50'].iloc[-1],
                'rsi': data['RSI'].iloc[-1],
                'macd': data['MACD'].iloc[-1],
                'macd_signal': data['Signal'].iloc[-1],
                'trend': 1 if data['SMA_20'].iloc[-1] > data['SMA_50'].iloc[-1] else -1
            }

        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {str(e)}")
            return {}

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {str(e)}")
            return pd.Series([50] * len(prices))  # Return neutral RSI

    def _calculate_risk_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate risk score based on market analysis"""
        try:
            market_data = analysis['market_data']
            sentiment = analysis['sentiment']

            # Combine various risk factors
            volatility_risk = abs(market_data.get('macd', 0) / market_data.get('close', 1))
            trend_risk = 0.7 if market_data.get('trend', 0) > 0 else 0.3
            sentiment_risk = sentiment.get('volatility', 0.5)

            # Weight and combine risks
            risk_score = (
                volatility_risk * 0.4 +
                trend_risk * 0.3 +
                sentiment_risk * 0.3
            )

            return min(1.0, max(0.0, risk_score))

        except Exception as e:
            self.logger.error(f"Error calculating risk score: {str(e)}")
            return 0.5

    async def backtest_strategy(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Backtest AI trading strategy"""
        try:
            # Get historical data
            historical_data = await self.data_loader.get_historical_data_async(
                symbol, start_date=start_date, end_date=end_date
            )
            if historical_data is None or historical_data.empty:
                return {'error': 'No historical data available'}

            signals = []
            portfolio_value = 1000  # Initial portfolio value
            position = None

            # Simulate trading
            for i in range(len(historical_data)):
                data_window = historical_data.iloc[:i+1]
                analysis = await self._analyze_technical_indicators(data_window)

                if i > 50:  # Wait for enough data
                    signal = await self.generate_trading_signals(symbol)
                    if signal:
                        signals.append(signal[0])
                        # Implement trading logic here

            return {
                'signals': signals,
                'final_value': portfolio_value,
                'total_trades': len(signals)
            }

        except Exception as e:
            self.logger.error(f"Error in backtesting: {str(e)}")
            return {'error': str(e)}

    async def validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Validate trading signal before execution"""
        try:
            if not signal or 'confidence' not in signal:
                return False

            # Basic validation checks
            if signal['confidence'] < self.min_confidence:
                return False

            # Risk management checks
            if signal['analysis']['risk_score'] > 0.8:  # High risk threshold
                return False

            # Market condition checks
            market_data = signal['analysis'].get('market_data', {})
            if market_data.get('rsi', 50) > 70 and signal['action'] == 'buy':
                return False
            if market_data.get('rsi', 50) < 30 and signal['action'] == 'sell':
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating signal: {str(e)}")
            return False