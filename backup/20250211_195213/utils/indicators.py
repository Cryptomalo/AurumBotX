import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, Union, List, Tuple
from dataclasses import dataclass

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
    """Advanced technical indicators calculator with optimized performance"""

    def __init__(self):
        self.cache = {}
        self.trend_indicators = ['SMA', 'EMA', 'MACD']
        self.momentum_indicators = ['RSI', 'Stochastic', 'MFI']
        self.volatility_indicators = ['BB', 'ATR', 'KC']
        self.volume_indicators = ['OBV', 'ADL', 'CMF']

    def get_trading_signals(self, df: pd.DataFrame) -> List[Dict]:
        """Generate trading signals based on technical analysis"""
        try:
            signals = []
            current_price = df['Close'].iloc[-1]

            # Check RSI conditions
            if 'RSI_14' in df.columns:
                rsi = df['RSI_14'].iloc[-1]
                if rsi < 30:
                    signals.append({
                        'type': 'BUY',
                        'indicator': 'RSI',
                        'strength': 0.7,
                        'price': current_price
                    })
                elif rsi > 70:
                    signals.append({
                        'type': 'SELL',
                        'indicator': 'RSI',
                        'strength': 0.7,
                        'price': current_price
                    })

            # Check MACD crossover
            if all(col in df.columns for col in ['MACD', 'MACD_Signal']):
                macd = df['MACD'].iloc[-2:]
                signal = df['MACD_Signal'].iloc[-2:]

                if macd.iloc[0] < signal.iloc[0] and macd.iloc[1] > signal.iloc[1]:
                    signals.append({
                        'type': 'BUY',
                        'indicator': 'MACD',
                        'strength': 0.8,
                        'price': current_price
                    })
                elif macd.iloc[0] > signal.iloc[0] and macd.iloc[1] < signal.iloc[1]:
                    signals.append({
                        'type': 'SELL',
                        'indicator': 'MACD',
                        'strength': 0.8,
                        'price': current_price
                    })

            return signals
        except Exception as e:
            logger.error(f"Error generating trading signals: {str(e)}")
            return []

    def add_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add all technical indicators with optimization"""
        try:
            df = df.copy()

            # Basic price and volume metrics
            df['Returns'] = df['Close'].pct_change()
            df['Log_Returns'] = np.log1p(df['Returns'])
            df['Volatility'] = self.calculate_volatility(df)

            # Volume analysis
            if 'Volume' in df.columns:
                df = self.add_volume_indicators(df)

            # Trend indicators
            df = self.add_trend_indicators(df)

            # Momentum indicators
            df = self.add_momentum_indicators(df)

            # Volatility indicators
            df = self.add_volatility_indicators(df)

            # Advanced patterns
            df = self.add_candlestick_patterns(df)

            # Support and Resistance
            support, resistance = self.calculate_support_resistance(df)
            df['Support'] = support
            df['Resistance'] = resistance

            # Market condition
            df['Market_Condition'] = self.determine_market_condition(df)

            # Clean up NaN values with forward fill then backward fill
            df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)

            return df

        except Exception as e:
            logger.error(f"Error adding indicators: {e}")
            return df

    def add_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add comprehensive trend indicators"""
        try:
            # Multiple timeframe Moving Averages
            periods = [20, 50, 100, 200]
            for period in periods:
                df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
                df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()

            # MACD calculation
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

            return df

        except Exception as e:
            logger.error(f"Error adding trend indicators: {e}")
            return df

    def add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum indicators"""
        try:
            # RSI with multiple timeframes
            for period in [14, 28]:
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                df[f'RSI_{period}'] = 100 - (100 / (1 + rs))

            return df

        except Exception as e:
            logger.error(f"Error adding momentum indicators: {e}")
            return df

    def add_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility based indicators"""
        try:
            # Bollinger Bands
            sma = df['Close'].rolling(window=20).mean()
            std = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = sma + (std * 2)
            df['BB_Middle'] = sma
            df['BB_Lower'] = sma - (std * 2)

            # Average True Range
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            df['ATR'] = true_range.rolling(14).mean()

            return df

        except Exception as e:
            logger.error(f"Error adding volatility indicators: {e}")
            return df

    def add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume based indicators"""
        try:
            # On Balance Volume
            df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()

            # Volume Profile
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']

            return df

        except Exception as e:
            logger.error(f"Error adding volume indicators: {e}")
            return df

    def add_candlestick_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add candlestick pattern recognition"""
        try:
            # Simple pattern detection
            df['Doji'] = ((np.abs(df['Open'] - df['Close']) <= 
                          (df['High'] - df['Low']) * 0.1)).astype(int)

            return df

        except Exception as e:
            logger.error(f"Error adding candlestick patterns: {e}")
            return df

    def calculate_support_resistance(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """Calculate dynamic support and resistance levels"""
        try:
            window = 20
            rolling_min = df['Low'].rolling(window=window, center=True).min()
            rolling_max = df['High'].rolling(window=window, center=True).max()

            # Identify support levels
            support = rolling_min.where(
                (df['Low'] == rolling_min) & 
                (df['Low'].shift(1) > rolling_min) & 
                (df['Low'].shift(-1) > rolling_min)
            )

            # Identify resistance levels
            resistance = rolling_max.where(
                (df['High'] == rolling_max) & 
                (df['High'].shift(1) < rolling_max) & 
                (df['High'].shift(-1) < rolling_max)
            )

            return support.fillna(method='ffill'), resistance.fillna(method='ffill')

        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return pd.Series(), pd.Series()

    def calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """Calculate overall trend strength"""
        try:
            # Moving Average alignment strength
            ma_alignment = self._calculate_ma_alignment(df)

            # Trend momentum from MACD
            if 'MACD' in df.columns:
                macd_strength = abs(df['MACD'].iloc[-1]) / df['Close'].iloc[-1]
            else:
                macd_strength = 0.5

            # Combine indicators
            trend_strength = np.mean([
                ma_alignment,
                min(macd_strength * 10, 1)  # Normalize MACD strength
            ])

            return float(min(max(trend_strength, 0), 1))

        except Exception as e:
            logger.error(f"Error calculating trend strength: {e}")
            return 0.5

    def _calculate_ma_alignment(self, df: pd.DataFrame) -> float:
        """Calculate moving average alignment strength"""
        try:
            if not all(col in df.columns for col in ['SMA_20', 'SMA_50', 'SMA_200']):
                return 0.5

            current_price = df['Close'].iloc[-1]
            ma_20 = df['SMA_20'].iloc[-1]
            ma_50 = df['SMA_50'].iloc[-1]
            ma_200 = df['SMA_200'].iloc[-1]

            # Check alignment
            bullish_alignment = (current_price > ma_20 > ma_50 > ma_200)
            bearish_alignment = (current_price < ma_20 < ma_50 < ma_200)

            if bullish_alignment or bearish_alignment:
                return 1.0

            # Partial alignment
            partial_score = sum([
                0.3 if current_price > ma_20 else 0,
                0.3 if ma_20 > ma_50 else 0,
                0.4 if ma_50 > ma_200 else 0
            ])

            return partial_score

        except Exception as e:
            logger.error(f"Error calculating MA alignment: {e}")
            return 0.5

    def determine_market_condition(self, df: pd.DataFrame) -> str:
        """Determine overall market condition"""
        try:
            # Trend analysis
            trend = self._determine_trend(df)
            trend_strength = self.calculate_trend_strength(df)

            # Volatility
            volatility = df['Volatility'].iloc[-1]

            # Volume profile
            volume_profile = self._analyze_volume_profile(df)

            return f"{trend}_{trend_strength:.2f}_{volume_profile}"

        except Exception as e:
            logger.error(f"Error determining market condition: {e}")
            return "unknown"

    def _determine_trend(self, df: pd.DataFrame) -> str:
        """Determine market trend direction"""
        try:
            if not all(col in df.columns for col in ['SMA_20', 'SMA_50', 'MACD']):
                return 'sideways'

            # Use multiple indicators for trend determination
            sma_20 = df['SMA_20'].iloc[-1]
            sma_50 = df['SMA_50'].iloc[-1]
            current_price = df['Close'].iloc[-1]
            macd = df['MACD'].iloc[-1]

            if current_price > sma_20 > sma_50 and macd > 0:
                return 'bullish'
            elif current_price < sma_20 < sma_50 and macd < 0:
                return 'bearish'

            return 'sideways'

        except Exception as e:
            logger.error(f"Error determining trend: {e}")
            return 'sideways'

    def _analyze_volume_profile(self, df: pd.DataFrame) -> str:
        """Analyze volume profile"""
        try:
            if 'Volume_Ratio' not in df.columns:
                return 'normal'

            volume_ratio = df['Volume_Ratio'].iloc[-1]

            if volume_ratio > 2.0:
                return 'high'
            elif volume_ratio < 0.5:
                return 'low'
            else:
                return 'normal'

        except Exception as e:
            logger.error(f"Error analyzing volume profile: {e}")
            return 'normal'

    def calculate_volatility(self, df: pd.DataFrame) -> pd.Series:
        """Calculate historical volatility"""
        try:
            # Exponentially weighted volatility
            return df['Returns'].ewm(span=20).std() * np.sqrt(252)

        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return pd.Series(0, index=df.index)