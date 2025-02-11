import pandas as pd
import pandas_ta as ta
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
            df['RSI'] = df.ta.rsi(close='Close', length=period)
            return df
        except Exception as e:
            logger.error(f"Error adding RSI: {e}", exc_info=True)
            return df

    def add_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add MACD components to the dataframe"""
        try:
            df = df.copy()
            macd = df.ta.macd(close='Close')
            df['MACD'] = macd['MACD_12_26_9']
            df['Signal'] = macd['MACDs_12_26_9']
            df['MACD_Hist'] = macd['MACDh_12_26_9']
            return df
        except Exception as e:
            logger.error(f"Error adding MACD: {e}", exc_info=True)
            return df

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> Optional[float]:
        """Calculate RSI with error handling"""
        try:
            rsi = df.ta.rsi(close='Close', length=period)
            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}", exc_info=True)
            return 50.0

    @staticmethod
    def calculate_macd(df: pd.DataFrame) -> Dict[str, float]:
        """Calculate MACD components with error handling"""
        try:
            macd = df.ta.macd(close='Close')
            return {
                'macd': float(macd['MACD_12_26_9'].iloc[-1]),
                'signal': float(macd['MACDs_12_26_9'].iloc[-1]),
                'histogram': float(macd['MACDh_12_26_9'].iloc[-1])
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
                df[f'SMA_{period}'] = df.ta.sma(close='Close', length=period)

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
                df[f'EMA_{period}'] = df.ta.ema(close='Close', length=period)

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
            bbands = df.ta.bbands(close='Close', length=period, std=std_dev)
            return {
                'middle': bbands[f'BBM_{period}_{std_dev}'],
                'upper': bbands[f'BBU_{period}_{std_dev}'],
                'lower': bbands[f'BBL_{period}_{std_dev}']
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
            momentum = df.ta.mom(close='Close', length=period)
            return float(momentum.iloc[-1])
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
            if 'Volume' in df.columns:
                df['Volume_MA'] = df.ta.sma(close='Volume', length=20)
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
            df['Momentum'] = df.ta.mom(close='Close', length=14)

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