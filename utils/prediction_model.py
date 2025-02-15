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
from openai import OpenAI
from typing import Dict, Any, List, Optional
from utils.indicators import TechnicalIndicators  # Using our custom indicators

# Configure logging
logging.basicConfig(level=logging.INFO)

class PredictionModel:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.metrics = {}
        self.indicators = TechnicalIndicators()  # Initialize our technical indicators

        # Risk management parameters
        self.max_position_size = 0.1  # 10% of portfolio
        self.max_risk_per_trade = 0.02  # 2% risk per trade
        self.volatility_adjustment = True

        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def create_features(self, df):
        """Create advanced technical indicators using standardized column names"""
        try:
            df = df.copy()

            # Ensure proper column names
            column_mapping = {
                'open': 'Open', 'high': 'High', 'low': 'Low',
                'close': 'Close', 'volume': 'Volume'
            }
            df.rename(columns={k: v for k, v in column_mapping.items() 
                            if k in df.columns}, inplace=True)

            # Add all technical indicators using our custom implementation
            df = self.indicators.add_all_indicators(df)

            # Price momentum
            for period in [5, 10, 20, 30]:
                df[f'momentum_{period}'] = df['Close'].pct_change(periods=period)

            df = df.dropna()
            return df

        except Exception as e:
            self.logger.error(f"Error creating features: {str(e)}")
            return df

    def _calculate_position_size(self, confidence: float, volatility: float, portfolio_value: float) -> float:
        """Calculate position size based on multiple risk factors"""
        try:
            # Base position size from confidence
            base_size = min(1.0, max(0.1, confidence * 0.8))

            # Adjust for volatility
            if self.volatility_adjustment:
                # Reduce position size in high volatility
                vol_factor = 1 / (1 + volatility)
                base_size *= vol_factor

            # Apply maximum risk per trade
            max_trade_value = portfolio_value * self.max_risk_per_trade
            position_value = portfolio_value * base_size

            # Ensure we don't exceed maximum position size
            position_value = min(position_value, 
                               portfolio_value * self.max_position_size)

            # Normalize to percentage
            final_size = position_value / portfolio_value

            self.logger.info(f"Calculated position size: {final_size:.2%}")
            return final_size

        except Exception as e:
            self.logger.error(f"Position size calculation error: {e}")
            return self.max_position_size * 0.5  # Conservative fallback

    def calculate_risk_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate comprehensive risk metrics"""
        try:
            returns = df['Returns'].fillna(0)

            # Value at Risk (VaR)
            var_95 = np.percentile(returns, 5)

            # Expected Shortfall (Conditional VaR)
            es_95 = returns[returns <= var_95].mean()

            # Volatility (20-day)
            volatility = returns.rolling(window=20).std().iloc[-1] * np.sqrt(252)

            # Maximum Drawdown
            cumulative_returns = (1 + returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdowns = cumulative_returns/rolling_max - 1
            max_drawdown = drawdowns.min()

            # Sharpe Ratio (assuming 0% risk-free rate for simplicity)
            sharpe = returns.mean() / returns.std() * np.sqrt(252)

            # Sortino Ratio (downside deviation only)
            negative_returns = returns[returns < 0]
            sortino = returns.mean() / negative_returns.std() * np.sqrt(252)

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

    async def analyze_market_with_ai(self, market_data: pd.DataFrame, social_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Market analysis using AI and multiple data sources with enhanced risk management"""
        try:
            # Prepare market data features
            market_features = self.create_features(market_data)
            if market_features is None:
                return None

            # Calculate risk metrics
            risk_metrics = self.calculate_risk_metrics(market_features)

            # Get technical predictions
            technical_prediction = self.predict(market_features)
            if technical_prediction is None:
                return None

            # Get AI analysis asynchronously
            market_context = self._prepare_market_context(market_features)
            ai_analysis = await self._get_openai_analysis(market_context)

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
                # Stop loss for long positions
                stop_loss = entry_price - (atr * vol_multiplier)
                # Take profit based on risk:reward ratio
                take_profit = entry_price + (atr * vol_multiplier * 2)
            else:
                # Stop loss for short positions
                stop_loss = entry_price + (atr * vol_multiplier)
                # Take profit based on risk:reward ratio
                take_profit = entry_price - (atr * vol_multiplier * 2)

            # Calculate trailing stop parameters
            trailing_stop_distance = atr * vol_multiplier

            return {
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'trailing_stop_distance': trailing_stop_distance,
                'risk_reward_ratio': 2.0
            }

        except Exception as e:
            self.logger.error(f"Stop loss calculation error: {e}")
            # Return conservative default values
            return {
                'stop_loss': entry_price * 0.98 if position_type == 'long' else entry_price * 1.02,
                'take_profit': entry_price * 1.04 if position_type == 'long' else entry_price * 0.96,
                'trailing_stop_distance': entry_price * 0.01,
                'risk_reward_ratio': 2.0
            }

    async def analyze_market_with_ai(self, market_data: pd.DataFrame, social_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Market analysis using AI and multiple data sources with enhanced risk management"""
        try:
            # Prepare market data features
            market_features = self.create_features(market_data)
            if market_features is None:
                return None

            # Calculate risk metrics
            risk_metrics = self.calculate_risk_metrics(market_features)

            # Get technical predictions
            technical_prediction = self.predict(market_features)
            if technical_prediction is None:
                return None

            # Get AI analysis asynchronously
            market_context = self._prepare_market_context(market_features)
            ai_analysis = await self._get_openai_analysis(market_context)

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

    def _prepare_market_context(self, market_data: pd.DataFrame) -> str:
        """Prepare market context for AI analysis using standardized column names"""
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

    def _prepare_training_data(self, df, target_column='Close', prediction_horizon=5):
        """Prepare data for training using standardized column names"""
        try:
            df = self.create_features(df)

            # Clean any string values in numeric columns
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                # Extract numeric values from strings like 'bullish_0.60'
                if df[col].dtype == object:
                    df[col] = df[col].apply(lambda x: float(str(x).split('_')[-1]) 
                                          if isinstance(x, str) and '_' in str(x) 
                                          else x)
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Create target variable (future returns)
            df['target'] = df[target_column].shift(-prediction_horizon)
            df['target_returns'] = df['target'].pct_change(prediction_horizon)

            # Select features
            feature_columns = [col for col in df.columns 
                             if col not in ['target', 'target_returns', 'Open', 'High', 'Low', 'Close', 'Volume']]

            X = df[feature_columns].iloc[:-prediction_horizon]
            y = df['target_returns'].iloc[:-prediction_horizon]

            # Fill any remaining NaN values
            X = X.fillna(0)
            y = y.fillna(0)

            return X, y

        except Exception as e:
            self.logger.error(f"Error preparing training data: {e}")
            raise

    def _calculate_confidence(self, technical_pred: Dict[str, Any], ai_analysis: Dict[str, Any]) -> float:
        """Calculate overall confidence score"""
        technical_conf = technical_pred.get('confidence', 0.5)
        ai_conf = ai_analysis.get('confidence', 0.5)

        # Weighted average with technical analysis having more weight
        return 0.7 * technical_conf + 0.3 * ai_conf

    def _calculate_position_size(self, confidence: float) -> float:
        """Calculate suggested position size based on confidence"""
        return min(1.0, max(0.1, confidence * 0.8))

    def train(self, df, target_column='Close', prediction_horizon=5):
        """Train ensemble of models"""
        try:
            X, y = self._prepare_training_data(df, target_column, prediction_horizon)

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

            # Store feature importance
            for name, model in self.models.items():
                if hasattr(model, 'feature_importances_'):
                    self.feature_importance[name] = dict(zip(X.columns, model.feature_importances_))

            return self.metrics

        except Exception as e:
            self.logger.error(f"Training error: {str(e)}")
            return None

    async def _get_openai_analysis(self, market_context: str) -> Dict[str, Any]:
        """Get market analysis from OpenAI asynchronously"""
        try:
            # Run OpenAI API call in a thread pool to avoid blocking
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4o",  # Using the latest model as of May 13, 2024
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

    def predict(self, df, target_column='Close', prediction_horizon=5):
        """Generate ensemble predictions with improved error handling"""
        try:
            if not self.models:
                self.logger.warning("Models not trained. Using default models.")
                self.train(df, target_column, prediction_horizon)

            X, _ = self._prepare_training_data(df, target_column, prediction_horizon)

            # Ensure all features are numeric
            X = X.apply(pd.to_numeric, errors='coerce')
            X = X.fillna(0)

            X_scaled = self.scaler.transform(X)

            predictions = {}
            weights = {'rf': 0.6, 'gb': 0.4}  # Random Forest has slightly more weight

            # Get predictions from each model
            for name, model in self.models.items():
                predictions[name] = model.predict(X_scaled)

            # Weighted ensemble prediction
            weighted_pred = np.zeros(len(X))
            for name, pred in predictions.items():
                weighted_pred += pred * weights[name]

            # Calculate prediction uncertainty
            pred_std = np.std([pred for pred in predictions.values()], axis=0)
            confidence = 1 / (1 + pred_std)  # Higher variance = lower confidence

            return {
                'prediction': weighted_pred[-1],  # Latest prediction
                'confidence': float(confidence[-1]),
                'predictions': weighted_pred,
                'model_predictions': predictions,
                'feature_importance': self.feature_importance
            }

        except Exception as e:
            self.logger.error(f"Prediction error: {e}")
            return None

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

    # Placeholder functions -  replace with actual implementations
    def optimize_hyperparameters(self, df):
        pass

    def calculate_dynamic_weights(self, df):
        return {'rf': 0.6, 'gb': 0.4}

    def _get_technical_predictions(self, market_data):
        return {'score': 0.7, 'confidence': 0.8}

    def _analyze_social_sentiment(self, social_data):
        return {'score': 0.6, 'confidence': 0.7}

    def _analyze_blockchain_metrics(self, symbol):
        return {'score': 0.5, 'confidence': 0.6}