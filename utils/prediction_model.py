import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score
import joblib
from datetime import datetime, timedelta

class PredictionModel:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importance = None
        self.metrics = {}

    def create_features(self, df):
        """Create advanced technical indicators"""
        df = df.copy()

        # Price-based features
        df['returns'] = df['Close'].pct_change()
        df['log_returns'] = np.log1p(df['returns'])

        # Volatility features
        df['volatility'] = df['returns'].rolling(window=20).std()
        df['volatility_30'] = df['returns'].rolling(window=30).std()

        # Volume features
        df['volume_ma5'] = df['Volume'].rolling(window=5).mean()
        df['volume_ma20'] = df['Volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['Volume'] / df['volume_ma20']

        # Price momentum
        df['momentum_5'] = df['Close'].pct_change(periods=5)
        df['momentum_20'] = df['Close'].pct_change(periods=20)

        # Moving averages
        df['sma_5'] = df['Close'].rolling(window=5).mean()
        df['sma_20'] = df['Close'].rolling(window=20).mean()
        df['sma_ratio'] = df['sma_5'] / df['sma_20']

        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2

        # Price channels
        df['upper_channel'] = df['High'].rolling(20).max()
        df['lower_channel'] = df['Low'].rolling(20).min()
        df['channel_position'] = (df['Close'] - df['lower_channel']) / (df['upper_channel'] - df['lower_channel'])

        # Drop NaN values
        df = df.dropna()

        return df

    def prepare_data(self, df, target_column='Close', prediction_horizon=5):
        """Prepare data for training"""
        # Create features
        df = self.create_features(df)

        # Create target variable (future returns)
        df['target'] = df[target_column].shift(-prediction_horizon)
        df['target_returns'] = df['target'].pct_change(prediction_horizon)

        # Select features for training
        feature_columns = [
            'returns', 'log_returns', 'volatility', 'volatility_30',
            'volume_ratio', 'momentum_5', 'momentum_20', 'sma_ratio',
            'RSI', 'MACD', 'channel_position'
        ]

        # Split data
        X = df[feature_columns].iloc[:-prediction_horizon]
        y = df['target_returns'].iloc[:-prediction_horizon]

        return X, y

    def train(self, df, target_column='Close', prediction_horizon=5):
        """Train the model with cross-validation"""
        try:
            X, y = self.prepare_data(df, target_column, prediction_horizon)

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Initialize models
            models = {
                'rf': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
                'gb': GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
            }

            # Time series cross-validation
            tscv = TimeSeriesSplit(n_splits=5)
            cv_scores = {name: [] for name in models.keys()}

            for train_idx, val_idx in tscv.split(X_scaled):
                X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

                for name, model in models.items():
                    model.fit(X_train, y_train)
                    pred = model.predict(X_val)
                    score = r2_score(y_val, pred)
                    cv_scores[name].append(score)

            # Select best model
            best_model = max(cv_scores.items(), key=lambda x: np.mean(x[1]))[0]
            self.model = models[best_model]
            self.model.fit(X_scaled, y)

            # Store feature importance
            if hasattr(self.model, 'feature_importances_'):
                self.feature_importance = dict(zip(X.columns, self.model.feature_importances_))

            # Store metrics
            self.metrics = {
                'model_type': best_model,
                'cv_scores_mean': np.mean(cv_scores[best_model]),
                'cv_scores_std': np.std(cv_scores[best_model]),
                'training_size': len(X)
            }

            return self.metrics

        except Exception as e:
            print(f"Error in training: {str(e)}")
            return None

    def predict(self, df, target_column='Close', prediction_horizon=5):
        """Generate predictions"""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        X, _ = self.prepare_data(df, target_column, prediction_horizon)
        X_scaled = self.scaler.transform(X)

        # Make predictions
        predictions = self.model.predict(X_scaled)

        # Calculate prediction intervals
        confidence_intervals = None
        if isinstance(self.model, RandomForestRegressor):
            predictions_all_trees = np.array([tree.predict(X_scaled) 
                                           for tree in self.model.estimators_])
            confidence_intervals = {
                'lower': np.percentile(predictions_all_trees, 25, axis=0),
                'upper': np.percentile(predictions_all_trees, 75, axis=0)
            }

        return {
            'predictions': predictions,
            'confidence_intervals': confidence_intervals
        }

    def get_feature_importance(self):
        """Return feature importance if available"""
        if self.feature_importance is None:
            return None
        return sorted(self.feature_importance.items(), 
                     key=lambda x: x[1], reverse=True)

    def save_model(self, path):
        """Save model to disk"""
        if self.model is None:
            raise ValueError("No model to save")
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'metrics': self.metrics,
            'feature_importance': self.feature_importance
        }, path)

    def load_model(self, path):
        """Load model from disk"""
        saved_model = joblib.load(path)
        self.model = saved_model['model']
        self.scaler = saved_model['scaler']
        self.metrics = saved_model['metrics']
        self.feature_importance = saved_model['feature_importance']