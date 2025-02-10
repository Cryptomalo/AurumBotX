import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import xgboost as xgb
import lightgbm as lgb
import joblib
from datetime import datetime, timedelta

class PredictionModel:
    def __init__(self):
        self.models = {}
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.metrics = {}

    def create_features(self, df):
        """Create advanced technical indicators"""
        df = df.copy()

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
        for ma_period in [5, 10, 20, 50, 100]:
            df[f'sma_{ma_period}'] = df['Close'].rolling(window=ma_period).mean()
            df[f'ema_{ma_period}'] = df['Close'].ewm(span=ma_period, adjust=False).mean()

        # RSI with multiple periods
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

        # Bollinger Bands
        for window in [20, 50]:
            df[f'BB_middle_{window}'] = df['Close'].rolling(window=window).mean()
            df[f'BB_upper_{window}'] = df[f'BB_middle_{window}'] + 2 * df['Close'].rolling(window=window).std()
            df[f'BB_lower_{window}'] = df[f'BB_middle_{window}'] - 2 * df['Close'].rolling(window=window).std()
            df[f'BB_width_{window}'] = (df[f'BB_upper_{window}'] - df[f'BB_lower_{window}']) / df[f'BB_middle_{window}']

        # Advanced volume indicators
        df['OBV'] = (df['Close'].diff().apply(np.sign) * df['Volume']).cumsum()
        df['Volume_ROC'] = df['Volume'].pct_change()

        # Drop NaN values
        df = df.dropna()

        return df

    def prepare_lstm_data(self, X, time_steps=10):
        """Prepare data for LSTM model"""
        X_lstm = []
        for i in range(len(X) - time_steps):
            X_lstm.append(X[i:(i + time_steps)].values)
        return np.array(X_lstm)

    def create_lstm_model(self, input_shape):
        """Create LSTM model"""
        model = Sequential([
            LSTM(100, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def prepare_data(self, df, target_column='Close', prediction_horizon=5):
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

    def train(self, df, target_column='Close', prediction_horizon=5):
        """Train ensemble of models with auto-optimization"""
        try:
            # Auto-optimize hyperparameters
            self.optimize_hyperparameters(df)
            
            # Dynamic ensemble weighting based on recent performance
            self.ensemble_weights = self.calculate_dynamic_weights(df)
            X, y = self.prepare_data(df, target_column, prediction_horizon)

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Initialize models
            self.models = {
                'rf': RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42),
                'gb': GradientBoostingRegressor(n_estimators=200, learning_rate=0.1, random_state=42),
                'xgb': xgb.XGBRegressor(n_estimators=200, learning_rate=0.1, random_state=42),
                'lgb': lgb.LGBMRegressor(n_estimators=200, learning_rate=0.1, random_state=42)
            }

            # Prepare LSTM data
            X_lstm = self.prepare_lstm_data(X_scaled)
            y_lstm = y[10:].values  # Adjust target for LSTM

            # Create and add LSTM model
            self.models['lstm'] = self.create_lstm_model((X_lstm.shape[1], X_lstm.shape[2]))

            # Time series cross-validation
            tscv = TimeSeriesSplit(n_splits=5)
            cv_scores = {name: [] for name in self.models.keys()}

            # Train and evaluate each model
            for train_idx, val_idx in tscv.split(X_scaled):
                X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

                # Train standard models
                for name, model in self.models.items():
                    if name != 'lstm':
                        model.fit(X_train, y_train)
                        pred = model.predict(X_val)
                        score = r2_score(y_val, pred)
                        cv_scores[name].append(score)

                # Train LSTM
                if len(train_idx) > 10:  # Ensure enough data for LSTM
                    X_lstm_train = self.prepare_lstm_data(X_train)
                    y_lstm_train = y_train[10:].values
                    X_lstm_val = self.prepare_lstm_data(X_val)
                    y_lstm_val = y_val[10:].values

                    self.models['lstm'].fit(X_lstm_train, y_lstm_train, 
                                          epochs=50, batch_size=32, verbose=0)
                    pred_lstm = self.models['lstm'].predict(X_lstm_val)
                    score_lstm = r2_score(y_lstm_val, pred_lstm)
                    cv_scores['lstm'].append(score_lstm)

            # Store metrics
            self.metrics = {
                'cv_scores_mean': {name: np.mean(scores) for name, scores in cv_scores.items()},
                'cv_scores_std': {name: np.std(scores) for name, scores in cv_scores.items()},
                'training_size': len(X),
                'feature_names': X.columns.tolist()
            }

            # Store feature importance for applicable models
            for name, model in self.models.items():
                if hasattr(model, 'feature_importances_'):
                    self.feature_importance[name] = dict(zip(X.columns, model.feature_importances_))

            return self.metrics

        except Exception as e:
            print(f"Error in training: {str(e)}")
            return None

    def predict(self, df, target_column='Close', prediction_horizon=5):
        """Generate ensemble predictions"""
        if not self.models:
            raise ValueError("Models not trained. Call train() first.")

        X, _ = self.prepare_data(df, target_column, prediction_horizon)
        X_scaled = self.scaler.transform(X)

        predictions = {}
        ensemble_weights = {
            'rf': 0.25,
            'gb': 0.2,
            'xgb': 0.25,
            'lgb': 0.2,
            'lstm': 0.1
        }

        # Get predictions from each model
        for name, model in self.models.items():
            if name == 'lstm':
                X_lstm = self.prepare_lstm_data(X_scaled)
                if len(X_lstm) > 0:
                    pred = model.predict(X_lstm)
                    # Pad predictions to match length
                    pad_length = len(X) - len(pred)
                    predictions[name] = np.pad(pred.flatten(), (pad_length, 0), 'edge')
            else:
                predictions[name] = model.predict(X_scaled)

        # Combine predictions using weights
        weighted_pred = np.zeros(len(X))
        for name, pred in predictions.items():
            weighted_pred += pred * ensemble_weights[name]

        # Calculate prediction intervals using model variance
        pred_std = np.std([pred for pred in predictions.values()], axis=0)
        confidence_intervals = {
            'lower': weighted_pred - 2 * pred_std,
            'upper': weighted_pred + 2 * pred_std
        }

        return {
            'predictions': weighted_pred,
            'confidence_intervals': confidence_intervals,
            'model_predictions': predictions
        }

    def get_feature_importance(self):
        """Return feature importance for all applicable models"""
        if not self.feature_importance:
            return None

        # Aggregate feature importance across models
        all_features = set()
        for importances in self.feature_importance.values():
            all_features.update(importances.keys())

        aggregated_importance = {feature: 0.0 for feature in all_features}
        for importances in self.feature_importance.values():
            for feature, importance in importances.items():
                aggregated_importance[feature] += importance

        # Normalize and sort
        total = sum(aggregated_importance.values())
        normalized_importance = {k: v/total for k, v in aggregated_importance.items()}

        return sorted(normalized_importance.items(), key=lambda x: x[1], reverse=True)

    def save_model(self, path):
        """Save model to disk"""
        if not self.models:
            raise ValueError("No model to save")
        joblib.dump({
            'models': self.models,
            'scaler': self.scaler,
            'metrics': self.metrics,
            'feature_importance': self.feature_importance
        }, path)

    def load_model(self, path):
        """Load model from disk"""
        saved_model = joblib.load(path)
        self.models = saved_model['models']
        self.scaler = saved_model['scaler']
        self.metrics = saved_model['metrics']
        self.feature_importance = saved_model['feature_importance']