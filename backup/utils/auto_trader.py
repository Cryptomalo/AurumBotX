import logging
from datetime import datetime, timedelta
import time
from typing import Dict
from utils.data_loader import CryptoDataLoader
from utils.indicators import TechnicalIndicators
from utils.strategies.base_strategy import BaseStrategy
from utils.strategies.meme_coin_sniping import MemeCoinSnipingStrategy
from utils.strategies.scalping import ScalpingStrategy
from utils.strategies.swing_trading import SwingTradingStrategy
from utils.database import get_db, TradingStrategy, SimulationResult
from utils.notifications import TradingNotifier
from utils.wallet_manager import WalletManager
import pandas as pd
import numpy as np

class AutoTrader:
    def __init__(self, symbol, initial_balance=10000, risk_per_trade=0.02):
        self.symbol = symbol
        self.initial_balance = initial_balance
        self.risk_per_trade = risk_per_trade
        self.balance = initial_balance
        self.portfolio = {
            'total_value': initial_balance,
            'crypto_holdings': {},
            'open_orders': [],
            'trade_history': [],
            'performance_metrics': {
                'total_profit': 0,
                'win_rate': 0,
                'avg_profit_per_trade': 0
            }
        }

        # Initialize components
        self.data_loader = CryptoDataLoader()
        self.indicators = TechnicalIndicators()
        self.notifier = TradingNotifier()
        self.wallet_manager = WalletManager(user_id=1)  # temporary user_id

        # Initialize strategies with default parameters
        self.strategies = {
            'meme_coin': MemeCoinSnipingStrategy({
                'min_liquidity': 200000,
                'sentiment_threshold': 0.75,
                'profit_target': 0.15,
                'max_loss': 0.05,
                'volume_threshold': 100000,
                'momentum_period': 12
            }),
            'scalping': ScalpingStrategy({
                'volume_threshold': 1000000,
                'min_volatility': 0.002,
                'profit_target': 0.005,
                'initial_stop_loss': 0.003,
                'trailing_stop': 0.002
            }),
            'swing': SwingTradingStrategy({
                'trend_period': 20,
                'profit_target': 0.15,
                'stop_loss': 0.10,
                'min_trend_strength': 0.6
            })
        }

        # Trading state
        self.is_in_position = False
        self.current_position = None
        self.last_action_time = None
        self.active_strategy = None

        # Setup logging
        self.setup_logging()

    def connect_wallet(self, wallet_address: str, chain_type: str = 'ETH'):
        """Connect a specific wallet for trading"""
        try:
            success = self.wallet_manager.add_wallet(wallet_address, chain_type)
            if success:
                self.logger.info(f"Wallet {wallet_address} connected successfully")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error connecting wallet: {str(e)}")
            return False

    def setup_logging(self):
        logging.basicConfig(
            filename=f'trading_log_{self.symbol}_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def calculate_market_volatility(self, df: pd.DataFrame) -> float:
        """Calculate market volatility using standard deviation of returns"""
        try:
            # Ensure we have enough data
            if len(df) < 2:
                self.logger.warning("Insufficient data for volatility calculation")
                return 0.0

            # Calculate returns
            returns = df['Close'].pct_change().dropna()

            if len(returns) == 0:
                self.logger.warning("No valid returns data for volatility calculation")
                return 0.0

            # Calculate annualized volatility
            daily_vol = returns.std()
            annualized_vol = daily_vol * np.sqrt(252)  # Annualize using trading days

            self.logger.info(f"Calculated market volatility: {annualized_vol:.4f}")
            return float(annualized_vol)

        except Exception as e:
            self.logger.error(f"Error calculating market volatility: {str(e)}")
            return 0.0

    def analyze_market(self):
        try:
            # Analisi multi-timeframe
            df_short = self.data_loader.get_historical_data(self.symbol, period='1d')
            df_medium = self.data_loader.get_historical_data(self.symbol, period='7d')
            df_long = self.data_loader.get_historical_data(self.symbol, period='30d')

            # Auto-adattamento delle strategie basato sulla volatilità
            market_volatility = self.calculate_market_volatility(df_medium)
            self.adjust_strategies_parameters(market_volatility)

            df = self.merge_timeframes(df_short, df_medium, df_long)
            if df is None or df.empty:
                self.logger.error("Unable to get market data")
                return None

            # Use standardized column names
            df = self.indicators.add_sma(df)
            df = self.indicators.add_rsi(df)
            df = self.indicators.add_macd(df)

            # Analisi AI
            ai_signal = self.prediction_model.analyze_market_with_ai(df, self._get_social_data())

            if ai_signal and ai_signal['confidence'] > 0.75:
                return {
                    'action': 'buy' if ai_signal['technical_score'] > 0.5 else 'sell',
                    'confidence': ai_signal['confidence'],
                    'size_factor': ai_signal['suggested_position_size'],
                    'target_price': self._calculate_target_price(df, ai_signal),
                    'stop_loss': self._calculate_stop_loss(df, ai_signal)
                }

            best_signal = None
            best_confidence = 0

            for strategy_name, strategy in self.strategies.items():
                if not hasattr(strategy, 'is_strategy_active') or not strategy.is_strategy_active():
                    continue

                analysis = strategy.analyze_market(df)
                signal = strategy.generate_signals(analysis)

                portfolio_status = {
                    'available_capital': self.balance,
                    'total_capital': self.initial_balance,
                    'current_spread': 0.001,
                    'market_trend': 1 if df['Close'].iloc[-1] > df['Close'].iloc[-20].mean() else -1
                }

                if (signal['action'] != 'hold' and
                    signal['confidence'] > best_confidence and
                    strategy.validate_trade(signal, portfolio_status)):
                    best_signal = signal
                    best_confidence = signal['confidence']
                    self.active_strategy = strategy_name

            if best_signal:
                best_signal['price'] = df['Close'].iloc[-1]
                return best_signal

            return None

        except Exception as e:
            self.logger.error(f"Market analysis error: {str(e)}")
            return None

    def execute_trade(self, signal):
        try:
            if signal is None:
                return

            current_time = datetime.now()
            # Reduced minimum time between trades for better opportunities
            if self.last_action_time and (current_time - self.last_action_time).seconds < 300:
                return

            # Add execution priority based on signal strength
            if signal.get('confidence', 0) > 0.9:
                self.last_action_time = current_time - timedelta(seconds=290)

            price = signal['price']
            action = signal['action']
            confidence = signal['confidence']

            if not self.is_in_position and action == 'buy':
                position_size = (self.balance * self.risk_per_trade * signal['size_factor'])

                self.logger.info(
                    f"BUY with strategy {self.active_strategy}: "
                    f"Price={price:.2f}, Size={position_size:.6f}"
                )

                self.is_in_position = True
                self.current_position = {
                    'entry_price': price,
                    'size': position_size,
                    'entry_time': current_time,
                    'strategy': self.active_strategy,
                    'target_price': signal['target_price'],
                    'stop_loss': signal['stop_loss']
                }
                self.last_action_time = current_time
                self.notifier.send_trade_notification('BUY', self.symbol, price, position_size)

            elif self.is_in_position and self.current_position:
                if (action == 'sell' or
                    price >= self.current_position['target_price'] or
                    price <= self.current_position['stop_loss']):

                    entry_price = self.current_position['entry_price']
                    position_size = self.current_position['size']
                    profit_loss = (price - entry_price) * position_size

                    self.balance += profit_loss
                    self.logger.info(
                        f"SELL with strategy {self.current_position['strategy']}: "
                        f"Price={price:.2f}, P/L={profit_loss:.2f}, "
                        f"Balance={self.balance:.2f}"
                    )

                    self.notifier.send_trade_notification(
                        'SELL', self.symbol, price, position_size, profit_loss
                    )

                    self.is_in_position = False
                    self.current_position = None
                    self.last_action_time = current_time

        except Exception as e:
            self.logger.error(f"Trade execution error: {str(e)}")
            self.notifier.send_error_notification(self.symbol, str(e))

    def run(self, interval=3600):
        self.logger.info(f"Starting trading bot for {self.symbol}")
        self.logger.info(f"Initial balance: {self.initial_balance}")

        try:
            while True:
                signal = self.analyze_market()
                self.execute_trade(signal)
                time.sleep(interval)

        except KeyboardInterrupt:
            self.logger.info("Trading bot stopped manually")
        except Exception as e:
            self.logger.error(f"Critical error in trading bot: {str(e)}")
            self.notifier.send_error_notification(self.symbol, str(e))
        finally:
            self.logger.info(f"Bot stopped. Final balance: {self.balance}")

    def adjust_strategies_parameters(self, market_volatility: float) -> None:
        """Adjust strategy parameters based on market volatility"""
        try:
            # Scale factors based on market volatility
            volatility_scale = min(max(market_volatility, 0.1), 0.5)  # Cap between 0.1 and 0.5

            # Adjust scalping strategy parameters
            if 'scalping' in self.strategies:
                self.strategies['scalping'].params.update({
                    'volume_threshold': 1000000 * (1 + volatility_scale),
                    'min_volatility': 0.002 * volatility_scale,
                    'profit_target': 0.005 * (1 + volatility_scale),
                    'initial_stop_loss': 0.003 * (1 + volatility_scale),
                    'trailing_stop': 0.002 * volatility_scale
                })

            # Adjust swing trading parameters
            if 'swing' in self.strategies:
                self.strategies['swing'].params.update({
                    'trend_period': int(20 * (1 + volatility_scale)),
                    'profit_target': 0.15 * (1 + volatility_scale),
                    'stop_loss': 0.10 * (1 + volatility_scale),
                    'min_trend_strength': 0.6 * (1 - volatility_scale/2)  # Lower requirement in volatile markets
                })

            # Adjust meme coin strategy parameters
            if 'meme_coin' in self.strategies:
                self.strategies['meme_coin'].params.update({
                    'min_liquidity': 200000 * (1 + volatility_scale),
                    'sentiment_threshold': 0.75 * (1 - volatility_scale/4),
                    'profit_target': 0.15 * (1 + volatility_scale),
                    'max_loss': 0.05 * (1 + volatility_scale/2),
                    'volume_threshold': 100000 * (1 + volatility_scale),
                    'momentum_period': int(12 * (1 + volatility_scale/2))
                })

            self.logger.info(f"Strategy parameters adjusted for volatility: {volatility_scale:.4f}")

        except Exception as e:
            self.logger.error(f"Error adjusting strategy parameters: {str(e)}")
            # Continue with default parameters if adjustment fails
            pass

    def merge_timeframes(self, df_short, df_medium, df_long):
        # Placeholder for merging multiple timeframes
        return df_medium

    def _get_social_data(self):
        # Placeholder for getting social media sentiment data
        return {}

    def _calculate_target_price(self, df, ai_signal):
        # Placeholder for calculating target price
        return df['Close'].iloc[-1] * 1.01

    def _calculate_stop_loss(self, df, ai_signal):
        # Placeholder for calculating stop loss
        return df['Close'].iloc[-1] * 0.99