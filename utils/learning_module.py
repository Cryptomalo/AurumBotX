import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score
import joblib

logger = logging.getLogger(__name__)

class LearningModule:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Initialize both RandomForest and GradientBoosting for ensemble
        self.rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.gb_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.metrics_history = []
        self.min_training_samples = 1000
        self.training_data = []
        self.models_trained = False

    def add_trade_result(self, trade_data: Dict[str, Any]):
        """Aggiunge risultato trade ai dati di training con validazione avanzata"""
        try:
            if not isinstance(trade_data, dict):
                self.logger.error("Invalid trade data format")
                return

            # Validazione e normalizzazione avanzata dei dati
            features = self._validate_and_normalize_features(trade_data)
            if not features:
                return

            self.training_data.append(features)
            self.logger.info(f"Added trade result to training data. Total samples: {len(self.training_data)}")

            # Riaddestra il modello se abbiamo abbastanza dati nuovi
            if len(self.training_data) % 10 == 0:
                self.train_model()

        except Exception as e:
            self.logger.error(f"Error adding trade result: {str(e)}")

    def _validate_and_normalize_features(self, trade_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """Validazione e normalizzazione avanzata delle features"""
        try:
            required_fields = {
                'price', 'volume', 'volatility', 'rsi', 'macd', 
                'sentiment_score', 'viral_score', 'holder_count', 
                'liquidity', 'confidence', 'success', 'momentum'
            }

            if missing_fields := required_fields - trade_data.keys():
                self.logger.error(f"Missing required fields: {missing_fields}")
                return None

            features = {
                'price': float(trade_data['price']),
                'volume': float(trade_data['volume']),
                'volatility': float(trade_data['volatility']),
                'rsi': float(trade_data['rsi']),
                'macd': float(trade_data['macd']),
                'sentiment_score': float(trade_data['sentiment_score']),
                'viral_score': float(trade_data['viral_score']),
                'holder_count': float(trade_data['holder_count']),
                'liquidity': float(trade_data['liquidity']),
                'confidence': float(trade_data['confidence']),
                'momentum': float(trade_data['momentum']),
                'success': int(bool(trade_data['success'])),
                'profit_ratio': self._calculate_profit_ratio(trade_data)
            }

            # Validazione valori
            if any(np.isnan(value) or np.isinf(value) for value in features.values()):
                self.logger.error("Invalid feature values detected")
                return None

            return features

        except Exception as e:
            self.logger.error(f"Error in feature validation: {str(e)}")
            return None

    def _calculate_profit_ratio(self, trade_data: Dict[str, Any]) -> float:
        """Calcola il profit ratio con gestione degli errori migliorata"""
        try:
            price = float(trade_data.get('price', 0))
            take_profit = float(trade_data.get('take_profit', 0))

            if price <= 0:
                return 0.0

            return (take_profit - price) / price

        except Exception as e:
            self.logger.error(f"Error calculating profit ratio: {str(e)}")
            return 0.0

    def train_model(self) -> bool:
        """Addestra modello ensemble con metriche di performance avanzate"""
        try:
            if not self.training_data:
                self.logger.error("No training data available")
                return False

            min_samples = 50 if len(self.training_data) < self.min_training_samples else self.min_training_samples
            if len(self.training_data) < min_samples:
                self.logger.warning(f"Insufficient training data: {len(self.training_data)} < {min_samples}")
                return False

            df = pd.DataFrame(self.training_data)
            class_counts = df['success'].value_counts()
            self.logger.info(f"Class distribution: {class_counts.to_dict()}")

            if len(class_counts) < 2:
                self.logger.error("Insufficient class diversity in training data")
                return False

            # Prepara features e target
            X = df.drop(['success', 'profit_ratio'], axis=1)
            y = df['success']

            if X.isnull().any().any() or y.isnull().any():
                self.logger.error("Training data contains null values")
                return False

            # Scala features
            X_scaled = self.scaler.fit_transform(X)

            # Addestra modelli
            self.rf_model.fit(X_scaled, y)
            self.gb_model.fit(X_scaled, y)

            # Calcola e salva metriche di performance
            y_pred_rf = self.rf_model.predict(X_scaled)
            y_pred_gb = self.gb_model.predict(X_scaled)

            metrics = {
                'timestamp': datetime.now().isoformat(),
                'rf_precision': precision_score(y, y_pred_rf),
                'rf_recall': recall_score(y, y_pred_rf),
                'rf_f1': f1_score(y, y_pred_rf),
                'gb_precision': precision_score(y, y_pred_gb),
                'gb_recall': recall_score(y, y_pred_gb),
                'gb_f1': f1_score(y, y_pred_gb)
            }

            self.metrics_history.append(metrics)

            # Aggiorna feature importance
            self._update_feature_importance(X.columns)

            self.models_trained = True
            self.logger.info("Models trained successfully")
            self.logger.info(f"Performance metrics: {metrics}")

            return True

        except Exception as e:
            self.logger.error(f"Error training model: {str(e)}")
            return False

    def _update_feature_importance(self, feature_names):
        """Aggiorna feature importance con media pesata dei modelli"""
        try:
            rf_importance = dict(zip(feature_names, self.rf_model.feature_importances_))
            gb_importance = dict(zip(feature_names, self.gb_model.feature_importances_))

            self.feature_importance = {
                feature: 0.6 * rf_importance[feature] + 0.4 * gb_importance[feature]
                for feature in feature_names
            }

        except Exception as e:
            self.logger.error(f"Error updating feature importance: {str(e)}")

    def predict_success_probability(self, trade_features: Dict[str, float]) -> float:
        """Predice probabilità di successo con validazione avanzata"""
        try:
            if not self.models_trained:
                self.logger.warning("Models not trained yet, returning default probability")
                return 0.5

            # Validazione input
            validated_features = self._validate_prediction_features(trade_features)
            if validated_features is None:
                return 0.5

            features_scaled = self.scaler.transform(validated_features)

            # Predizioni ensemble
            rf_prob = self.rf_model.predict_proba(features_scaled)[0][1]
            gb_prob = self.gb_model.predict_proba(features_scaled)[0][1]

            # Media pesata con confidence adjustment
            ensemble_prob = 0.6 * rf_prob + 0.4 * gb_prob
            confidence_adj = self._calculate_confidence_adjustment(trade_features)

            final_prob = ensemble_prob * confidence_adj

            self.logger.info(f"Predicted success probability: {final_prob:.2f}")
            return float(final_prob)

        except Exception as e:
            self.logger.error(f"Prediction error: {e}")
            return 0.5

    def _validate_prediction_features(self, features: Dict[str, float]) -> Optional[pd.DataFrame]:
        """Validate features for prediction with improved error handling"""
        try:
            required_features = {
                'price', 'volume', 'volatility', 'rsi', 'macd',
                'sentiment_score', 'viral_score', 'holder_count',
                'liquidity', 'confidence', 'momentum'
            }

            if missing := required_features - features.keys():
                logger.error(f"Missing required features: {missing}")
                return None

            df = pd.DataFrame([features])

            # Use numpy's isinf and isnan for validation
            if df.isnull().any().any() or np.isinf(df.values).any():
                logger.error("Invalid feature values detected")
                return None

            return df

        except Exception as e:
            logger.error(f"Feature validation error: {e}")
            return None

    def get_model_metrics(self) -> Dict[str, Any]:
        """Ritorna le metriche di performance del modello"""
        if not self.metrics_history:
            return {}

        latest_metrics = self.metrics_history[-1]
        return {
            'timestamp': latest_metrics['timestamp'],
            'rf_metrics': {
                'precision': latest_metrics['rf_precision'],
                'recall': latest_metrics['rf_recall'],
                'f1': latest_metrics['rf_f1']
            },
            'gb_metrics': {
                'precision': latest_metrics['gb_precision'],
                'recall': latest_metrics['gb_recall'],
                'f1': latest_metrics['gb_f1']
            }
        }

    def save_model(self, path: str):
        """Salva modello con metriche e configurazione"""
        try:
            joblib.dump({
                'rf_model': self.rf_model,
                'gb_model': self.gb_model,
                'scaler': self.scaler,
                'feature_importance': self.feature_importance,
                'metrics_history': self.metrics_history,
                'models_trained': self.models_trained
            }, path)
            self.logger.info(f"Model saved to {path}")

        except Exception as e:
            self.logger.error(f"Error saving model: {str(e)}")

    def load_model(self, path: str):
        """Carica modello con metriche e configurazione"""
        try:
            saved_data = joblib.load(path)
            self.rf_model = saved_data['rf_model']
            self.gb_model = saved_data['gb_model']
            self.scaler = saved_data['scaler']
            self.feature_importance = saved_data['feature_importance']
            self.metrics_history = saved_data.get('metrics_history', [])
            self.models_trained = saved_data.get('models_trained', False)
            self.logger.info(f"Model loaded from {path}")

        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")

    def _calculate_confidence_adjustment(self, features: Dict[str, float]) -> float:
        """Calcola fattore di aggiustamento confidenza basato su feature importance"""
        try:
            if not self.feature_importance:
                return 1.0

            total_importance = sum(self.feature_importance.values())
            if total_importance == 0:
                return 1.0

            weighted_score = sum(
                self.feature_importance.get(feature, 0) * features.get(feature, 0) / total_importance
                for feature in self.feature_importance.keys()
            )

            # Normalizza score tra 0.5 e 1.5
            return max(0.5, min(1.5, 1.0 + weighted_score))

        except Exception as e:
            self.logger.error(f"Error calculating confidence adjustment: {str(e)}")
            return 1.0

    def get_important_features(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Ritorna le feature più importanti per il modello"""
        try:
            if not self.feature_importance:
                return []

            sorted_features = sorted(
                self.feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )

            return [
                {'feature': feature, 'importance': importance}
                for feature, importance in sorted_features[:top_n]
            ]

        except Exception as e:
            self.logger.error(f"Error getting important features: {str(e)}")
            return []