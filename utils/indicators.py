import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, Union, List, Tuple
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

# Create numpy compatibility layer
np.NaN = np.nan  # Ensure NaN is available for older code

# Try importing pandas_ta with proper error handling and compatibility fixes
try:
    # Patch numpy NaN before importing pandas_ta (this part is redundant given the numpy compatibility layer above)
    import sys
    import numpy
    sys.modules['numpy'].NaN = numpy.nan

    import pandas_ta as ta
except ImportError as e:
    logger.error(f"Failed to import pandas_ta: {e}")
    raise ImportError("pandas_ta is required but failed to import. Please ensure it's properly installed.")

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

    def add_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add all technical indicators with optimization"""
        try:
            df = df.copy()

            # Verify required columns exist (case-insensitive)
            required_columns = ['close', 'high', 'low', 'open', 'volume']
            existing_columns = [col.lower() for col in df.columns]

            for col in required_columns:
                if col not in existing_columns:
                    upper_col = col.upper()
                    if upper_col in df.columns:
                        df[col] = df[upper_col]
                    else:
                        raise ValueError(f"Missing required column: {col}")

            # Calculate returns first to avoid DataFrame copy warnings
            df['returns'] = df['close'].pct_change()
            df['volatility'] = self.calculate_volatility(df)

            # Add indicators
            df = self.add_volume_indicators(df)
            df = self.add_trend_indicators(df)
            df = self.add_momentum_indicators(df)
            df = self.add_volatility_indicators(df)

            # Support and Resistance
            support, resistance = self.calculate_support_resistance(df)
            df['support'] = support
            df['resistance'] = resistance

            # Market condition
            df['market_condition'] = self.determine_market_condition(df)

            # Add uppercase column names for compatibility
            for col in df.columns:
                df[col.upper()] = df[col]

            return df

        except Exception as e:
            logger.error(f"Error adding indicators: {e}")
            return df

    def add_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add trend indicators"""
        try:
            # Multiple timeframe Moving Averages
            periods = [20, 50, 100, 200]
            for period in periods:
                df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
                df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()

            # MACD
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = exp1 - exp2
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']

            return df

        except Exception as e:
            logger.error(f"Error adding trend indicators: {e}")
            return df

    def add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum indicators"""
        try:
            # RSI
            for period in [14, 28]:
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                df[f'rsi_{period}'] = 100 - (100 / (1 + rs))

            return df

        except Exception as e:
            logger.error(f"Error adding momentum indicators: {e}")
            return df

    def add_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility indicators"""
        try:
            # Bollinger Bands
            sma = df['close'].rolling(window=20).mean()
            std = df['close'].rolling(window=20).std()
            df['bb_upper'] = sma + (std * 2)
            df['bb_middle'] = sma
            df['bb_lower'] = sma - (std * 2)

            # ATR
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            df['atr'] = true_range.rolling(14).mean()

            return df

        except Exception as e:
            logger.error(f"Error adding volatility indicators: {e}")
            return df

    def add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume indicators"""
        try:
            # On Balance Volume
            df['obv'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()

            # Volume Profile
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']

            return df

        except Exception as e:
            logger.error(f"Error adding volume indicators: {e}")
            return df

    def calculate_support_resistance(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """Add support and resistance levels"""
        try:
            window = 20
            df['rolling_min'] = df['low'].rolling(window=window, center=True).min()
            df['rolling_max'] = df['high'].rolling(window=window, center=True).max()

            # Identify support levels
            support = df['rolling_min'].where(
                (df['low'] == df['rolling_min']) &
                (df['low'].shift(1) > df['rolling_min']) &
                (df['low'].shift(-1) > df['rolling_min'])
            ).ffill()

            # Identify resistance levels
            resistance = df['rolling_max'].where(
                (df['high'] == df['rolling_max']) &
                (df['high'].shift(1) < df['rolling_max']) &
                (df['high'].shift(-1) < df['rolling_max'])
            ).ffill()

            return support, resistance

        except Exception as e:
            logger.error(f"Error adding support/resistance levels: {e}")
            return pd.Series(np.nan, index=df.index), pd.Series(np.nan, index=df.index)


    def calculate_volatility(self, df: pd.DataFrame) -> pd.Series:
        """Calculate historical volatility"""
        try:
            return df['returns'].ewm(span=20).std() * np.sqrt(252)
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return pd.Series(0, index=df.index)

    def get_trading_signals(self, df: pd.DataFrame) -> List[Dict]:
        """Generate enhanced trading signals using multiple indicators"""
        try:
            signals = []
            current_price = df['close'].iloc[-1]

            # RSI Signals
            if 'rsi_14' in df.columns:
                rsi = df['rsi_14'].iloc[-1]
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
            if all(col in df.columns for col in ['macd', 'macd_signal']):
                macd = df['macd'].iloc[-2:]
                signal = df['macd_signal'].iloc[-2:]
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
            if all(col in df.columns for col in ['bb_lower', 'bb_upper']):
                bb_lower = df['bb_lower'].iloc[-1]
                bb_upper = df['bb_upper'].iloc[-1]

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

    def determine_market_condition(self, df: pd.DataFrame) -> str:
        """Determine overall market condition using multiple indicators"""
        try:
            trend = self._determine_trend(df)
            trend_strength = self.calculate_trend_strength(df)
            volume_profile = self._analyze_volume_profile(df)

            return f"{trend}_{trend_strength:.2f}_{volume_profile}"

        except Exception as e:
            logger.error(f"Error determining market condition: {e}")
            return "unknown"

    def _determine_trend(self, df: pd.DataFrame) -> str:
        """Enhanced trend determination using multiple timeframes"""
        try:
            current_price = df['close'].iloc[-1]

            # Check EMAs across multiple timeframes
            ema_trends = []
            for length in [20, 50, 100, 200]:
                ema_col = f'ema_{length}'
                if ema_col in df.columns:
                    ema = df[ema_col].iloc[-1]
                    ema_trends.append(current_price > ema)

            # MACD trend
            macd_bullish = False
            if 'macd' in df.columns:
                macd_bullish = df['macd'].iloc[-1] > 0

            # Combine signals
            bullish_count = sum(ema_trends) + macd_bullish
            total_signals = len(ema_trends) + 1

            if bullish_count / total_signals > 0.7:
                return 'bullish'
            elif bullish_count / total_signals < 0.3:
                return 'bearish'
            else:
                return 'sideways'

        except Exception as e:
            logger.error(f"Error determining trend: {e}")
            return 'sideways'

    def calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """Calculate trend strength using multiple indicators"""
        try:
            # ADX for trend strength if available (Not implemented in the edited code, using a default)
            adx = 0.5

            # EMA alignment
            ema_alignment = self._calculate_ma_alignment(df)

            # MACD momentum
            if 'macd' in df.columns:
                macd = df['macd'].iloc[-1]
                macd_strength = min(1, abs(macd) / df['close'].iloc[-1] * 100)
            else:
                macd_strength = 0.5

            # Combine indicators with weights
            trend_strength = (
                adx * 0.4 +
                ema_alignment * 0.4 +
                macd_strength * 0.2
            )

            return float(min(max(trend_strength, 0), 1))

        except Exception as e:
            logger.error(f"Error calculating trend strength: {e}")
            return 0.5

    def _calculate_ma_alignment(self, df: pd.DataFrame) -> float:
        """Calculate moving average alignment strength"""
        try:
            # Get the EMAs
            emas = []
            for length in sorted([20, 50, 100, 200]):
                ema_col = f'ema_{length}'
                if ema_col in df.columns:
                    emas.append(df[ema_col].iloc[-1])

            if len(emas) < 2:
                return 0.5

            # Check if EMAs are properly aligned
            aligned = all(emas[i] > emas[i+1] for i in range(len(emas)-1))
            anti_aligned = all(emas[i] < emas[i+1] for i in range(len(emas)-1))

            if aligned or anti_aligned:
                return 1.0

            # Calculate partial alignment
            pairs_aligned = sum(
                1 for i in range(len(emas)-1)
                if (emas[i] > emas[i+1]) == aligned
            )

            return pairs_aligned / (len(emas) - 1)

        except Exception as e:
            logger.error(f"Error calculating MA alignment: {e}")
            return 0.5

    def _analyze_volume_profile(self, df: pd.DataFrame) -> str:
        """Enhanced volume profile analysis"""
        try:
            if 'volume' not in df.columns:
                return 'normal'

            # Calculate volume metrics
            vol_sma = df['volume'].rolling(window=20).mean()
            current_vol = df['volume'].iloc[-1]
            vol_ratio = current_vol / vol_sma.iloc[-1]

            # Volume trend
            vol_trend = df['volume'].iloc[-5:].mean() > vol_sma.iloc[-5:].mean()

            # Classify volume profile
            if vol_ratio > 2.0 and vol_trend:
                return 'high_increasing'
            elif vol_ratio > 2.0:
                return 'high_stable'
            elif vol_ratio < 0.5 and not vol_trend:
                return 'low_decreasing'
            elif vol_ratio < 0.5:
                return 'low_stable'
            elif vol_trend:
                return 'normal_increasing'
            else:
                return 'normal_stable'

        except Exception as e:
            logger.error(f"Error analyzing volume profile: {e}")
            return 'normal'