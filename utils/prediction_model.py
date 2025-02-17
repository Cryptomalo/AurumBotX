import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score
import joblib
from datetime import datetime
import logging
import os
import json
import asyncio
from openai import OpenAI, RateLimitError, APIError
from typing import Dict, Any, List, Optional, Union
from utils.indicators import TechnicalIndicators

# Configure logging
logging.basicConfig(level=logging.INFO)

class PredictionModel:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.metrics = {}
        self.indicators = TechnicalIndicators()
        self.max_position_size = 0.1  # 10% of portfolio

        # Initialize OpenAI client if key is available
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.openai_client = OpenAI(api_key=openai_key)
        else:
            self.logger.warning("OpenAI API key not found. AI analysis will be limited.")
            self.openai_client = None

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean DataFrame from NaN and infinite values"""
        try:
            # Replace infinite values with NaN
            df = df.replace([np.inf, -np.inf], np.nan)

            # Forward fill then backward fill NaN values
            df = df.fillna(method='ffill').fillna(method='bfill')

            # If any NaN values remain, fill with 0
            df = df.fillna(0)

            return df
        except Exception as e:
            self.logger.error(f"Error cleaning data: {str(e)}")
            raise

    def create_features(self, data: Union[pd.DataFrame, Dict]) -> pd.DataFrame:
        """Create advanced technical indicators"""
        try:
            # Convert dict to DataFrame if necessary
            if isinstance(data, dict):
                self.logger.info("Converting dictionary to DataFrame")
                # Handle both single point and time series data
                if 'Close' in data and isinstance(data['Close'], (int, float)):
                    df = pd.DataFrame([data])
                elif 'Close' in data and isinstance(data['Close'], (list, np.ndarray)):
                    df = pd.DataFrame(data)
                else:
                    raise ValueError(f"Invalid data structure. Required 'Close' key with numeric value or array. Got: {data.keys()}")
            elif isinstance(data, pd.DataFrame):
                df = data.copy()
            else:
                raise ValueError(f"Unsupported data type: {type(data)}")

            # Standardize column names
            df.columns = df.columns.str.title()

            # Verify required columns
            required_cols = ['Close', 'High', 'Low', 'Open', 'Volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                self.logger.error(f"Missing required columns: {missing_cols}")
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Basic price features
            df['Returns'] = df['Close'].pct_change()
            df['Log_Returns'] = np.log1p(df['Returns'])
            df = self.clean_data(df)  # Clean after calculating returns

            # Technical indicators
            for window in [5, 10, 20, 30]:
                df[f'Volatility_{window}'] = df['Returns'].rolling(window=window).std()
                df[f'Volume_MA_{window}'] = df['Volume'].rolling(window=window).mean()
                df[f'Momentum_{window}'] = df['Close'].pct_change(periods=window)
                df[f'SMA_{window}'] = df['Close'].rolling(window=window).mean()
                df[f'EMA_{window}'] = df['Close'].ewm(span=window, adjust=False).mean()

            # RSI
            for period in [7, 14, 21]:
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                df[f'RSI_{period}'] = 100 - (100 / (1 + rs))

            # MACD
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

            # Final cleaning
            df = self.clean_data(df)

            self.logger.debug(f"Created features DataFrame with shape: {df.shape}")
            return df

        except Exception as e:
            self.logger.error(f"Error creating features: {str(e)}")
            raise

    def prepare_data(self, data: Union[pd.DataFrame, Dict], target_column: str = 'Close', prediction_horizon: int = 5):
        """Prepare data for training"""
        try:
            self.logger.info(f"Preparing data with type: {type(data)}")

            # Create features
            features = self.create_features(data)
            if features is None or features.empty:
                raise ValueError("Feature creation failed")

            # Create target variable (future returns)
            features['target'] = features[target_column].shift(-prediction_horizon)
            features['target_returns'] = features['target'].pct_change(prediction_horizon)

            # Select features for training
            feature_columns = [col for col in features.columns 
                             if col not in ['target', 'target_returns', 'Open', 'High', 'Low', 'Close', 'Volume']]

            X = features[feature_columns].iloc[:-prediction_horizon]
            y = features['target_returns'].iloc[:-prediction_horizon]

            # Clean any remaining NaN values
            X = X.fillna(0)
            y = y.fillna(0)

            return X, y

        except Exception as e:
            self.logger.error(f"Error preparing training data: {str(e)}")
            raise

    def train(self, df: pd.DataFrame, target_column: str = 'Close', prediction_horizon: int = 5) -> Optional[Dict[str, Any]]:
        """Train ensemble of models with improved error handling"""
        try:
            X, y = self.prepare_data(df, target_column, prediction_horizon)

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Initialize models with optimized parameters
            self.models = {
                'rf': RandomForestRegressor(
                    n_estimators=200,
                    max_depth=10,
                    min_samples_split=5,
                    random_state=42
                ),
                'gb': GradientBoostingRegressor(
                    n_estimators=200,
                    learning_rate=0.1,
                    max_depth=5,
                    random_state=42
                )
            }

            # Time series cross-validation
            tscv = TimeSeriesSplit(n_splits=5)
            cv_scores = {name: [] for name in self.models.keys()}

            # Train and evaluate each model
            for train_idx, val_idx in tscv.split(X_scaled):
                X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

                for name, model in self.models.items():
                    model.fit(X_train, y_train)
                    pred = model.predict(X_val)
                    score = r2_score(y_val, pred)
                    cv_scores[name].append(score)

            # Store metrics and feature importance
            self.metrics = {
                'cv_scores_mean': {name: np.mean(scores) for name, scores in cv_scores.items()},
                'cv_scores_std': {name: np.std(scores) for name, scores in cv_scores.items()}
            }

            for name, model in self.models.items():
                if hasattr(model, 'feature_importances_'):
                    self.feature_importance[name] = dict(zip(X.columns, model.feature_importances_))

            return self.metrics

        except Exception as e:
            self.logger.error(f"Training error: {str(e)}")
            return None

    def predict(self, data: Union[pd.DataFrame, Dict]) -> Optional[Dict[str, Any]]:
        """Generate predictions with error handling"""
        try:
            # Create features and prepare data
            features = self.create_features(data)
            feature_columns = [col for col in features.columns 
                             if col not in ['Open', 'High', 'Low', 'Close', 'Volume']]
            X = features[feature_columns]

            if not self.models:
                self.logger.warning("Models not trained. Training now...")
                self.train(features)

            # Scale features
            X_scaled = self.scaler.transform(X)

            # Get predictions from each model
            predictions = {}
            weights = {'rf': 0.6, 'gb': 0.4}  # Random Forest has slightly more weight

            for name, model in self.models.items():
                predictions[name] = model.predict(X_scaled)

            # Weighted ensemble prediction
            weighted_pred = np.zeros(len(X))
            for name, pred in predictions.items():
                weighted_pred += pred * weights[name]

            # Calculate prediction uncertainty
            pred_std = np.std([pred for pred in predictions.values()], axis=0)
            confidence = 1 / (1 + pred_std)

            return {
                'prediction': weighted_pred[-1],  # Latest prediction
                'confidence': float(confidence[-1]),
                'predictions': weighted_pred,
                'model_predictions': predictions,
                'feature_importance': self.feature_importance
            }

        except Exception as e:
            self.logger.error(f"Prediction error: {str(e)}")
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
            f"Recent volatility: {latest_data.get('Volatility_20', 0):.4f}"
        )

    async def _get_openai_analysis(self, market_context: str) -> Dict[str, Any]:
        """Get market analysis from OpenAI asynchronously"""
        try:
            if not self.openai_client:
                return {
                    'signal': 'hold',
                    'confidence': 0.5,
                    'sentiment': 0.5,
                    'reasoning': 'OpenAI client not configured'
                }

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

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            self.logger.error(f"OpenAI analysis error: {str(e)}")
            return {
                'signal': 'hold',
                'confidence': 0.5,
                'sentiment': 0.5,
                'reasoning': 'Analysis failed, defaulting to neutral position'
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
            return 0.05  # Conservative fallback

    async def scan_twitter_sentiment(self, symbol: str) -> Dict[str, float]:
        """
        Analizza il sentiment da Twitter per un dato simbolo
        """
        try:
            if not self.openai_client:
                return {'sentiment': 0.5, 'confidence': 0.5}

            # Simuliamo l'analisi del sentiment per ora
            # TODO: Implementare l'integrazione reale con Twitter
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
        """Prepara features avanzate con deep learning"""
        try:
            features = df.copy()

            # Deep learning features
            for window in [5, 10, 20, 50]:
                features[f'price_momentum_{window}'] = df['Close'].pct_change(window)
                features[f'volume_momentum_{window}'] = df['Volume'].pct_change(window)
                features[f'volatility_{window}'] = df['Close'].pct_change().rolling(window).std()

            # Pattern recognition
            features['pattern_score'] = self._detect_patterns(df)

            # Orderbook analysis
            if 'Bid_Volume' in df.columns and 'Ask_Volume' in df.columns:
                features['order_imbalance'] = (df['Bid_Volume'] - df['Ask_Volume']) / (df['Bid_Volume'] + df['Ask_Volume'])

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

            # Get technical predictions
            technical_prediction = self.predict(market_features)
            if technical_prediction is None:
                self.logger.error("Failed to get technical predictions")
                return None

            # Get AI analysis asynchronously if OpenAI client is available
            market_context = self._prepare_market_context(market_features)
            try:
                ai_analysis = await self._get_openai_analysis(market_context) if self.openai_client else {
                    'sentiment': 0.5,
                    'confidence': 0.5
                }
            except (RateLimitError, APIError) as e:
                self.logger.warning(f"OpenAI API error, using fallback: {str(e)}")
                ai_analysis = {
                    'sentiment': 0.5,
                    'confidence': 0.5,
                    'signal': 'hold',
                    'reasoning': 'API error, using neutral position'
                }

            # Calculate optimal position size
            confidence = self._calculate_confidence(technical_prediction, ai_analysis)
            position_size = self._calculate_position_size(
                confidence,
                risk_metrics['volatility'],
                100000  # Example portfolio value
            )

            # Calculate stop loss levels
            current_price = market_features['Close'].iloc[-1]
            stop_levels = self.calculate_stop_loss(
                current_price,
                risk_metrics,
                'long' if technical_prediction.get('prediction', 0.5) > 0.5 else 'short'
            )

            return {
                'technical_score': technical_prediction.get('prediction', 0.5),
                'sentiment_score': ai_analysis.get('sentiment', 0.5),
                'confidence': confidence,
                'position_size': position_size,
                'risk_metrics': risk_metrics,
                'stop_levels': stop_levels,
                'indicators': {
                    'rsi': market_features.get('RSI_14', pd.Series([])).iloc[-1],
                    'macd': market_features.get('MACD', pd.Series([])).iloc[-1],
                    'atr': market_features.get('ATR', pd.Series([])).iloc[-1]
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

    def _prepare_training_data(self, df: pd.DataFrame, target_column: str = 'Close', prediction_horizon: int = 5):
        """Prepare data for training"""
        try:
            # Create target variable (future returns)
            df['target'] = df[target_column].shift(-prediction_horizon)
            df['target_returns'] = df['target'].pct_change(prediction_horizon)

            # Select features
            feature_columns = [col for col in df.columns 
                             if col not in ['target', 'target_returns', 'Open', 'High', 'Low', 'Close', 'Volume']]

            X = df[feature_columns].iloc[:-prediction_horizon]
            y = df['target_returns'].iloc[:-prediction_horizon]

            # Clean any remaining NaN values
            X = X.fillna(0)
            y = y.fillna(0)

            return X, y

        except Exception as e:
            self.logger.error(f"Error preparing training data: {str(e)}")
            raise

    def _detect_patterns(self, df: pd.DataFrame) -> np.ndarray:
        # Placeholder for pattern recognition algorithm
        # Replace with actual pattern detection logic using deep learning or other methods
        return np.random.rand(len(df))

    def save_model(self, path: str):
        """Save model to disk"""
        if not self.models:
            raise ValueError("No model to save")
        joblib.dump({
            'models': self.models,
            'scaler': self.scaler,
            'metrics': self.metrics,
            'feature_importance': self.feature_importance
        }, path)

    def load_model(self, path: str):
        """Load model from disk"""
        try:
            saved_model = joblib.load(path)
            self.models = saved_model['models']
            self.scaler = saved_model['scaler']
            self.metrics = saved_model['metrics']
            self.feature_importance = saved_model['feature_importance']
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            raise

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
            f"Recent volatility: {latest_data.get('Volatility_20', 0):.4f}"
        )

    async def _get_openai_analysis(self, market_context: str) -> Dict[str, Any]:
        """Get market analysis from OpenAI asynchronously"""
        try:
            if not self.openai_client:
                return {
                    'signal': 'hold',
                    'confidence': 0.5,
                    'sentiment': 0.5,
                    'reasoning': 'OpenAI client not configured'
                }

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

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            self.logger.error(f"OpenAI analysis error: {str(e)}")
            return {
                'signal': 'hold',
                'confidence': 0.5,
                'sentiment': 0.5,
                'reasoning': 'Analysis failed, defaulting to neutral position'
            }