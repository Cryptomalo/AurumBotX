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
from openai import OpenAI
from typing import Dict, Any, List, Optional
import pandas_ta as ta

logging.basicConfig(level=logging.INFO)

class PredictionModel:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.metrics = {}

        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def create_features(self, df):
        """Create advanced technical indicators"""
        df = df.copy()

        try:
            # Basic price features
            df['returns'] = df['Close'].pct_change()
            df['log_returns'] = np.log1p(df['returns'])

            # Volatility features
            for window in [5, 10, 20, 30]:
                df[f'volatility_{window}'] = df['returns'].rolling(window=window).std()
                df[f'volume_ma_{window}'] = df['Volume'].rolling(window=window).mean()

            # Price momentum
            for period in [5, 10, 20, 30]:
                df[f'momentum_{period}'] = df['Close'].pct_change(periods=period)

            # Moving averages and crossovers
            for ma_period in [5, 10, 20, 50]:
                df[f'sma_{ma_period}'] = df['Close'].rolling(window=ma_period).mean()
                df[f'ema_{ma_period}'] = df['Close'].ewm(span=ma_period, adjust=False).mean()

            # RSI
            for period in [7, 14, 21]:
                df[f'RSI_{period}'] = ta.rsi(df['Close'], length=period)

            # MACD
            macd = ta.macd(df['Close'])
            df = pd.concat([df, macd], axis=1)

            # Bollinger Bands
            bb = ta.bbands(df['Close'])
            df = pd.concat([df, bb], axis=1)

            # Additional indicators
            df['ADX'] = ta.adx(df['High'], df['Low'], df['Close'])
            df['OBV'] = ta.obv(df['Close'], df['Volume'])

            df = df.dropna()
            return df

        except Exception as e:
            self.logger.error(f"Error creating features: {str(e)}")
            return df

    def analyze_market_with_ai(self, market_data: pd.DataFrame, social_data: Dict) -> Optional[Dict]:
        """Market analysis using AI and multiple data sources"""
        try:
            # Prepare market data features
            market_features = self.create_features(market_data)

            # Get technical predictions
            technical_prediction = self.predict(market_features)
            if technical_prediction is None:
                return None

            # Get AI analysis from OpenAI
            market_context = self._prepare_market_context(market_features)
            ai_analysis = self._get_openai_analysis(market_context)

            # Combine signals
            confidence = self._calculate_confidence(technical_prediction, ai_analysis)

            return {
                'technical_score': technical_prediction.get('prediction', 0.5),
                'sentiment_score': ai_analysis.get('sentiment', 0.5),
                'confidence': confidence,
                'suggested_position_size': self._calculate_position_size(confidence),
                'indicators': {
                    'rsi': market_features['RSI_14'].iloc[-1],
                    'macd': market_features['MACD_12_26_9'].iloc[-1],
                    'adx': market_features['ADX_14'].iloc[-1]
                }
            }

        except Exception as e:
            self.logger.error(f"AI analysis error: {str(e)}")
            return None

    def _prepare_market_context(self, market_data: pd.DataFrame) -> str:
        """Prepare market context for AI analysis"""
        latest_data = market_data.iloc[-1]
        return (
            f"Current market data:\n"
            f"Price: {latest_data['Close']:.2f}\n"
            f"Volume: {latest_data['Volume']:.2f}\n"
            f"RSI: {latest_data.get('RSI_14', 0):.2f}\n"
            f"MACD: {latest_data.get('MACD_12_26_9', 0):.4f}\n"
            f"ADX: {latest_data.get('ADX_14', 0):.2f}\n"
            f"Recent volatility: {latest_data.get('volatility_20', 0):.4f}"
        )

    def _get_openai_analysis(self, market_context: str) -> Dict:
        """Get market analysis from OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
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

    def _calculate_confidence(self, technical_pred: Dict, ai_analysis: Dict) -> float:
        """Calculate overall confidence score"""
        technical_conf = technical_pred.get('confidence', 0.5)
        ai_conf = ai_analysis.get('confidence', 0.5)

        # Weighted average of confidence scores with technical analysis having more weight
        return 0.7 * technical_conf + 0.3 * ai_conf

    def _calculate_position_size(self, confidence: float) -> float:
        """Calculate suggested position size based on confidence"""
        # Base position size on confidence level with conservative scaling
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

    def _prepare_training_data(self, df, target_column='Close', prediction_horizon=5):
        """Prepare data for training"""
        df = self.create_features(df)

        # Create target variable (future returns)
        df['target'] = df[target_column].shift(-prediction_horizon)
        df['target_returns'] = df['target'].pct_change(prediction_horizon)

        # Select features
        feature_columns = [col for col in df.columns if col not in ['target', 'target_returns', 'Open', 'High', 'Low', 'Close', 'Volume']]

        X = df[feature_columns].iloc[:-prediction_horizon]
        y = df['target_returns'].iloc[:-prediction_horizon]

        return X, y

    def predict(self, df, target_column='Close', prediction_horizon=5):
        """Generate ensemble predictions"""
        try:
            if not self.models:
                self.logger.warning("Models not trained. Using default models.")
                self.train(df, target_column, prediction_horizon)

            X, _ = self._prepare_training_data(df, target_column, prediction_horizon)
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
            self.logger.error(f"Prediction error: {str(e)}")
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