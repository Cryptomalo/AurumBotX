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
        features = pd.DataFrame(index=df.index)

        # Technical indicators as features
        features['SMA_ratio'] = df['Close'] / df['SMA_20']
        features['RSI'] = df['RSI']
        features['MACD'] = df['MACD']
        features['Volume'] = df['Volume']

        # Price changes
        features['price_change'] = df['Close'].pct_change()
        features['price_volatility'] = df['Close'].rolling(window=20).std()

        # Remove NaN values but keep track of valid indices
        features = features.dropna()
        return features

    def prepare_labels(self, df, valid_indices):
        """Create labels for training (1 for price increase, 0 for decrease)"""
        future_returns = df['Close'].shift(-1) / df['Close'] - 1
        # Align labels with features using the same indices
        labels = future_returns.loc[valid_indices]
        return labels[:-1].astype(int)  # Remove last row and convert to int

    def train(self, df):
        """Train the trading model"""
        # Prepare features and keep track of valid indices
        features = self.prepare_features(df)
        valid_indices = features.index

        # Prepare labels using the same indices
        labels = self.prepare_labels(df, valid_indices)

        # Ensure features and labels have the same length
        features = features[:-1]  # Remove last row to match labels

        # Scale features
        scaled_features = self.scaler.fit_transform(features)

        # Train model
        self.model.fit(scaled_features, labels)

    def predict(self, df):
        """Make trading predictions"""
        features = self.prepare_features(df)
        scaled_features = self.scaler.transform(features)
        return self.model.predict_proba(scaled_features)[:, 1]