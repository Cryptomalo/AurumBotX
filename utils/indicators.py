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
        try:
            # Calculate price changes
            delta = df['Close'].diff()

            # Separate gains and losses
            gain = delta.copy()
            loss = delta.copy()
            gain[gain < 0] = 0
            loss[loss > 0] = 0
            loss = abs(loss)

            # Calculate average gains and losses
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()

            # Calculate RS and RSI
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # Handle division by zero
            df['RSI'].fillna(50, inplace=True)  # Fill NaN with neutral value
            df['RSI'] = df['RSI'].clip(0, 100)  # Ensure values are between 0 and 100

            return df
        except Exception as e:
            print(f"Error calculating RSI: {str(e)}")
            df['RSI'] = 50  # Set neutral value in case of error
            return df

    @staticmethod
    def add_macd(df, fast=12, slow=26, signal=9):
        """Add MACD indicator"""
        try:
            # Calculate MACD components
            exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
            exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()

            # Fill NaN values
            df['MACD'].fillna(0, inplace=True)
            df['Signal'].fillna(0, inplace=True)

            return df
        except Exception as e:
            print(f"Error calculating MACD: {str(e)}")
            df['MACD'] = 0
            df['Signal'] = 0
            return df