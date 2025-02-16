import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib

logger = logging.getLogger(__name__)

class LearningModule:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.min_training_samples = 1000
        self.training_data = []
        
    def add_trade_result(self, trade_data: Dict[str, Any]):
        """Add trade result to training data"""
        try:
            if not trade_data.get('success'):
                return
                
            features = {
                'price': trade_data.get('price', 0),
                'volume': trade_data.get('volume', 0),
                'volatility': trade_data.get('volatility', 0),
                'rsi': trade_data.get('indicators', {}).get('rsi', 50),
                'macd': trade_data.get('indicators', {}).get('macd', 0),
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
        """Train model on collected data"""
        try:
            if len(self.training_data) < self.min_training_samples:
                return False
                
            df = pd.DataFrame(self.training_data)
            
            # Prepare features and target
            X = df.drop(['success', 'profit_ratio'], axis=1)
            y = df['success']
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled, y)
            
            # Update feature importance
            self.feature_importance = dict(zip(X.columns, self.model.feature_importances_))
            
            self.logger.info("Model trained successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error training model: {str(e)}")
            return False
            
    def predict_success_probability(self, trade_features: Dict[str, float]) -> float:
        """Predict probability of trade success"""
        try:
            features = pd.DataFrame([trade_features])
            features_scaled = self.scaler.transform(features)
            
            # Get probability of success
            probabilities = self.model.predict_proba(features_scaled)
            
            # Return probability of success (class 1)
            return float(probabilities[0][1])
            
        except Exception as e:
            self.logger.error(f"Prediction error: {str(e)}")
            return 0.5  # Return neutral probability on error
            
    def save_model(self, path: str):
        """Save model and scaler to disk"""
        try:
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_importance': self.feature_importance
            }, path)
            self.logger.info(f"Model saved to {path}")
            
        except Exception as e:
            self.logger.error(f"Error saving model: {str(e)}")
            
    def load_model(self, path: str):
        """Load model and scaler from disk"""
        try:
            saved_data = joblib.load(path)
            self.model = saved_data['model']
            self.scaler = saved_data['scaler']
            self.feature_importance = saved_data['feature_importance']
            self.logger.info(f"Model loaded from {path}")
            
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
