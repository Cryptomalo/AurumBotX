import asyncio
import logging
from datetime import datetime, timedelta
import time
from typing import Dict, Any, Optional
import pandas as pd
from utils.data_loader import CryptoDataLoader
from utils.indicators import TechnicalIndicators
from utils.strategies.base_strategy import BaseStrategy
from utils.strategies.meme_coin_sniping import MemeCoinStrategy
from utils.strategies.scalping import ScalpingStrategy
from utils.strategies.swing_trading import SwingTradingStrategy
from utils.strategies.dex_sniping import DexSnipingStrategy
from utils.database import get_db, TradingStrategy, SimulationResult
from utils.notifications import TradingNotifier
from utils.wallet_manager import WalletManager
from utils.prediction_model import PredictionModel

class AutoTrader:
    def __init__(self, symbol: str, initial_balance: float = 10000, risk_per_trade: float = 0.02, testnet: bool = True):
        self.logger = logging.getLogger(__name__)
        self.symbol = symbol.replace("-", "/")  # Convert BTC-USDT to BTC/USDT format
        self.initial_balance = initial_balance
        self.risk_per_trade = risk_per_trade
        self.testnet = testnet
        self.logger.info(f"Initializing bot in {'testnet' if testnet else 'mainnet'} mode")
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
        self.setup_logging()
        self.data_loader = CryptoDataLoader()
        self.indicators = TechnicalIndicators()
        self.prediction_model = PredictionModel()

        # Disable external services in test mode
        if self.testnet:
            self.notifier = None
            self.wallet_manager = None
        else:
            self.notifier = TradingNotifier()
            self.wallet_manager = WalletManager(user_id=1)

        # Initialize strategies with testnet configuration
        self.strategies = {
            'scalping': ScalpingStrategy({
                'volume_threshold': 1000000,
                'min_volatility': 0.002,
                'profit_target': 0.005,
                'initial_stop_loss': 0.003,
                'trailing_stop': 0.002,
                'testnet': testnet
            }),
            'swing': SwingTradingStrategy({
                'trend_period': 20,
                'profit_target': 0.15,
                'stop_loss': 0.10,
                'min_trend_strength': 0.6,
                'testnet': testnet
            })
        }

        if not self.testnet:
            self.strategies.update({
                'meme_coin': MemeCoinStrategy({
                    'min_liquidity': 200000,
                    'sentiment_threshold': 0.75,
                    'profit_target': 0.15,
                    'max_loss': 0.05,
                    'volume_threshold': 100000,
                    'momentum_period': 12,
                    'testnet': testnet
                }),
                'dex': DexSnipingStrategy({
                    'min_liquidity': 5,
                    'max_buy_tax': 10,
                    'min_holders': 50,
                    'testnet': testnet,
                    'rpc_url': 'https://bsc-dataseed.binance.org/'
                })
            })

        # Trading state
        self.is_in_position = False
        self.current_position = None
        self.last_action_time = None
        self.active_strategy = None

    def setup_logging(self):
        """Configure logging with proper format and file output"""
        log_filename = f'trading_log_{self.symbol}_{datetime.now().strftime("%Y%m%d")}.log'
        logging.basicConfig(
            filename=log_filename,
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def analyze_market(self):
        """Analyze market data and generate trading signals"""
        try:
            if self.testnet:
                self.logger.info("Running in testnet mode")

            # Get market data
            df_short = self.data_loader.get_historical_data(self.symbol, period='1d', interval='1m')
            df_medium = self.data_loader.get_historical_data(self.symbol, period='7d', interval='15m')
            df_long = self.data_loader.get_historical_data(self.symbol, period='30d', interval='1h')

            if df_short is None or df_short.empty:
                self.logger.error("Unable to get market data")
                return None

            # Add technical indicators with error handling
            try:
                df_short = self.indicators.add_all_indicators(df_short)
                market_volatility = self.calculate_market_volatility(df_medium)
                self.adjust_strategies_parameters(market_volatility)
            except Exception as e:
                self.logger.error(f"Error adding technical indicators: {str(e)}")
                return None

            # Merge timeframes
            df = self.merge_timeframes(df_short, df_medium, df_long)
            if df is None:
                return None

            # Get AI predictions
            try:
                ai_signal = self.prediction_model.analyze_market_with_ai(df, self._get_social_data())
                if ai_signal and ai_signal['confidence'] > 0.75:
                    return {
                        'action': 'buy' if ai_signal['technical_score'] > 0.5 else 'sell',
                        'confidence': ai_signal['confidence'],
                        'size_factor': ai_signal['suggested_position_size'],
                        'target_price': self._calculate_target_price(df, ai_signal),
                        'stop_loss': self._calculate_stop_loss(df, ai_signal)
                    }
            except Exception as e:
                self.logger.warning(f"AI analysis error (non-critical): {str(e)}")

            best_signal = None
            best_confidence = 0

            for strategy_name, strategy in self.strategies.items():
                if not strategy.is_strategy_active():
                    continue

                try:
                    signal = strategy.generate_signals(df)
                    if not signal:
                        continue

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
                except Exception as e:
                    self.logger.error(f"Error in strategy {strategy_name}: {str(e)}")
                    continue

            if best_signal:
                best_signal['price'] = df['Close'].iloc[-1]
                return best_signal

            return None

        except Exception as e:
            self.logger.error(f"Market analysis error: {str(e)}")
            return None

    def _get_social_data(self):
        """Get social media data for sentiment analysis"""
        try:
            return {
                'sentiment_score': 0.5,
                'volume_score': 0.5,
                'trend_score': 0.5
            }
        except Exception as e:
            self.logger.error(f"Error getting social data: {str(e)}")
            return None

    def _calculate_target_price(self, df: pd.DataFrame, ai_signal: Dict[str, Any]) -> float:
        """Calculate target price based on AI signals"""
        try:
            current_price = df['Close'].iloc[-1]
            volatility = self.calculate_market_volatility(df)
            if volatility is None:
                return current_price * 1.02
            target_multiplier = 1 + (ai_signal['confidence'] * volatility * 5)
            return current_price * target_multiplier
        except Exception as e:
            self.logger.error(f"Error calculating target price: {str(e)}")
            return df['Close'].iloc[-1] * 1.02

    def _calculate_stop_loss(self, df: pd.DataFrame, ai_signal: Dict[str, Any]) -> float:
        """Calculate stop loss based on AI signals"""
        try:
            current_price = df['Close'].iloc[-1]
            volatility = self.calculate_market_volatility(df)
            if volatility is None:
                return current_price * 0.98
            stop_multiplier = 1 - (ai_signal['confidence'] * volatility * 3)
            return current_price * stop_multiplier
        except Exception as e:
            self.logger.error(f"Error calculating stop loss: {str(e)}")
            return df['Close'].iloc[-1] * 0.98

    def execute_trade(self, signal: Optional[Dict[str, Any]]) -> bool:
        """Execute a trade based on the generated signal"""
        if not signal:
            return False

        try:
            current_time = datetime.now()
            if self.last_action_time and (current_time - self.last_action_time).seconds < 300:
                return False

            if signal.get('confidence', 0) > 0.9:
                self.last_action_time = current_time - timedelta(seconds=290)

            price = signal['price']
            action = signal['action']

            if not self.is_in_position and action == 'buy':
                position_size = self.balance * self.risk_per_trade * signal['size_factor']

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
                if self.notifier:
                    self.notifier.send_trade_notification('BUY', self.symbol, price, position_size)
                return True

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

                    if self.notifier:
                        self.notifier.send_trade_notification(
                            'SELL', self.symbol, price, position_size, profit_loss
                        )

                    self.is_in_position = False
                    self.current_position = None
                    self.last_action_time = current_time
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Trade execution error: {str(e)}")
            if self.notifier:
                self.notifier.send_error_notification(self.symbol, str(e))
            return False

    def run(self, interval: int = 3600):
        """Main trading loop"""
        self.logger.info(f"Starting trading bot for {self.symbol}")
        self.logger.info(f"Initial balance: {self.initial_balance}")

        try:
            while True:
                signal = self.analyze_market()
                if signal:
                    self.execute_trade(signal)
                time.sleep(interval)

        except KeyboardInterrupt:
            self.logger.info("Trading bot stopped manually")
        except Exception as e:
            self.logger.error(f"Critical error in trading bot: {str(e)}")
            if self.notifier:
                self.notifier.send_error_notification(self.symbol, str(e))
        finally:
            self.logger.info(f"Bot stopped. Final balance: {self.balance}")

    def calculate_market_volatility(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate market volatility using standard deviation"""
        try:
            returns = df['Close'].pct_change().dropna()
            volatility = returns.std()
            self.logger.info(f"Calculated volatility: {volatility}")
            return volatility
        except Exception as e:
            self.logger.error(f"Error calculating volatility: {str(e)}")
            return None

    def adjust_strategies_parameters(self, volatility: Optional[float]):
        """Adjust strategy parameters based on market volatility"""
        if volatility is None:
            return

        try:
            for strategy in self.strategies.values():
                strategy.optimize_parameters({'volatility': volatility})
            self.logger.info("Strategy parameters updated based on volatility")
        except Exception as e:
            self.logger.error(f"Error adjusting parameters: {str(e)}")

    def merge_timeframes(self, df_short: pd.DataFrame, df_medium: pd.DataFrame, df_long: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Merge data from different timeframes"""
        try:
            if df_short is None or df_medium is None or df_long is None:
                return None

            df_medium_resampled = df_medium.resample('1min').ffill()
            df_long_resampled = df_long.resample('1min').ffill()

            df_merged = df_short.copy()
            df_merged['sma_medium'] = df_medium_resampled['Close'].rolling(window=20).mean()
            df_merged['sma_long'] = df_long_resampled['Close'].rolling(window=50).mean()

            return df_merged

        except Exception as e:
            self.logger.error(f"Error merging timeframes: {str(e)}")
            return None