import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, Union, List, Tuple
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class MarketCondition:
    trend: str  # 'bullish', 'bearish', 'sideways'
    strength: float  # 0-1
    volatility: float
    volume_profile: str
    support_level: float
    resistance_level: float

class TechnicalIndicators:
    """Advanced technical indicators calculator with standardized column names"""

    STANDARD_COLUMNS = ['Open', 'High', 'Low', 'Close', 'Volume']

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.trend_indicators = ['SMA', 'EMA', 'MACD']
        self.momentum_indicators = ['RSI', 'Stochastic', 'MFI']
        self.volatility_indicators = ['BB', 'ATR', 'KC']
        self.volume_indicators = ['OBV', 'Volume_MA', 'Volume_Ratio']

    def add_sma(self, df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """Add Simple Moving Average"""
        try:
            df = df.copy()
            df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
            return df
        except Exception as e:
            self.logger.error(f"Error adding SMA: {str(e)}")
            return df

    def add_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add Relative Strength Index"""
        try:
            df = df.copy()
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            df[f'RSI_{period}'] = 100 - (100 / (1 + rs))
            return df
        except Exception as e:
            self.logger.error(f"Error adding RSI: {str(e)}")
            return df

    def add_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add MACD indicator"""
        try:
            df = df.copy()
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
            return df
        except Exception as e:
            self.logger.error(f"Error adding MACD: {str(e)}")
            return df

    def add_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add all technical indicators with standardized column names"""
        try:
            df = df.copy()

            # Validate required columns
            missing_cols = [col for col in self.STANDARD_COLUMNS if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Basic metrics
            df['Returns'] = df['Close'].pct_change()
            df['Volatility'] = self.calculate_volatility(df)

            # Core indicators with standardized names
            df = self.add_trend_indicators(df)
            df = self.add_momentum_indicators(df)
            df = self.add_volatility_indicators(df)
            if 'Volume' in df.columns:
                df = self.add_volume_indicators(df)

            # Market analysis
            support, resistance = self.calculate_support_resistance(df)
            df['Support'] = support
            df['Resistance'] = resistance
            df['Market_Condition'] = self.determine_market_condition(df)

            # Clean up NaN values using recommended methods
            df = df.ffill()  # Forward fill
            df = df.bfill()  # Backward fill
            df = df.fillna(0)  # Fill remaining NaNs with 0

            return df

        except Exception as e:
            self.logger.error(f"Error adding indicators: {str(e)}")
            return df

    def add_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add trend indicators with standard column names"""
        try:
            # Moving Averages
            periods = [20, 50, 200]
            for period in periods:
                df = self.add_sma(df, period)
                df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()

            # MACD with standard names
            df = self.add_macd(df)

            return df
        except Exception as e:
            logger.error(f"Error adding trend indicators: {str(e)}")
            return df

    def add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum indicators with standard column names"""
        try:
            # RSI
            for period in [14, 28]:
                df = self.add_rsi(df, period)

            return df
        except Exception as e:
            logger.error(f"Error adding momentum indicators: {str(e)}")
            return df

    def add_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility indicators with standard column names"""
        try:
            # Bollinger Bands
            sma = df['Close'].rolling(window=20).mean()
            std = df['Close'].rolling(window=20).std()
            df['BB_Middle'] = sma
            df['BB_Upper'] = sma + (std * 2)
            df['BB_Lower'] = sma - (std * 2)
            df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']

            # ATR
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            df['ATR'] = true_range.rolling(14).mean()

            return df
        except Exception as e:
            logger.error(f"Error adding volatility indicators: {str(e)}")
            return df

    def add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume indicators with standard column names"""
        try:
            # Volume Moving Average
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']

            # On Balance Volume (OBV)
            df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()

            return df
        except Exception as e:
            logger.error(f"Error adding volume indicators: {str(e)}")
            return df

    def calculate_volatility(self, df: pd.DataFrame) -> pd.Series:
        """Calculate historical volatility"""
        try:
            returns = df['Returns'].fillna(0)
            return returns.ewm(span=20).std() * np.sqrt(252)
        except Exception as e:
            logger.error(f"Error calculating volatility: {str(e)}")
            return pd.Series(0, index=df.index)

    def calculate_support_resistance(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """Calculate support and resistance levels"""
        try:
            window = 20
            rolling_min = df['Low'].rolling(window=window, center=True).min()
            rolling_max = df['High'].rolling(window=window, center=True).max()

            support = rolling_min.where(
                (df['Low'] == rolling_min) & 
                (df['Low'].shift(1) > rolling_min) & 
                (df['Low'].shift(-1) > rolling_min)
            )

            resistance = rolling_max.where(
                (df['High'] == rolling_max) & 
                (df['High'].shift(1) < rolling_max) & 
                (df['High'].shift(-1) < rolling_max)
            )

            return support.fillna(method='ffill'), resistance.fillna(method='ffill')
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {str(e)}")
            return pd.Series(index=df.index), pd.Series(index=df.index)

    def determine_market_condition(self, df: pd.DataFrame) -> str:
        """Determine market condition"""
        try:
            sma_20 = df['SMA_20'].iloc[-1] if 'SMA_20' in df.columns else df['Close'].rolling(20).mean().iloc[-1]
            sma_50 = df['SMA_50'].iloc[-1] if 'SMA_50' in df.columns else df['Close'].rolling(50).mean().iloc[-1]
            current_price = df['Close'].iloc[-1]

            if current_price > sma_20 > sma_50:
                trend = "bullish"
            elif current_price < sma_20 < sma_50:
                trend = "bearish"
            else:
                trend = "sideways"

            # Calculate trend strength
            strength = self._calculate_trend_strength(df)

            return f"{trend}_{strength:.2f}"
        except Exception as e:
            logger.error(f"Error determining market condition: {str(e)}")
            return "unknown"

    def _calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """Calculate trend strength"""
        try:
            current_price = df['Close'].iloc[-1]
            if not all(col in df.columns for col in ['SMA_20', 'SMA_50', 'SMA_200']):
                return 0.5

            ma_20 = df['SMA_20'].iloc[-1]
            ma_50 = df['SMA_50'].iloc[-1]
            ma_200 = df['SMA_200'].iloc[-1]

            score = sum([
                0.3 if current_price > ma_20 else 0,
                0.3 if ma_20 > ma_50 else 0,
                0.4 if ma_50 > ma_200 else 0
            ])

            return min(max(score, 0), 1)
        except Exception as e:
            logger.error(f"Error calculating trend strength: {str(e)}")
            return 0.5

    def get_trading_signals(self, df: pd.DataFrame) -> List[Dict]:
        """Generate enhanced trading signals using multiple indicators"""
        try:
            signals = []
            current_price = df['Close'].iloc[-1]

            # RSI Signals
            if 'RSI_14' in df.columns:
                rsi = df['RSI_14'].iloc[-1]
                if rsi < 30:
                    signals.append({
                        'type': 'BUY',
                        'indicator': 'RSI',
                        'strength': 0.7 + (30 - rsi) / 100,  # Increased strength for extreme oversold
                        'price': current_price
                    })
                elif rsi > 70:
                    signals.append({
                        'type': 'SELL',
                        'indicator': 'RSI',
                        'strength': 0.7 + (rsi - 70) / 100,  # Increased strength for extreme overbought
                        'price': current_price
                    })

            # MACD Signals
            if all(col in df.columns for col in ['MACD', 'MACD_Signal']):
                macd = df['MACD'].iloc[-2:]
                signal = df['MACD_Signal'].iloc[-2:]
                hist = macd - signal

                # Calculate signal strength based on histogram size
                strength = min(0.9, 0.7 + abs(hist.iloc[-1]) / current_price)

                if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
                    signals.append({
                        'type': 'BUY',
                        'indicator': 'MACD',
                        'strength': strength,
                        'price': current_price
                    })
                elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] >= signal.iloc[-2]:
                    signals.append({
                        'type': 'SELL',
                        'indicator': 'MACD',
                        'strength': strength,
                        'price': current_price
                    })

            # Bollinger Bands Signals
            if all(col in df.columns for col in ['BB_Lower', 'BB_Upper']):
                bb_lower = df['BB_Lower'].iloc[-1]
                bb_upper = df['BB_Upper'].iloc[-1]

                if current_price < bb_lower:
                    signals.append({
                        'type': 'BUY',
                        'indicator': 'BB',
                        'strength': 0.6,
                        'price': current_price
                    })
                elif current_price > bb_upper:
                    signals.append({
                        'type': 'SELL',
                        'indicator': 'BB',
                        'strength': 0.6,
                        'price': current_price
                    })

            return signals

        except Exception as e:
            logger.error(f"Error generating trading signals: {str(e)}")
            return []