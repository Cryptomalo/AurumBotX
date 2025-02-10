import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

class TradingBot:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100)
        self.scaler = StandardScaler()
        
    def prepare_features(self, df):
        """Prepare features for the model"""
        features = pd.DataFrame()
        
        # Technical indicators as features
        features['SMA_ratio'] = df['Close'] / df['SMA_20']
        features['RSI'] = df['RSI']
        features['MACD'] = df['MACD']
        features['Volume'] = df['Volume']
        
        # Price changes
        features['price_change'] = df['Close'].pct_change()
        features['price_volatility'] = df['Close'].rolling(window=20).std()
        
        return features.dropna()
    
    def prepare_labels(self, df):
        """Create labels for training (1 for price increase, 0 for decrease)"""
        future_returns = df['Close'].shift(-1) / df['Close'] - 1
        return (future_returns > 0).astype(int)
    
    def train(self, df):
        """Train the trading model"""
        features = self.prepare_features(df)
        labels = self.prepare_labels(df)[:-1]  # Remove last row as we don't have future data
        
        # Scale features
        scaled_features = self.scaler.fit_transform(features)
        
        # Train model
        self.model.fit(scaled_features[:-1], labels)
        
    def predict(self, df):
        """Make trading predictions"""
        features = self.prepare_features(df)
        scaled_features = self.scaler.transform(features)
        return self.model.predict_proba(scaled_features)[:, 1]
