import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from utils.prediction_model import PredictionModel

class TradingBot:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            min_samples_leaf=5,
            max_depth=15,
            class_weight='balanced'
        )
        self.max_drawdown = 0.15  # 15% massimo drawdown
        self.position_sizing = {
            'min_position': 0.01,  # 1% minimo per posizione
            'max_position': 0.10   # 10% massimo per posizione
        }
        self.scaler = StandardScaler()
        self.prediction_model = PredictionModel()
        self.feature_names = [
            'SMA_ratio', 'RSI', 'MACD', 'Volume',
            'price_change', 'price_volatility'
        ]

    def prepare_features(self, df):
        """Prepare features for the model"""
        try:
            features = pd.DataFrame(index=df.index)

            # Technical indicators as features
            features['SMA_ratio'] = df['Close'] / df['SMA_20']
            features['RSI'] = df['RSI']
            features['MACD'] = df['MACD']
            features['Volume'] = df['Volume']

            # Price changes
            features['price_change'] = df['Close'].pct_change()
            features['price_volatility'] = df['Close'].rolling(window=20).std()

            # Add advanced predictions
            try:
                if hasattr(self.prediction_model, 'model') and self.prediction_model.model is not None:
                    predictions = self.prediction_model.predict(df)
                    features['price_prediction'] = predictions['predictions']
                    if predictions.get('confidence_intervals'):
                        features['prediction_uncertainty'] = (
                            predictions['confidence_intervals']['upper'] - 
                            predictions['confidence_intervals']['lower']
                        )
            except Exception as e:
                print(f"Error in advanced predictions: {e}")
                features['price_prediction'] = 0
                features['prediction_uncertainty'] = 0

            # Remove NaN values
            features = features.dropna()
            return features
        except Exception as e:
            print(f"Error in prepare_features: {e}")
            return pd.DataFrame()

    def prepare_labels(self, df, valid_indices):
        """Create labels for training"""
        try:
            future_returns = df['Close'].shift(-1) / df['Close'] - 1
            labels = future_returns.loc[valid_indices]
            labels = (labels > 0).astype(int)
            return labels[:-1]
        except Exception as e:
            print(f"Error in prepare_labels: {e}")
            return pd.Series()

    def train(self, df):
        """Train both classification and prediction models"""
        try:
            # Train prediction model first
            prediction_metrics = self.prediction_model.train(df)
            print("Prediction model metrics:", prediction_metrics)

            # Prepare features and labels
            features = self.prepare_features(df)
            if features.empty:
                return False

            valid_indices = features.index
            labels = self.prepare_labels(df, valid_indices)
            if labels.empty:
                return False

            # Ensure features and labels have the same length
            features = features[:-1]

            # Check if we have enough data
            if len(features) < 30:
                print("Not enough data for training")
                return False

            # Scale features
            scaled_features = self.scaler.fit_transform(features)

            # Train classification model
            self.model.fit(scaled_features, labels)
            return True

        except Exception as e:
            print(f"Error in training: {str(e)}")
            return False

    def predict(self, df):
        """Make trading predictions with confidence scores"""
        try:
            features = self.prepare_features(df)
            if features.empty:
                return pd.Series(0.5, index=df.index)

            scaled_features = self.scaler.transform(features)

            # Get class probabilities
            probas = self.model.predict_proba(scaled_features)
            predictions = pd.Series(index=df.index, dtype=float)

            if probas.shape[1] == 2:
                predictions[features.index] = probas[:, 1]
            else:
                predictions[features.index] = self.model.predict(scaled_features).astype(float)

            predictions.fillna(0.5, inplace=True)
            return predictions

        except Exception as e:
            print(f"Error in prediction: {e}")
            return pd.Series(0.5, index=df.index)

    def handle_websocket_error(self, e: Exception):
        """Gestisce errori WebSocket con retry exponenziale"""
        max_retries = 5
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                print(f"Tentativo riconnessione WebSocket {attempt + 1}/{max_retries}")
                if self.reconnect_websocket():
                    return True
                retry_delay *= 2  # Exponential backoff
                time.sleep(retry_delay)
            except Exception as conn_error:
                print(f"Errore riconnessione: {str(conn_error)}")
                
        return False
        
    def reconnect_websocket(self):
        """Riconnette il WebSocket"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Implementa logica di riconnessione
                return True
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise e
                time.sleep(2)
        return False

    def get_feature_importance(self):
        """Get feature importance from both models"""
        try:
            importance_dict = {
                'classification': dict(zip(self.feature_names, self.model.feature_importances_)),
                'prediction': self.prediction_model.get_feature_importance()
            }
            return importance_dict
        except Exception as e:
            print(f"Error getting feature importance: {e}")
            return None