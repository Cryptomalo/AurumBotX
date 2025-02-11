import pandas as pd
import pandas_ta as ta
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
                df[f'SMA_{period}'] = ta.sma(df['Close'], length=period)
                df[f'EMA_{period}'] = ta.ema(df['Close'], length=period)

            # MACD with signal and histogram
            macd = ta.macd(df['Close'])
            df['MACD'] = macd['MACD_12_26_9']
            df['MACD_Signal'] = macd['MACDs_12_26_9']
            df['MACD_Hist'] = macd['MACDh_12_26_9']

            # ADX for trend strength
            adx = ta.adx(df['High'], df['Low'], df['Close'])
            df['ADX'] = adx['ADX_14']
            df['DI_plus'] = adx['DMP_14']
            df['DI_minus'] = adx['DMN_14']

            # Ichimoku Cloud
            ichimoku = ta.ichimoku(df['High'], df['Low'], df['Close'])
            for col in ichimoku.columns:
                df[f'Ichimoku_{col}'] = ichimoku[col]

            return df

        except Exception as e:
            logger.error(f"Error adding trend indicators: {e}")
            return df

    def add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum indicators"""
        try:
            # RSI with multiple timeframes
            for period in [14, 28]:
                df[f'RSI_{period}'] = ta.rsi(df['Close'], length=period)

            # Stochastic Oscillator
            stoch = ta.stoch(df['High'], df['Low'], df['Close'])
            df['STOCH_K'] = stoch['STOCHk_14_3_3']
            df['STOCH_D'] = stoch['STOCHd_14_3_3']

            # Money Flow Index
            df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'])

            # Williams %R
            df['WILLIAMS_R'] = ta.willr(df['High'], df['Low'], df['Close'])

            # Commodity Channel Index
            df['CCI'] = ta.cci(df['High'], df['Low'], df['Close'])

            return df

        except Exception as e:
            logger.error(f"Error adding momentum indicators: {e}")
            return df

    def add_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility based indicators"""
        try:
            # Bollinger Bands
            bb = ta.bbands(df['Close'])
            df['BB_Upper'] = bb['BBU_20_2.0']
            df['BB_Middle'] = bb['BBM_20_2.0']
            df['BB_Lower'] = bb['BBL_20_2.0']

            # Average True Range
            df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'])

            # Keltner Channels
            kc = ta.kc(df['High'], df['Low'], df['Close'])
            df['KC_Upper'] = kc['KCUe_20_2']
            df['KC_Middle'] = kc['KCBe_20_2']
            df['KC_Lower'] = kc['KCLe_20_2']

            # Donchian Channels
            dc = ta.donchian(df['High'], df['Low'])
            df['DC_Upper'] = dc['DCU_20_20']
            df['DC_Middle'] = dc['DCM_20_20']
            df['DC_Lower'] = dc['DCL_20_20']

            return df

        except Exception as e:
            logger.error(f"Error adding volatility indicators: {e}")
            return df

    def add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume based indicators"""
        try:
            # On Balance Volume
            df['OBV'] = ta.obv(df['Close'], df['Volume'])

            # Accumulation/Distribution Line
            df['ADL'] = ta.ad(df['High'], df['Low'], df['Close'], df['Volume'])

            # Chaikin Money Flow
            df['CMF'] = ta.cmf(df['High'], df['Low'], df['Close'], df['Volume'])

            # Volume Weighted Average Price
            df['VWAP'] = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])

            # Elder Force Index
            df['EFI'] = ta.efi(df['Close'], df['Volume'])

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
            # Bullish patterns
            df['Hammer'] = ta.cdl_pattern(df['Open'], df['High'], df['Low'], df['Close'], name='cdl_hammer')
            df['MorningStar'] = ta.cdl_pattern(df['Open'], df['High'], df['Low'], df['Close'], name='cdl_morningstar')
            df['BullishEngulfing'] = ta.cdl_pattern(df['Open'], df['High'], df['Low'], df['Close'], name='cdl_engulfing')

            # Bearish patterns
            df['ShootingStar'] = ta.cdl_pattern(df['Open'], df['High'], df['Low'], df['Close'], name='cdl_shootingstar')
            df['EveningStar'] = ta.cdl_pattern(df['Open'], df['High'], df['Low'], df['Close'], name='cdl_eveningstar')
            df['BearishEngulfing'] = ta.cdl_pattern(df['Open'], df['High'], df['Low'], df['Close'], name='cdl_engulfing')

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
            # ADX based trend strength
            adx_strength = df['ADX'].iloc[-1] / 100.0

            # Moving Average alignment
            ma_alignment = self._calculate_ma_alignment(df)

            # MACD momentum
            macd_strength = abs(df['MACD'].iloc[-1]) / df['Close'].iloc[-1]

            # Combine indicators
            trend_strength = np.mean([
                adx_strength,
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

    def determine_market_condition(self, df: pd.DataFrame) -> MarketCondition:
        """Determine overall market condition"""
        try:
            # Trend analysis
            trend = self._determine_trend(df)
            trend_strength = self.calculate_trend_strength(df)

            # Volatility
            volatility = df['Volatility'].iloc[-1]

            # Volume profile
            volume_profile = self._analyze_volume_profile(df)

            # Support/Resistance
            support = df['Support'].iloc[-1]
            resistance = df['Resistance'].iloc[-1]

            return MarketCondition(
                trend=trend,
                strength=trend_strength,
                volatility=volatility,
                volume_profile=volume_profile,
                support_level=support,
                resistance_level=resistance
            )

        except Exception as e:
            logger.error(f"Error determining market condition: {e}")
            return MarketCondition(
                trend='sideways',
                strength=0.5,
                volatility=0.0,
                volume_profile='normal',
                support_level=0.0,
                resistance_level=0.0
            )

    def _determine_trend(self, df: pd.DataFrame) -> str:
        """Determine market trend direction"""
        try:
            # Use multiple indicators for trend determination
            sma_20 = df['SMA_20'].iloc[-1]
            sma_50 = df['SMA_50'].iloc[-1]
            current_price = df['Close'].iloc[-1]
            macd = df['MACD'].iloc[-1]
            adx = df['ADX'].iloc[-1]

            # Strong trend criteria
            strong_trend = adx > 25

            if strong_trend:
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
            current_volume = df['Volume'].iloc[-1]
            avg_volume = df['Volume_MA'].iloc[-1]
            volume_ratio = current_volume / avg_volume

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