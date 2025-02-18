import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import r2_score
import joblib
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from utils.indicators import TechnicalIndicators
import random

# Configure logging
logging.basicConfig(level=logging.INFO)

class PredictionModel:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = {}
        
    def predict(self, data):
        """Synchronous prediction method with retry logic"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                if not self.models:
                    return {'prediction': 0.5, 'confidence': 0.5}
                    
                time.sleep(retry_delay * attempt)  # Exponential backoff
            
            features = self._prepare_features(data)
            weighted_pred = 0
            
            for name, model in self.models.items():
                pred = model.predict(features)
                weighted_pred += pred[0] if len(pred) > 0 else 0.5
                
            weighted_pred /= len(self.models) if self.models else 1
            return {'prediction': weighted_pred, 'confidence': 0.7}
            
        except Exception as e:
            self.logger.error(f"Prediction error: {str(e)}")
            return {'prediction': 0.5, 'confidence': 0.5}
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.metrics = {}
        self.indicators = TechnicalIndicators()
        self.openai_client = None
        
        # DeepSeek integration
        try:
            from deepseek import DeepSeekLLM, DeepSeekCoder, DeepSeekMath
            self.deepseek_llm = DeepSeekLLM()
            self.deepseek_coder = DeepSeekCoder()
            self.deepseek_math = DeepSeekMath()
            self.use_deepseek = True
        except:
            self.logger.warning("DeepSeek not available, using fallback models")
            self.use_deepseek = False

        # Risk management parameters
        self.max_position_size = 0.1  # 10% of portfolio
        self.volatility_adjustment = True

        # Required columns for the model
        self.required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']

    def _validate_dataframe(self, df: Any) -> bool:
        """Validate that input is a valid DataFrame with required columns"""
        if not isinstance(df, pd.DataFrame):
            self.logger.error(f"Input is not a DataFrame: {type(df)}")
            return False

        if df.empty:
            self.logger.error("Empty DataFrame provided")
            return False

        missing_cols = [col for col in self.required_columns if col not in df.columns]
        if missing_cols:
            self.logger.error(f"Missing required columns: {missing_cols}")
            return False

        return True

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create technical indicators with validation"""
        try:
            if not self._validate_dataframe(df):
                raise ValueError("Invalid DataFrame structure")

            df = df.copy()

            # Ensure numeric type
            for col in self.required_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Basic price features
            df['returns'] = df['Close'].pct_change()
            df['log_returns'] = np.log1p(df['returns'])

            # Add technical indicators
            df = self.indicators.add_all_indicators(df)

            # Clean NaN values
            df = df.fillna(method='ffill').fillna(method='bfill')

            return df
        except Exception as e:
            self.logger.error(f"Error creating features: {str(e)}")
            raise

    def prepare_data(self, data: Any, target_column: str = 'Close',
                     prediction_horizon: int = 5) -> tuple:
        """Prepare data for training with improved validation"""
        try:
            # Convert dict to DataFrame if necessary
            if isinstance(data, dict):
                # Handle scalar values
                if all(not isinstance(v, (list, np.ndarray)) for v in data.values()):
                    # Convert scalar dict to single-row DataFrame
                    df = pd.DataFrame([data])
                    # Ensure all required columns are present
                    for col in self.required_columns:
                        if col not in df.columns:
                            df[col] = 0.0  # Default value for missing columns
                else:
                    df = pd.DataFrame(data)

                # Ensure proper index
                if 'timestamp' in data:
                    df.index = pd.to_datetime(data['timestamp'])
                else:
                    df.index = pd.date_range(end=datetime.now(), periods=len(df), freq='1min')
            elif isinstance(data, pd.DataFrame):
                df = data.copy()
                if df.index.empty:
                    df.index = pd.date_range(end=datetime.now(), periods=len(df), freq='1min')
            else:
                raise ValueError(f"Unsupported data type: {type(data)}")

            if not self._validate_dataframe(df):
                raise ValueError("Invalid DataFrame structure")

            # Create features
            df = self.create_features(df)

            # Create target with validation
            if target_column not in df.columns:
                raise ValueError(f"Target column '{target_column}' not found")

            df['target'] = df[target_column].shift(-prediction_horizon)
            df['target_returns'] = df['target'].pct_change(prediction_horizon)

            # Select features with validation
            feature_columns = [col for col in df.columns
                               if col not in ['target', 'target_returns'] + self.required_columns]

            if not feature_columns:
                raise ValueError("No valid feature columns found after preparation")

            X = df[feature_columns].iloc[:-prediction_horizon]
            y = df['target_returns'].iloc[:-prediction_horizon]

            # Final validation
            if X.empty or y.empty:
                raise ValueError("Empty feature or target data after preparation")

            return X, y

        except Exception as e:
            self.logger.error(f"Error preparing data: {str(e)}")
            raise

    async def train_async(self, data: Any, target_column: str = 'Close',
                         prediction_horizon: int = 5) -> Optional[Dict[str, Any]]:
        """Asynchronous version of train method"""
        try:
            X, y = self.prepare_data(data, target_column, prediction_horizon)

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Initialize models with basic hyperparameters
            self.models = {
                'rf': RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42),
                'gb': GradientBoostingRegressor(n_estimators=200, learning_rate=0.1, random_state=42)
            }

            # Cross validation
            tscv = TimeSeriesSplit(n_splits=5)
            cv_scores = {name: [] for name in self.models.keys()}

            # Train and evaluate asynchronously
            for train_idx, val_idx in tscv.split(X_scaled):
                X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

                for name, model in self.models.items():
                    # Train model asynchronously
                    await asyncio.to_thread(model.fit, X_train, y_train)
                    pred = await asyncio.to_thread(model.predict, X_val)
                    score = r2_score(y_val, pred)
                    cv_scores[name].append(score)

            # Store metrics
            self.metrics = {
                'cv_scores_mean': {name: np.mean(scores) for name, scores in cv_scores.items()},
                'cv_scores_std': {name: np.std(scores) for name, scores in cv_scores.items()}
            }

            # Store feature importance
            for name, model in self.models.items():
                if hasattr(model, 'feature_importances_'):
                    self.feature_importance[name] = dict(zip(X.columns, model.feature_importances_))

            return self.metrics

        except Exception as e:
            self.logger.error(f"Async training error: {str(e)}")
            return None

    async def predict_async(self, data: Any, target_column: str = 'Close',
                          prediction_horizon: int = 5) -> Optional[Dict[str, Any]]:
        """Asynchronous version of predict method"""
        try:
            if not self.models:
                self.logger.warning("Models not trained. Training now...")
                if await self.train_async(data, target_column, prediction_horizon) is None:
                    raise ValueError("Model training failed")

            # Convert dict to DataFrame if necessary
            if isinstance(data, dict):
                df = pd.DataFrame(data)
            elif isinstance(data, pd.DataFrame):
                df = data.copy()
            else:
                raise ValueError(f"Unsupported data type: {type(data)}")

            X, _ = self.prepare_data(df, target_column, prediction_horizon)
            X_scaled = self.scaler.transform(X)

            predictions = {}
            weights = {'rf': 0.6, 'gb': 0.4}

            # Get predictions asynchronously
            for name, model in self.models.items():
                predictions[name] = await asyncio.to_thread(model.predict, X_scaled)

            # Weighted ensemble
            weighted_pred = np.zeros(len(X))
            for name, pred in predictions.items():
                weighted_pred += pred * weights[name]

            # Calculate uncertainty
            pred_std = np.std([pred for pred in predictions.values()], axis=0)
            confidence = 1 / (1 + pred_std)

            return {
                'prediction': float(weighted_pred[-1]),  # Latest prediction
                'confidence': float(confidence[-1]),
                'predictions': weighted_pred.tolist(),
                'model_predictions': {k: v.tolist() for k, v in predictions.items()},
                'feature_importance': self.feature_importance
            }

        except Exception as e:
            self.logger.error(f"Async prediction error: {str(e)}")
            return None

    def save_model(self, path: str):
        """Save model state"""
        if not self.models:
            raise ValueError("No model to save")
        joblib.dump({
            'models': self.models,
            'scaler': self.scaler,
            'metrics': self.metrics,
            'feature_importance': self.feature_importance
        }, path)

    def load_model(self, path: str):
        """Load model state"""
        try:
            saved_model = joblib.load(path)
            self.models = saved_model['models']
            self.scaler = saved_model['scaler']
            self.metrics = saved_model['metrics']
            self.feature_importance = saved_model['feature_importance']
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            raise

    async def scan_twitter_sentiment(self, symbol: str) -> Dict[str, float]:
        """Analyze Twitter sentiment for a given symbol"""
        try:
            # Simulate sentiment analysis for now
            sentiment_score = 0.5 + np.random.normal(0, 0.1)
            confidence = 0.7 + np.random.normal(0, 0.1)

            return {
                'sentiment': max(0, min(1, sentiment_score)),
                'confidence': max(0, min(1, confidence))
            }

        except Exception as e:
            self.logger.error(f"Error scanning Twitter sentiment: {str(e)}")
            return {'sentiment': 0.5, 'confidence': 0.5}
    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepara features avanzate con deep learning e analisi multiframe"""
        try:
            features = df.copy()
            
            # Multi-timeframe analysis
            timeframes = [5, 15, 30, 60]
            for tf in timeframes:
                features[f'price_momentum_{tf}'] = df['Close'].pct_change(tf)
                features[f'volume_momentum_{tf}'] = df['Volume'].pct_change(tf)
                features[f'volatility_{tf}'] = df['Close'].pct_change().rolling(tf).std()
                
            # Market regime detection
            features['trend_strength'] = abs(features['SMA_20'] - features['SMA_50']) / features['SMA_50']
            features['market_regime'] = np.where(features['trend_strength'] > 0.02, 'trending', 'ranging')
            
            # Deep learning features
            for window in [5, 10, 20, 50]:
                features[f'price_momentum_{window}'] = df['Close'].pct_change(window)
                features[f'volume_momentum_{window}'] = df['Volume'].pct_change(window)
                features[f'volatility_{window}'] = df['Close'].pct_change().rolling(window).std()
            
            # Pattern recognition
            features['pattern_score'] = self._detect_patterns(df)
            
            # Orderbook analysis
            if 'bid_volume' in df.columns and 'ask_volume' in df.columns:
                features['order_imbalance'] = (df['bid_volume'] - df['ask_volume']) / (df['bid_volume'] + df['ask_volume'])
            
            return features
        except Exception as e:
            self.logger.error(f"Error preparing features: {str(e)}")
            raise
    def optimize_strategy_parameters(self, strategy_name: str, market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Ottimizza i parametri della strategia basandosi sui dati storici
        """
        try:
            if market_data.empty:
                raise ValueError("Empty market data provided")

            # Prepare features
            features = self.create_features(market_data)

            # Calculate base metrics
            volatility = features['Close'].pct_change().std() * np.sqrt(252)
            avg_volume = features['Volume'].mean()
            price_trend = features['Close'].pct_change(20).mean()

            # Strategy-specific optimization
            if strategy_name == "Scalping":
                optimized_params = {
                    'volume_threshold': int(avg_volume * 0.8),
                    'min_volatility': max(0.0008, volatility / 252),
                    'profit_target': max(0.002, volatility / 10),
                    'initial_stop_loss': max(0.0015, volatility / 15),
                    'trailing_stop': max(0.0008, volatility / 20),
                }
            elif strategy_name == "SwingTrading":
                optimized_params = {
                    'trend_period': 20 if abs(price_trend) > 0.01 else 30,
                    'profit_target': max(0.15, volatility * 2),
                    'stop_loss': max(0.10, volatility * 1.5),
                    'min_trend_strength': min(0.6, volatility * 5),
                }
            else:
                optimized_params = {}

            self.logger.info(f"Optimized parameters for {strategy_name}: {optimized_params}")
            return optimized_params

        except Exception as e:
            self.logger.error(f"Error optimizing strategy parameters: {str(e)}")
            return {}

    async def analyze_market_with_ai(self, market_data: pd.DataFrame, social_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Market analysis using AI and multiple data sources with enhanced risk management"""
        try:
            # Prepare market data features
            market_features = self.create_features(market_data)
            if market_features.empty:
                self.logger.error("Empty market features after processing")
                return None

            # Calculate risk metrics
            risk_metrics = self.calculate_risk_metrics(market_features)

            # Get technical predictions with retries
            technical_prediction = None
            for attempt in range(3):
                try:
                    technical_prediction = await self.predict_async(market_features)
                    if technical_prediction is not None:
                        break
                except Exception as e:
                    self.logger.warning(f"Technical prediction attempt {attempt + 1} failed: {e}")
                    if attempt == 2:  # Last attempt
                        self.logger.error("All technical prediction attempts failed")
                        return None
                    await asyncio.sleep(1)  # Wait before retry

            # Get AI analysis asynchronously if OpenAI client is available
            market_context = self._prepare_market_context(market_features)
            ai_analysis = await self._get_openai_analysis(market_context) if self.openai_client else {
                'sentiment': 0.5,
                'confidence': 0.5,
                'reasoning': 'AI service not available'
            }

            # Validate technical prediction before proceeding
            if technical_prediction is None:
                self.logger.error("Technical prediction is None after retries")
                return None

            # Calculate optimal position size with enhanced validation
            confidence = self._calculate_confidence(technical_prediction, ai_analysis)
            position_size = self._calculate_position_size(
                confidence,
                risk_metrics['volatility'],
                100000  # Example portfolio value
            )

            # Calculate stop loss levels with proper error handling
            try:
                current_price = float(market_features['Close'].iloc[-1])
                stop_levels = self.calculate_stop_loss(
                    current_price,
                    risk_metrics,
                    'long' if technical_prediction.get('prediction', 0.5) > 0.5 else 'short'
                )
            except (IndexError, ValueError) as e:
                self.logger.error(f"Error calculating stop levels: {e}")
                stop_levels = None

            return {
                'technical_score': technical_prediction.get('prediction', 0.5),
                'sentiment_score': ai_analysis.get('sentiment', 0.5),
                'confidence': confidence,
                'position_size': position_size,
                'risk_metrics': risk_metrics,
                'stop_levels': stop_levels,
                'reasoning': ai_analysis.get('reasoning', 'Technical analysis only'),
                'analysis_source': 'ai_enhanced' if self.openai_client else 'technical_only',
                'indicators': {
                    'rsi': float(market_features.get('RSI_14', pd.Series([])).iloc[-1]),
                    'macd': float(market_features.get('MACD', pd.Series([])).iloc[-1]),
                    'atr': float(market_features.get('ATR', pd.Series([])).iloc[-1])
                }
            }

        except Exception as e:
            self.logger.error(f"AI analysis error: {str(e)}")
            return None

    def calculate_risk_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate comprehensive risk metrics"""
        try:
            returns = df['Close'].pct_change().fillna(0)

            # Value at Risk (VaR)
            var_95 = np.percentile(returns, 5)

            # Expected Shortfall (Conditional VaR)
            es_95 = returns[returns <= var_95].mean()

            # Volatility (20-day annualized)
            volatility = returns.rolling(window=20).std().iloc[-1] * np.sqrt(252)

            # Maximum Drawdown
            cumulative_returns = (1 + returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdowns = cumulative_returns/rolling_max - 1
            max_drawdown = drawdowns.min()

            # Sharpe Ratio (assuming 0% risk-free rate for simplicity)
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)

            # Sortino Ratio (downside deviation only)
            negative_returns = returns[returns < 0]
            sortino = np.mean(returns) / negative_returns.std() * np.sqrt(252)

            return {
                'var_95': var_95,
                'expected_shortfall': es_95,
                'volatility': volatility,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe,
                'sortino_ratio': sortino
            }

        except Exception as e:
            self.logger.error(f"Risk metrics calculation error: {e}")
            return {
                'var_95': -0.02,
                'expected_shortfall': -0.03,
                'volatility': 0.02,
                'max_drawdown': -0.1,
                'sharpe_ratio': 0,
                'sortino_ratio': 0
            }

    def calculate_stop_loss(self, 
                           entry_price: float, 
                           risk_metrics: Dict[str, float],
                           position_type: str = 'long') -> Dict[str, float]:
        """Calculate dynamic stop loss and take profit levels"""
        try:
            # ATR-based stop loss
            atr = risk_metrics.get('volatility', 0.02) * entry_price

            # Dynamic multiplier based on volatility
            vol_multiplier = 1 + (risk_metrics.get('volatility', 0.02) / 0.02)

            if position_type == 'long':
                stop_loss = entry_price - (atr * vol_multiplier)
                take_profit = entry_price + (atr * vol_multiplier * 2)
            else:
                stop_loss = entry_price + (atr * vol_multiplier)
                take_profit = entry_price - (atr * vol_multiplier * 2)

            return {
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'trailing_stop_distance': atr * vol_multiplier,
                'risk_reward_ratio': 2.0
            }

        except Exception as e:
            self.logger.error(f"Stop loss calculation error: {e}")
            return {
                'stop_loss': entry_price * 0.98 if position_type == 'long' else entry_price * 1.02,
                'take_profit': entry_price * 1.04 if position_type == 'long' else entry_price * 0.96,
                'trailing_stop_distance': entry_price * 0.01,
                'risk_reward_ratio': 2.0
            }

    async def _analyze_with_deepseek(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze market data using DeepSeek models"""
        if not self.use_deepseek:
            return None
            
        try:
            # Pattern recognition with DeepSeek-LLM
            pattern_analysis = await self.deepseek_llm.analyze_patterns(market_data)
            
            # Strategy optimization with DeepSeek-Coder
            strategy_improvements = await self.deepseek_coder.optimize_trading_logic(
                self.models,
                market_data
            )
            
            # Advanced financial calculations
            risk_metrics = await self.deepseek_math.calculate_advanced_metrics(
                market_data,
                include_volatility=True,
                include_kelly=True
            )
            
            return {
                'pattern_analysis': pattern_analysis,
                'strategy_improvements': strategy_improvements,
                'risk_metrics': risk_metrics,
                'confidence': 0.85  # DeepSeek typically has higher confidence
            }
        except Exception as e:
            self.logger.error(f"DeepSeek analysis error: {e}")
            return None

    def _prepare_market_context(self, market_data: pd.DataFrame) -> str:
        """Prepare market context for AI analysis"""
        latest_data = market_data.iloc[-1]
        return (
            f"Current market data:\n"
            f"Price: {latest_data.get('Close', 0):.2f}\n"
            f"Volume: {latest_data.get('Volume', 0):.2f}\n"
            f"RSI: {latest_data.get('RSI_14', 0):.2f}\n"
            f"MACD: {latest_data.get('MACD', 0):.4f}\n"
            f"ATR: {latest_data.get('ATR', 0):.2f}\n"
            f"Recent volatility: {latest_data.get('volatility_20', 0):.4f}"
        )

    async def _get_openai_analysis(self, market_context: str) -> Dict[str, Any]:
        """Get market analysis from OpenAI with improved error handling and rate limiting"""
        if not self.openai_client:
            return {
                'signal': 'hold',
                'confidence': 0.5,
                'sentiment': 0.5,
                'reasoning': 'OpenAI client not configured'
            }

        max_retries = 5
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                # Calculate exponential backoff delay
                delay = base_delay * (2 ** attempt)

                # Add jitter to avoid thundering herd
                jitter = random.uniform(0, 0.1)
                total_delay = delay + jitter

                if attempt > 0:
                    self.logger.info(f"Retrying OpenAI request in {total_delay:.2f} seconds (attempt {attempt + 1})")
                    await asyncio.sleep(total_delay)

                response = await asyncio.to_thread(
                    self.openai_client.chat.completions.create,
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert crypto market analyst. Analyze the given market data "
                                "and provide a trading signal with confidence score. Respond in JSON format."
                            )
                        },
                        {
                            "role": "user",
                            "content": f"Analyze this market data and provide trading signals:\n{market_context}"
                        }
                    ],
                    response_format={"type": "json_object"}
                )

                if response and response.choices:
                    return json.loads(response.choices[0].message.content)

            except Exception as e:
                error_msg = str(e).lower()
                if "rate limit" in error_msg:
                    if attempt == max_retries - 1:
                        self.logger.error("OpenAI rate limit exceeded after all retries")
                        break
                    continue
                elif "timeout" in error_msg or "connection" in error_msg:
                    if attempt == max_retries - 1:
                        self.logger.error(f"OpenAI request failed after {max_retries} retries: {e}")
                        break
                    continue
                else:
                    self.logger.error(f"Unexpected OpenAI error: {e}")
                    break

        # Fallback response if all retries failed
        return {
            'signal': 'hold',
            'confidence': 0.5,
            'sentiment': 0.5,
            'reasoning': 'Analysis failed, using technical signals only'
        }

    def _calculate_confidence(self, technical_pred: Dict[str, Any], ai_analysis: Dict[str, Any]) -> float:
        """Calculate overall confidence score"""
        technical_conf = technical_pred.get('confidence', 0.5)
        ai_conf = ai_analysis.get('confidence', 0.5)
        return 0.7 * technical_conf + 0.3 * ai_conf

    def _calculate_position_size(self, confidence: float, volatility: float, portfolio_value: float) -> float:
        """Calculate position size based on multiple risk factors"""
        try:
            # Base position size from confidence
            base_size = min(1.0, max(0.1, confidence * 0.8))

            # Adjust for volatility
            if self.volatility_adjustment:
                vol_factor = 1 / (1 + volatility)
                base_size *= vol_factor

            # Apply maximum risk per trade
            position_value = portfolio_value * base_size
            position_value = min(position_value, portfolio_value * self.max_position_size)

            # Normalize to percentage
            final_size = position_value / portfolio_value

            self.logger.info(f"Calculated position size: {final_size:.2%}")
            return final_size

        except Exception as e:
            self.logger.error(f"Position size calculation error: {e}")
            return self.max_position_size * 0.5  # Conservative fallback
            
    def _detect_patterns(self, df: pd.DataFrame) -> np.ndarray:
        """Pattern recognition placeholder"""
        return np.random.rand(len(df))