import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import asyncio
from utils.data_loader import CryptoDataLoader
from utils.sentiment_analyzer import SentimentAnalyzer
from utils.prediction_model import PredictionModel

logger = logging.getLogger(__name__)

class RetryHandler:
    """Gestisce i tentativi di retry per le operazioni che possono fallire"""
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def execute(self, operation, *args, **kwargs):
        """Esegue un'operazione con retry e backoff esponenziale"""
        retries = 0
        last_exception = None

        while retries < self.max_retries:
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                retries += 1
                if retries < self.max_retries:
                    delay = self.base_delay * (2 ** (retries - 1))
                    logger.warning(f"Retry {retries}/{self.max_retries} dopo {delay}s. Errore: {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Operazione fallita dopo {self.max_retries} tentativi. Ultimo errore: {str(e)}")

        if last_exception:
            raise last_exception
        return None

class AITrading:
    """Sistema base di trading con AI con gestione errori migliorata"""
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logger
        self.config = config or {}
        self.retry_handler = RetryHandler()
        self.data_loader = CryptoDataLoader()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.prediction_model = PredictionModel()
        self.min_confidence = self.config.get('min_confidence', 0.7)

        # Configurazione retry
        self.max_retries = 3
        self.retry_delay = 1.0  # Delay iniziale in secondi

        self.logger.info("Sistema di trading AI inizializzato con retry configurati")

    async def _retry_operation(self, operation, *args, **kwargs):
        """Gestione retry generica con backoff esponenziale - Now deprecated"""
        return await self.retry_handler.execute(operation, *args, **kwargs)

    def _validate_numeric(self, value: float) -> bool:
        """Validate if a numeric value is valid (not NaN or infinite)"""
        if isinstance(value, (int, float)):
            return not (np.isnan(value) or np.isinf(value))
        return False

    def _extract_market_metrics(self, df: Optional[pd.DataFrame]) -> Dict[str, float]:
        """Estrae metriche chiave dai dati di mercato con validazione"""
        try:
            if df is None or df.empty:
                raise ValueError("DataFrame vuoto o None")

            required_columns = ['Close', 'Volume', 'RSI', 'SMA_20', 'SMA_50']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                self.logger.warning(f"Colonne mancanti: {missing_columns}")
                # Aggiungi colonne mancanti con valori di default
                for col in missing_columns:
                    if col == 'RSI':
                        df[col] = 50  # RSI neutrale
                    elif col in ['SMA_20', 'SMA_50']:
                        df[col] = df['Close'].rolling(window=int(col.split('_')[1])).mean()
                    else:
                        df[col] = 0

            latest = df.iloc[-1]
            metrics = {
                'price': float(latest['Close']),
                'volume': float(latest['Volume']),
                'rsi': float(latest['RSI']),
                'trend': 1 if latest['SMA_20'] > latest['SMA_50'] else -1
            }

            # Validate numeric values
            invalid_metrics = [
                key for key, value in metrics.items()
                if not self._validate_numeric(value)
            ]

            if invalid_metrics:
                self.logger.warning(f"Invalid metrics found: {invalid_metrics}")
                for key in invalid_metrics:
                    metrics[key] = 0.0 if key != 'trend' else 0

            return metrics

        except Exception as e:
            self.logger.error(f"Errore nell'estrazione metriche: {str(e)}")
            return {
                'price': 0.0,
                'volume': 0.0,
                'rsi': 50.0,
                'trend': 0
            }

    async def analyze_market(self, symbol: str) -> Dict[str, Any]:
        """Analizza le condizioni di mercato con retry"""
        try:
            self.logger.info(f"Analisi mercato per {symbol}")

            # Recupera dati storici con retry
            async def get_data():
                market_data = await self.data_loader.get_historical_data(
                    symbol=symbol,
                    period='1d',
                    interval='1h'
                )
                if market_data is None or market_data.empty:
                    raise ValueError(f"Nessun dato disponibile per {symbol}")
                return market_data

            market_data = await self._retry_operation(get_data)

            # Analisi del sentiment con retry e fallback
            async def get_sentiment():
                try:
                    return await self.sentiment_analyzer.analyze_sentiment(symbol)
                except Exception as e:
                    self.logger.warning(f"Fallback a sentiment neutrale per {symbol}: {str(e)}")
                    return {'score': 0.5, 'magnitude': 0.5}

            sentiment_data = await self._retry_operation(get_sentiment)

            # Combina le analisi
            analysis = {
                'market_data': self._extract_market_metrics(market_data),
                'sentiment': sentiment_data,
                'timestamp': datetime.now().isoformat()
            }

            return analysis

        except Exception as e:
            self.logger.error(f"Errore nell'analisi del mercato: {str(e)}")
            return {}

    async def generate_trading_signals(self, symbol: str) -> List[Dict[str, Any]]:
        """Genera segnali di trading usando analisi AI con retry"""
        try:
            # Analisi mercato con retry
            analysis = await self._retry_operation(self.analyze_market, symbol)
            if not analysis:
                return []

            market_data = analysis.get('market_data', {})
            if not market_data:
                return []

            # Genera previsioni con retry e validazione
            async def get_prediction():
                prediction = self.prediction_model.predict(market_data)
                if not isinstance(prediction, dict):
                    raise ValueError("Previsione non valida")
                return prediction

            try:
                prediction = await self._retry_operation(get_prediction)
            except Exception as e:
                self.logger.error(f"Errore previsione, usando default: {str(e)}")
                prediction = {'prediction': 0.5, 'confidence': 0.0}

            signals = []
            if prediction.get('confidence', 0) >= self.min_confidence:
                signal = {
                    'symbol': symbol,
                    'action': 'buy' if prediction.get('prediction', 0.5) > 0.5 else 'sell',
                    'confidence': prediction.get('confidence', 0),
                    'price': market_data.get('price', 0),
                    'timestamp': datetime.now().isoformat(),
                    'analysis': {
                        'technical_score': prediction.get('prediction', 0.5),
                        'sentiment_score': analysis['sentiment'].get('score', 0.5)
                    }
                }
                signals.append(signal)

            return signals

        except Exception as e:
            self.logger.error(f"Errore nella generazione dei segnali: {str(e)}")
            return []

    async def analyze_and_predict(self, symbol: str) -> Dict[str, Any]:
        """Analizza il mercato e genera previsioni con gestione errori completa"""
        try:
            # Ottieni l'analisi del mercato con retry
            analysis = await self._retry_operation(self.analyze_market, symbol)
            if not analysis:
                self.logger.warning(f"Nessuna analisi disponibile per {symbol}")
                return {}

            # Genera segnali di trading
            signals = await self._retry_operation(self.generate_trading_signals, symbol)

            if not signals:
                self.logger.warning(f"Nessun segnale generato per {symbol}")
                return {
                    'timestamp': datetime.now().isoformat(),
                    'symbol': symbol,
                    'action': 'hold',
                    'confidence': 0.0,
                    'price': analysis.get('market_data', {}).get('price', 0),
                    'analysis': {
                        'technical_score': 0.5,
                        'sentiment_score': 0.5,
                        'risk_score': 0.5
                    }
                }

            # Combina analisi e segnali
            signal = signals[0]  # Prendi il primo segnale
            signal_analysis = signal.get('analysis', {})
            return {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'action': signal.get('action', 'hold'),
                'confidence': signal.get('confidence', 0),
                'price': signal.get('price', 0),
                'analysis': {
                    'technical_score': signal_analysis.get('technical_score', 0.5),
                    'sentiment_score': signal_analysis.get('sentiment_score', 0.5),
                    'risk_score': self._calculate_risk_score(analysis)
                }
            }

        except Exception as e:
            self.logger.error(f"Errore in analyze_and_predict: {str(e)}")
            return {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'action': 'hold',
                'confidence': 0,
                'price': 0,
                'analysis': {
                    'technical_score': 0.5,
                    'sentiment_score': 0.5,
                    'risk_score': 0.5
                }
            }

    def _calculate_risk_score(self, analysis: Dict[str, Any]) -> float:
        """Calcola risk score con validazione"""
        try:
            market_data = analysis.get('market_data', {})
            sentiment = analysis.get('sentiment', {})

            if not market_data or not sentiment:
                return 0.5

            volatility_risk = min(1.0, abs(market_data.get('rsi', 50) - 50) / 50)
            trend_risk = 0.7 if market_data.get('trend', 0) > 0 else 0.3
            sentiment_risk = sentiment.get('score', 0.5)

            risk_score = (
                volatility_risk * 0.4 +
                trend_risk * 0.3 +
                sentiment_risk * 0.3
            )

            return min(1.0, max(0.0, risk_score))

        except Exception as e:
            self.logger.error(f"Errore calcolo risk score: {str(e)}")
            return 0.5

    async def validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Valida un segnale di trading"""
        try:
            if not signal or 'confidence' not in signal:
                return False

            # Validazioni base
            if signal['confidence'] < self.min_confidence:
                return False

            # Controlli sul mercato
            market_data = signal.get('analysis', {}).get('market_data', {})
            if market_data.get('rsi', 50) > 70 and signal['action'] == 'buy':
                return False
            if market_data.get('rsi', 50) < 30 and signal['action'] == 'sell':
                return False

            return True

        except Exception as e:
            self.logger.error(f"Errore nella validazione del segnale: {str(e)}")
            return False

    async def _analyze_technical_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators for analysis"""
        try:
            if data is None or data.empty:
                return {}

            # Calculate basic technical indicators
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            data['RSI'] = self._calculate_rsi(data['Close'])

            # Calculate MACD
            exp1 = data['Close'].ewm(span=12, adjust=False).mean()
            exp2 = data['Close'].ewm(span=26, adjust=False).mean()
            data['MACD'] = exp1 - exp2
            data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()

            # Return latest values with validation
            indicators = {
                'close': float(data['Close'].iloc[-1]),
                'sma_20': float(data['SMA_20'].iloc[-1]),
                'sma_50': float(data['SMA_50'].iloc[-1]),
                'rsi': float(data['RSI'].iloc[-1]),
                'macd': float(data['MACD'].iloc[-1]),
                'macd_signal': float(data['Signal'].iloc[-1]),
                'trend': 1 if data['SMA_20'].iloc[-1] > data['SMA_50'].iloc[-1] else -1
            }

            # Validate all values
            for key, value in indicators.items():
                if not self._validate_numeric(value):
                    self.logger.warning(f"Invalid indicator value for {key}")
                    indicators[key] = 0.0 if key != 'trend' else 0

            return indicators

        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {str(e)}")
            return {}

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        try:
            if prices is None or len(prices) < period:
                return pd.Series([50] * len(prices) if prices is not None else [])

            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {str(e)}")
            return pd.Series([50] * len(prices) if prices is not None else [])

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
                    signal = await self._retry_operation(self.generate_trading_signals, symbol)
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