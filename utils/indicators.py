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
    # Patch numpy NaN before importing pandas_ta
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
    """Advanced technical indicators calculator with optimized performance using pandas-ta"""

    def __init__(self):
        self.cache = {}
        # Custom indicator settings
        self.indicator_settings = {
            'trend': {
                'ema_lengths': [20, 50, 100, 200],
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9
            },
            'momentum': {
                'rsi_length': 14,
                'stoch_length': 14,
                'willr_length': 14
            },
            'volatility': {
                'bbands_length': 20,
                'bbands_std': 2,
                'atr_length': 14
            },
            'volume': {
                'vwap_anchor': 'D',  # Daily anchor
                'obv_length': 20,
                'pvt_length': 20
            }
        }

    def add_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add all technical indicators with optimization using pandas_ta"""
        try:
            df = df.copy()

            # Initialize strategy with all indicators
            strategy = ta.Strategy(
                name="full_suite",
                ta=[
                    # Trend
                    {"kind": "ema", "length": l} for l in self.indicator_settings['trend']['ema_lengths']
                ] + [
                    {"kind": "macd", "fast": self.indicator_settings['trend']['macd_fast'],
                     "slow": self.indicator_settings['trend']['macd_slow'],
                     "signal": self.indicator_settings['trend']['macd_signal']},
                    # Momentum
                    {"kind": "rsi", "length": self.indicator_settings['momentum']['rsi_length']},
                    {"kind": "stoch", "length": self.indicator_settings['momentum']['stoch_length']},
                    {"kind": "willr", "length": self.indicator_settings['momentum']['willr_length']},
                    # Volatility
                    {"kind": "bbands", "length": self.indicator_settings['volatility']['bbands_length'],
                     "std": self.indicator_settings['volatility']['bbands_std']},
                    {"kind": "atr", "length": self.indicator_settings['volatility']['atr_length']},
                    # Volume
                    {"kind": "obv"},
                    {"kind": "pvt"},
                    {"kind": "vwap", "anchor": self.indicator_settings['volume']['vwap_anchor']}
                ]
            )

            # Calculate all indicators
            df.ta.strategy(strategy)

            # Add custom calculations
            df['Volatility'] = self.calculate_volatility(df)
            support, resistance = self.calculate_support_resistance(df)
            df['Support'] = support
            df['Resistance'] = resistance
            df['Market_Condition'] = self.determine_market_condition(df)

            # Clean up NaN values
            df = df.fillna(method='ffill').fillna(method='bfill').fillna(np.nan)

            return df

        except Exception as e:
            logger.error(f"Error adding indicators: {e}")
            return df

    def get_trading_signals(self, df: pd.DataFrame) -> List[Dict]:
        """Generate enhanced trading signals using multiple indicators"""
        try:
            signals = []
            current_price = df['close'].iloc[-1]

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
            if all(col in df.columns for col in ['MACD_12_26_9', 'MACDs_12_26_9']):
                macd = df['MACD_12_26_9'].iloc[-2:]
                signal = df['MACDs_12_26_9'].iloc[-2:]
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
            if all(col in df.columns for col in ['BBL_20_2.0', 'BBU_20_2.0']):
                bb_lower = df['BBL_20_2.0'].iloc[-1]
                bb_upper = df['BBU_20_2.0'].iloc[-1]

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

    def calculate_volatility(self, df: pd.DataFrame) -> pd.Series:
        """Calculate advanced volatility metrics"""
        try:
            # Use True Range based volatility
            if 'ATR_14' in df.columns:
                return df['ATR_14'] / df['Close']
            else:
                # Fallback to traditional volatility calculation
                returns = df['Close'].pct_change()
                return returns.ewm(span=20).std() * np.sqrt(252)
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return pd.Series(0, index=df.index)

    def calculate_support_resistance(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """Calculate dynamic support and resistance using fractals and pivot points"""
        try:
            # Pivot Points
            high = df['High'].rolling(window=20, center=True).max()
            low = df['Low'].rolling(window=20, center=True).min()
            close = df['Close']

            pivot = (high + low + close) / 3
            support1 = 2 * pivot - high
            resistance1 = 2 * pivot - low

            # Fractals
            support_fractals = low.where(
                (df['Low'].shift(2) > df['Low'].shift(1)) &
                (df['Low'].shift(1) > df['Low']) &
                (df['Low'] < df['Low'].shift(-1)) &
                (df['Low'].shift(-1) < df['Low'].shift(-2))
            )

            resistance_fractals = high.where(
                (df['High'].shift(2) < df['High'].shift(1)) &
                (df['High'].shift(1) < df['High']) &
                (df['High'] > df['High'].shift(-1)) &
                (df['High'].shift(-1) > df['High'].shift(-2))
            )

            # Combine both methods
            support = ((support_fractals + support1) / 2).ffill()
            resistance = ((resistance_fractals + resistance1) / 2).ffill()

            return support, resistance

        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return pd.Series(), pd.Series()

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
            current_price = df['Close'].iloc[-1]

            # Check EMAs across multiple timeframes
            ema_trends = []
            for length in self.indicator_settings['trend']['ema_lengths']:
                ema_col = f'EMA_{length}'
                if ema_col in df.columns:
                    ema = df[ema_col].iloc[-1]
                    ema_trends.append(current_price > ema)

            # MACD trend
            macd_bullish = False
            if 'MACD_12_26_9' in df.columns:
                macd_bullish = df['MACD_12_26_9'].iloc[-1] > 0

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
            # ADX for trend strength if available
            if 'ADX_14' in df.columns:
                adx = df['ADX_14'].iloc[-1] / 100  # Normalize to 0-1
            else:
                adx = 0.5

            # EMA alignment
            ema_alignment = self._calculate_ma_alignment(df)

            # MACD momentum
            if 'MACD_12_26_9' in df.columns:
                macd = df['MACD_12_26_9'].iloc[-1]
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
            for length in sorted(self.indicator_settings['trend']['ema_lengths']):
                ema_col = f'EMA_{length}'
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