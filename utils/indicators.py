import pandas as pd
import numpy as np

class TechnicalIndicators:
    @staticmethod
    def add_sma(df, period=20):
        """Add Simple Moving Average"""
        df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
        return df

    @staticmethod
    def add_ema(df, period=20):
        """Add Exponential Moving Average"""
        df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()
        return df

    @staticmethod
    def add_rsi(df, period=14):
        """Add Relative Strength Index"""
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df

    @staticmethod
    def add_macd(df, fast=12, slow=26, signal=9):
        """Add MACD indicator"""
        exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
        return df
