import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
import joblib

logger = logging.getLogger(__name__)

class LearningModule:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Inizializza sia RandomForest che GradientBoosting per ensemble
        self.rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.gb_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.min_training_samples = 1000
        self.training_data = []

    def add_trade_result(self, trade_data: Dict[str, Any]):
        """Aggiunge risultato trade ai dati di training"""
        try:
            if not trade_data.get('success'):
                return

            features = {
                'price': trade_data.get('price', 0),
                'volume': trade_data.get('volume', 0),
                'volatility': trade_data.get('volatility', 0),
                'rsi': trade_data.get('indicators', {}).get('rsi', 50),
                'macd': trade_data.get('indicators', {}).get('macd', 0),
                'sentiment_score': trade_data.get('sentiment', {}).get('score', 0.5),
                'viral_score': trade_data.get('viral_metrics', {}).get('coefficient', 0.5),
                'holder_count': trade_data.get('metrics', {}).get('holders', 0),
                'liquidity': trade_data.get('metrics', {}).get('liquidity', 0),
                'confidence': trade_data.get('confidence', 0.5),
                'success': 1 if trade_data.get('success') else 0,
                'profit_ratio': (trade_data.get('take_profit', 0) - trade_data.get('price', 0)) / 
                               trade_data.get('price', 1) if trade_data.get('price', 0) > 0 else 0
            }

            self.training_data.append(features)
            self.logger.info("Added trade result to training data")

        except Exception as e:
            self.logger.error(f"Error adding trade result: {str(e)}")

    def train_model(self) -> bool:
        """Addestra modello ensemble su dati raccolti"""
        try:
            if len(self.training_data) < self.min_training_samples:
                return False

            df = pd.DataFrame(self.training_data)

            # Prepara features e target
            X = df.drop(['success', 'profit_ratio'], axis=1)
            y = df['success']

            # Scala features
            X_scaled = self.scaler.fit_transform(X)

            # Addestra entrambi i modelli
            self.rf_model.fit(X_scaled, y)
            self.gb_model.fit(X_scaled, y)

            # Aggiorna feature importance
            rf_importance = dict(zip(X.columns, self.rf_model.feature_importances_))
            gb_importance = dict(zip(X.columns, self.gb_model.feature_importances_))

            # Media pesata delle feature importance
            self.feature_importance = {
                feature: 0.6 * rf_importance[feature] + 0.4 * gb_importance[feature]
                for feature in X.columns
            }

            self.logger.info("Models trained successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error training model: {str(e)}")
            return False

    def predict_success_probability(self, trade_features: Dict[str, float]) -> float:
        """Predice probabilità di successo del trade usando ensemble"""
        try:
            features = pd.DataFrame([trade_features])
            features_scaled = self.scaler.transform(features)

            # Combina predizioni dei due modelli
            rf_prob = self.rf_model.predict_proba(features_scaled)[0][1]
            gb_prob = self.gb_model.predict_proba(features_scaled)[0][1]

            # Media pesata (60% RandomForest, 40% GradientBoosting)
            ensemble_prob = 0.6 * rf_prob + 0.4 * gb_prob

            # Aggiusta confidenza basata su feature importance
            confidence_adjustment = self._calculate_confidence_adjustment(trade_features)
            final_prob = ensemble_prob * confidence_adjustment

            self.logger.info(f"Predicted success probability: {final_prob:.2f}")
            return float(final_prob)

        except Exception as e:
            self.logger.error(f"Prediction error: {str(e)}")
            return 0.5  # Probabilità neutra in caso di errore

    def _calculate_confidence_adjustment(self, features: Dict[str, float]) -> float:
        """Calcola fattore di aggiustamento confidenza basato su feature importance"""
        try:
            if not self.feature_importance:
                return 1.0

            total_importance = sum(self.feature_importance.values())
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

    def save_model(self, path: str):
        """Salva modello e scaler su disco"""
        try:
            joblib.dump({
                'rf_model': self.rf_model,
                'gb_model': self.gb_model,
                'scaler': self.scaler,
                'feature_importance': self.feature_importance
            }, path)
            self.logger.info(f"Model saved to {path}")

        except Exception as e:
            self.logger.error(f"Error saving model: {str(e)}")

    def load_model(self, path: str):
        """Carica modello e scaler da disco"""
        try:
            saved_data = joblib.load(path)
            self.rf_model = saved_data['rf_model']
            self.gb_model = saved_data['gb_model']
            self.scaler = saved_data['scaler']
            self.feature_importance = saved_data['feature_importance']
            self.logger.info(f"Model loaded from {path}")

        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")