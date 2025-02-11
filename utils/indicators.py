import pandas as pd
import numpy as np

class TechnicalIndicators:
    @staticmethod
    def add_sma(df, period=20):
        """Add Simple Moving Average"""
        df = df.copy()
        df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
        return df

    @staticmethod
    def add_ema(df, period=20):
        """Add Exponential Moving Average"""
        df = df.copy()
        df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()
        return df

    @staticmethod
    def add_rsi(df, period=14):
        """Add Relative Strength Index"""
        try:
            df = df.copy()
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            df = df.assign(RSI=rsi.fillna(50).clip(0, 100))
            return df
        except Exception as e:
            print(f"Error calculating RSI: {str(e)}")
            df = df.assign(RSI=50)
            return df

    @staticmethod
    def add_macd(df, fast=12, slow=26, signal=9):
        """Add MACD indicator"""
        try:
            df = df.copy()
            exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
            exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=signal, adjust=False).mean()
            df = df.assign(
                MACD=macd.fillna(0),
                Signal=signal_line.fillna(0)
            )
            return df
        except Exception as e:
            print(f"Error calculating MACD: {str(e)}")
            df = df.assign(MACD=0, Signal=0)
            return df
