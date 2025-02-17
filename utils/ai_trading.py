import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
from utils.data_loader import CryptoDataLoader, RetryHandler
from utils.sentiment_analyzer import SentimentAnalyzer
from utils.prediction_model import PredictionModel

logger = logging.getLogger(__name__)

class AITrading:
    """Sistema base di trading con AI"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.retry_handler = RetryHandler()
        self.data_loader = CryptoDataLoader()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.prediction_model = PredictionModel()
        self.min_confidence = self.config.get('min_confidence', 0.7)

        logger.info("Sistema di trading AI inizializzato")

    async def analyze_market(self, symbol: str) -> Dict[str, Any]:
        """Analizza le condizioni di mercato"""
        try:
            logger.info(f"Analisi mercato per {symbol}")

            # Recupera dati storici
            market_data = await self.data_loader.get_historical_data(
                symbol=symbol,
                period='1d',
                interval='1h'
            )

            if market_data is None or market_data.empty:
                logger.warning(f"Nessun dato disponibile per {symbol}")
                return {}

            # Analisi del sentiment
            sentiment_data = await self.sentiment_analyzer.analyze_sentiment(symbol)

            # Combina le analisi
            analysis = {
                'market_data': self._extract_market_metrics(market_data),
                'sentiment': sentiment_data,
                'timestamp': datetime.now().isoformat()
            }

            return analysis

        except Exception as e:
            logger.error(f"Errore nell'analisi del mercato: {str(e)}")
            return {}

    def _extract_market_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Estrae metriche chiave dai dati di mercato"""
        try:
            latest = df.iloc[-1]
            return {
                'price': latest['Close'],
                'volume': latest['Volume'],
                'rsi': df.get('RSI', pd.Series([50])).iloc[-1],
                'trend': 1 if df['SMA_20'].iloc[-1] > df['SMA_50'].iloc[-1] else -1
            }
        except Exception as e:
            logger.error(f"Errore nell'estrazione metriche: {str(e)}")
            return {}

    async def generate_trading_signals(self, symbol: str) -> List[Dict[str, Any]]:
        """Genera segnali di trading usando analisi AI"""
        try:
            analysis = await self.analyze_market(symbol)
            if not analysis:
                return []

            # Genera previsioni
            market_data = analysis.get('market_data', {})
            if not market_data:
                return []

            prediction = self.prediction_model.predict(market_data)

            # Genera segnali se la confidenza è sufficiente
            signals = []
            if prediction['confidence'] >= self.min_confidence:
                signal = {
                    'symbol': symbol,
                    'action': 'buy' if prediction['prediction'] > 0.5 else 'sell',
                    'confidence': prediction['confidence'],
                    'price': market_data.get('price', 0),
                    'timestamp': datetime.now().isoformat(),
                    'analysis': {
                        'technical_score': prediction['prediction'],
                        'sentiment_score': analysis['sentiment'].get('score', 0.5)
                    }
                }
                signals.append(signal)

            return signals

        except Exception as e:
            logger.error(f"Errore nella generazione dei segnali: {str(e)}")
            return []

    async def validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Valida un segnale di trading"""
        try:
            if not signal or 'confidence' not in signal:
                return False

            # Validazioni base
            if signal['confidence'] < self.min_confidence:
                return False

            # Controlli sul mercato
            market_data = signal['analysis'].get('market_data', {})
            if market_data.get('rsi', 50) > 70 and signal['action'] == 'buy':
                return False
            if market_data.get('rsi', 50) < 30 and signal['action'] == 'sell':
                return False

            return True

        except Exception as e:
            logger.error(f"Errore nella validazione del segnale: {str(e)}")
            return False

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