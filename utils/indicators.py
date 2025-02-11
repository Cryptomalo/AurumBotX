import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> float:
        """Calculate RSI for the latest data point"""
        try:
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1])
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            return 50.0

    @staticmethod
    def calculate_macd(df: pd.DataFrame) -> float:
        """Calculate MACD for the latest data point"""
        try:
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            return float(macd.iloc[-1])
        except Exception as e:
            logger.error(f"Error calculating MACD: {str(e)}")
            return 0.0

    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add all technical indicators to the dataframe"""
        try:
            df = df.copy()

            # Calculate RSI
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # Calculate MACD
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

            return df
        except Exception as e:
            logger.error(f"Error adding indicators: {str(e)}")
            return df

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