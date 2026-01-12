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

        self.required_columns = ["Open", "High", "Low", "Close", "Volume"]

        # Definizione delle 26 feature attese dal modello
        self.expected_features = [
            'open',
            'high',
            'low',
            'close',
            'volume',
            'returns',
            'volatility',
            'sma_20',
            'ema_20',
            'sma_50',
            'ema_50',
            'sma_200',
            'ema_200',
            'macd',
            'macd_signal',
            'macd_hist',
            'rsi_14',
            'rsi_28',
            'bb_middle',
            'bb_upper',
            'bb_lower',
            'bb_width',
            'atr',
            'volume_ma',
            'volume_ratio',
            'obv'
        ]

    def predict(self, data):
        """Synchronous prediction method with retry logic"""
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                if not self.models:
                    return {"prediction": 0.5, "confidence": 0.5}

                time.sleep(retry_delay * attempt)  # Exponential backoff
                features = self._prepare_features(data)
                weighted_pred = 0

                for name, model in self.models.items():
                    pred = model.predict(features)
                    weighted_pred += pred[0] if len(pred) > 0 else 0.5

                weighted_pred /= len(self.models) if self.models else 1
                return {"prediction": weighted_pred, "confidence": 0.7}

            except Exception as e:
                self.logger.error(f"Prediction error: {str(e)}")
                if attempt == max_retries - 1:
                    return {"prediction": 0.5, "confidence": 0.5}

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
            df["returns"] = df["Close"].pct_change()
            df["log_returns"] = np.log1p(df["returns"])

            # Add technical indicators
            df = self.indicators.add_all_indicators(df)

            # Clean NaN values
            df = df.fillna(method='ffill').fillna(method='bfill')

            return df
        except Exception as e:
            self.logger.error(f"Error creating features: {str(e)}")
            raise

    def prepare_data(self, df: pd.DataFrame, target_column: str = "Close",
                     prediction_horizon: int = 5) -> tuple:
        """Prepare data for training with improved validation"""
        try:
            # Convert dict to DataFrame if necessary
            if isinstance(df, dict):
                df = pd.DataFrame(df)
            elif not isinstance(df, pd.DataFrame):
                raise ValueError(f"Unsupported data type: {type(df)}")

            if not self._validate_dataframe(df):
                raise ValueError("Invalid DataFrame structure")

            # Create features
            df = self.create_features(df)

            # Create target with validation
            if target_column not in df.columns:
                raise ValueError(f"Target column '{target_column}' not found")

            # Ensure numeric type for target column
            df[target_column] = pd.to_numeric(df[target_column], errors='coerce')

            # Create target variables
            df["target"] = df[target_column].shift(-prediction_horizon)
            df["target_returns"] = df["target"].pct_change(prediction_horizon)

            # Select features with validation
            feature_columns = [col for col in df.columns
                            if col not in ["target", "target_returns"] + self.required_columns
                            and pd.api.types.is_numeric_dtype(df[col])]  # Only select numeric columns

            if not feature_columns:
                raise ValueError("No valid numeric feature columns found after preparation")

            # Convert all feature columns to numeric, replacing non-numeric with NaN
            for col in feature_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Drop rows with NaN values
            df = df.dropna(subset=feature_columns + ["target_returns"])

            X = df[feature_columns].iloc[:-prediction_horizon]
            y = df["target_returns"].iloc[:-prediction_horizon]

            # Final validation
            if X.empty or y.empty:
                raise ValueError("Empty feature or target data after preparation")

            return X, y

        except Exception as e:
            self.logger.error(f"Error preparing data: {str(e)}")
            raise

    async def train_async(self, data: Any, target_column: str = "Close",
                         prediction_horizon: int = 5) -> Optional[Dict[str, Any]]:
        """Asynchronous version of train method"""
        try:
            X, y = self.prepare_data(data, target_column, prediction_horizon)

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Initialize models with basic hyperparameters
            self.models = {
                "rf": RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42),
                "gb": GradientBoostingRegressor(n_estimators=200, learning_rate=0.1, random_state=42)
            }

            # Cross validation
            tscv = TimeSeriesSplit(n_splits=5)
            cv_scores = {name: [] for name in self.models.keys()}

            # Train and evaluate asynchronously
            for train_idx, val_idx in tscv.split(X_scaled):
                X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

                for name, model in self.models.items():
                    # Train model asynchronously - converti a numpy per evitare warning
                    X_train_array = X_train if isinstance(X_train, np.ndarray) else X_train
                    X_val_array = X_val if isinstance(X_val, np.ndarray) else X_val
                    await asyncio.to_thread(model.fit, X_train_array, y_train)
                    pred = await asyncio.to_thread(model.predict, X_val_array)
                    score = r2_score(y_val, pred)
                    cv_scores[name].append(score)

            # Store metrics
            self.metrics = {
                "cv_scores_mean": {name: np.mean(scores) for name, scores in cv_scores.items()},
                "cv_scores_std": {name: np.std(scores) for name, scores in cv_scores.items()}
            }

            # Store feature importance
            for name, model in self.models.items():
                if hasattr(model, "feature_importances_"):
                    self.feature_importance[name] = dict(zip(X.columns, model.feature_importances_))

            return self.metrics

        except Exception as e:
            self.logger.error(f"Async training error: {str(e)}")
            return None

    async def predict_async(self, data: Any, target_column: str = "Close",
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
            weights = {"rf": 0.6, "gb": 0.4}

            # Get predictions asynchronously
            for name, model in self.models.items():
                # Converti a numpy array per evitare warning sklearn
                X_array = X_scaled if isinstance(X_scaled, np.ndarray) else X_scaled.values
                predictions[name] = await asyncio.to_thread(model.predict, X_array)

            # Weighted ensemble
            weighted_pred = np.zeros(len(X))
            for name, pred in predictions.items():
                weighted_pred += pred * weights[name]

            # Calculate uncertainty
            pred_std = np.std([pred for pred in predictions.values()], axis=0)
            confidence = 1 / (1 + pred_std)

            return {
                "prediction": float(weighted_pred[-1]),  # Latest prediction
                "confidence": float(confidence[-1]),
                "predictions": weighted_pred.tolist(),
                "model_predictions": {k: v.tolist() for k, v in predictions.items()},
                "feature_importance": self.feature_importance
            }

        except Exception as e:
            self.logger.error(f"Async prediction error: {str(e)}")
            return None

    def save_model(self, path: str):
        """Save model state""" 
        if not self.models:
            raise ValueError("No model to save")
        joblib.dump({
            "models": self.models,
            "scaler": self.scaler,
            "metrics": self.metrics,
            "feature_importance": self.feature_importance
        }, path)

    def load_model(self, path: str):
        """Load model state"""
        try:
            saved_model = joblib.load(path)
            self.models = saved_model["models"]
            self.scaler = saved_model["scaler"]
            self.metrics = saved_model["metrics"]
            self.feature_importance = saved_model["feature_importance"]
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
                "sentiment": max(0, min(1, sentiment_score)),
                "confidence": max(0, min(1, confidence))
            }

        except Exception as e:
            self.logger.error(f"Error scanning Twitter sentiment: {str(e)}")
            return {"sentiment": 0.5, "confidence": 0.5}

    def _prepare_features(self, data) -> pd.DataFrame:
        """Prepara features avanzate con deep learning e analisi multiframe"""
        try:
            # Se data è un dizionario, convertilo in DataFrame
            if isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                df = data.copy()

            # Aggiungi colonne mancanti con valori di default se necessario
            for col in self.required_columns:
                if col not in df.columns:
                    if col == "Close":
                        df[col] = data.get("price", 0.0)
                    elif col == "Volume":
                        df[col] = data.get("volume", 0.0)
                    else:
                        df[col] = 0.0

            # Applica gli indicatori tecnici
            features = self.indicators.add_all_indicators(df)

            # Seleziona solo le colonne numeriche
            numeric_cols = features.select_dtypes(include=np.number).columns.tolist()
            features = features[numeric_cols]

            # Gestisci NaN residui
            features = features.fillna(0)

            # Assicurati che le colonne corrispondano a quelle usate per l\"addestramento
            # Filtra le feature per includere solo quelle attese
            final_features = pd.DataFrame(columns=self.expected_features)
            for col in self.expected_features:
                if col in features.columns:
                    final_features[col] = features[col]
                else:
                    final_features[col] = 0.0 # Aggiungi colonna mancante con valore 0

            # Rimuovi eventuali colonne extra
            final_features = final_features[self.expected_features]

            return final_features
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
            volatility = features["Close"].pct_change().std() * np.sqrt(252)
            avg_volume = features["Volume"].mean()
            price_trend = features["Close"].pct_change(20).mean()

            # Strategy-specific optimization
            if strategy_name == "Scalping":
                optimized_params = {
                    "volume_threshold": int(avg_volume * 0.8),
                    "min_volatility": max(0.0008, volatility / 252),
                    "profit_target": max(0.002, volatility / 10),
                    "initial_stop_loss": max(0.0015, volatility / 15),
                    "trailing_stop": max(0.0008, volatility / 20),
                }
            elif strategy_name == "SwingTrading":
                optimized_params = {
                    "trend_period": 20 if abs(price_trend) > 0.01 else 30,
                    "profit_target": max(0.15, volatility * 2),
                    "stop_loss": max(0.10, volatility * 1.5),
                    "min_trend_strength": min(0.6, volatility * 5),
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
            # Placeholder for actual technical prediction logic
        except Exception as e:
            self.logger.error(f"Error in analyze_market_with_ai: {str(e)}")
            return None


