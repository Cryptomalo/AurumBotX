import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, Union, List

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """Advanced technical indicators calculator with optimized performance"""

    def __init__(self):
        self.cache = {}

    def add_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add RSI to the dataframe"""
        try:
            df = df.copy()
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))
            return df
        except Exception as e:
            logger.error(f"Error adding RSI: {e}", exc_info=True)
            return df

    def add_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add MACD components to the dataframe"""
        try:
            df = df.copy()
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Hist'] = df['MACD'] - df['Signal']
            return df
        except Exception as e:
            logger.error(f"Error adding MACD: {e}", exc_info=True)
            return df

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> Optional[float]:
        """Calculate RSI with error handling"""
        try:
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}", exc_info=True)
            return 50.0

    @staticmethod
    def calculate_macd(df: pd.DataFrame) -> Dict[str, float]:
        """Calculate MACD components with error handling"""
        try:
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            histogram = macd - signal

            return {
                'macd': float(macd.iloc[-1]),
                'signal': float(signal.iloc[-1]),
                'histogram': float(histogram.iloc[-1])
            }
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}", exc_info=True)
            return {'macd': 0.0, 'signal': 0.0, 'histogram': 0.0}

    @staticmethod
    def add_sma(df: pd.DataFrame, periods: Union[int, List[int]] = 20) -> pd.DataFrame:
        """Add Simple Moving Averages for multiple periods"""
        try:
            df = df.copy()
            if isinstance(periods, int):
                periods = [periods]

            for period in periods:
                df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()

            return df
        except Exception as e:
            logger.error(f"Error adding SMA: {e}", exc_info=True)
            return df

    @staticmethod
    def add_ema(df: pd.DataFrame, periods: Union[int, List[int]] = 20) -> pd.DataFrame:
        """Add Exponential Moving Averages for multiple periods"""
        try:
            df = df.copy()
            if isinstance(periods, int):
                periods = [periods]

            for period in periods:
                df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()

            return df
        except Exception as e:
            logger.error(f"Error adding EMA: {e}", exc_info=True)
            return df

    def calculate_bollinger_bands(
        self,
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        try:
            middle = df['Close'].rolling(window=period).mean()
            std = df['Close'].rolling(window=period).std()
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)

            return {
                'middle': middle,
                'upper': upper,
                'lower': lower
            }
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}", exc_info=True)
            return {
                'middle': pd.Series(),
                'upper': pd.Series(),
                'lower': pd.Series()
            }

    def calculate_momentum(
        self,
        df: pd.DataFrame,
        period: int = 14
    ) -> Optional[float]:
        """Calculate momentum indicator"""
        try:
            return float(df['Close'].iloc[-1] - df['Close'].iloc[-period])
        except Exception as e:
            logger.error(f"Error calculating momentum: {e}", exc_info=True)
            return 0.0

    def add_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add all technical indicators with optimization"""
        try:
            df = df.copy()

            # Basic price indicators
            df['Returns'] = df['Close'].pct_change()
            df['Volatility'] = df['Returns'].rolling(window=20).std()

            # Volume indicators
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']

            # Moving averages
            periods = [20, 50, 200]
            df = self.add_sma(df, periods)
            df = self.add_ema(df, periods)

            # RSI
            df = self.add_rsi(df)

            # MACD
            df = self.add_macd(df)

            # Bollinger Bands
            bb = self.calculate_bollinger_bands(df)
            if bb:
                df['BB_Middle'] = bb['middle']
                df['BB_Upper'] = bb['upper']
                df['BB_Lower'] = bb['lower']

            # Momentum
            df['Momentum'] = df['Close'].diff(14)

            # Clean up NaN values
            df = df.fillna(method='bfill').fillna(method='ffill').fillna(0)

            return df

        except Exception as e:
            logger.error(f"Error adding indicators: {e}", exc_info=True)
            return df

    def get_trading_signals(self, df: pd.DataFrame) -> Dict[str, str]:
        """Generate trading signals based on technical indicators"""
        try:
            signals = {}

            # RSI signals
            rsi = df['RSI'].iloc[-1]
            if rsi < 30:
                signals['RSI'] = 'Oversold'
            elif rsi > 70:
                signals['RSI'] = 'Overbought'
            else:
                signals['RSI'] = 'Neutral'

            # MACD signals
            if df['MACD'].iloc[-1] > df['Signal'].iloc[-1]:
                signals['MACD'] = 'Bullish'
            else:
                signals['MACD'] = 'Bearish'

            # Trend signals based on moving averages
            current_price = df['Close'].iloc[-1]
            sma_200 = df['SMA_200'].iloc[-1]
            sma_50 = df['SMA_50'].iloc[-1]

            if current_price > sma_200 and sma_50 > sma_200:
                signals['Trend'] = 'Strong Bullish'
            elif current_price < sma_200 and sma_50 < sma_200:
                signals['Trend'] = 'Strong Bearish'
            else:
                signals['Trend'] = 'Mixed'

            return signals

        except Exception as e:
            logger.error(f"Error generating trading signals: {e}", exc_info=True)
            return {'Error': 'Unable to generate signals'}