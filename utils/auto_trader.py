import logging
from datetime import datetime, timedelta
import time
import asyncio
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np # Added numpy import
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
from utils.backup_manager import BackupManager

class AutoTrader:
    def __init__(self, symbol: str, initial_balance: float = 10000, risk_per_trade: float = 0.02, testnet: bool = True):
        self.logger = logging.getLogger(__name__)
        self.symbol = self._format_symbol(symbol)  # Convert BTC-USDT to BTCUSDT format
        self.initial_balance = initial_balance
        self.risk_per_trade = risk_per_trade
        self.testnet = testnet
        self.logger.info(f"Initializing bot in {'testnet' if testnet else 'mainnet'} mode")

        # Initialize backup manager
        self.backup_manager = BackupManager()

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
        self.data_loader = CryptoDataLoader(testnet=testnet)
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

        # Start automatic backup
        self._start_config_backup()

    async def analyze_market_async(self, market_data: pd.DataFrame, sentiment_data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Asynchronous version of market analysis"""
        try:
            if self.testnet:
                self.logger.info("Running analysis in testnet mode")

            if market_data is None or market_data.empty:
                self.logger.error("Unable to get market data")
                return None

            # Add technical indicators synchronously
            try:
                market_data = self.indicators.add_all_indicators(market_data)
                market_volatility = self.calculate_market_volatility(market_data)
                self.adjust_strategies_parameters(market_volatility)
            except Exception as e:
                self.logger.error(f"Error analyzing market conditions: {str(e)}")
                return None

            # Get AI predictions asynchronously
            try:
                if sentiment_data:
                    ai_signal = await self.prediction_model.analyze_market_with_ai(
                        market_data, 
                        sentiment_data
                    )
                    if ai_signal and ai_signal.get('confidence', 0) > 0.75:
                        return {
                            'action': 'buy' if ai_signal['technical_score'] > 0.5 else 'sell',
                            'confidence': ai_signal['confidence'],
                            'size_factor': ai_signal['suggested_position_size'],
                            'target_price': await self._calculate_target_price_async(market_data, ai_signal),
                            'stop_loss': await self._calculate_stop_loss_async(market_data, ai_signal),
                            'price': market_data['Close'].iloc[-1]
                        }
            except Exception as e:
                self.logger.warning(f"AI analysis error (non-critical): {str(e)}")

            best_signal = None
            best_confidence = 0

            # Try each strategy asynchronously
            for strategy_name, strategy in self.strategies.items():
                if not hasattr(strategy, 'is_strategy_active') or not strategy.is_strategy_active():
                    continue

                try:
                    analysis = await strategy.analyze_market(market_data, sentiment_data)
                    if not analysis or len(analysis) == 0:
                        continue

                    signal = analysis[0] if isinstance(analysis, list) else analysis
                    if signal['action'] == 'hold':
                        continue

                    portfolio_status = {
                        'available_capital': self.balance,
                        'total_capital': self.initial_balance,
                        'current_spread': 0.001,
                        'market_trend': 1 if market_data['Close'].iloc[-1] > market_data['SMA_20'].iloc[-1] else -1
                    }

                    if (signal.get('confidence', 0) > best_confidence and 
                        await strategy.validate_trade(signal, portfolio_status)):
                        best_signal = signal
                        best_confidence = signal['confidence']
                        self.active_strategy = strategy_name
                except Exception as e:
                    self.logger.error(f"Error in strategy {strategy_name}: {str(e)}")
                    continue

            if best_signal:
                best_signal['price'] = market_data['Close'].iloc[-1]
                return best_signal

            return None

        except Exception as e:
            self.logger.error(f"Market analysis error: {str(e)}")
            return None

    def calculate_market_volatility(self, df: pd.DataFrame) -> float:
        """Calculate market volatility using standard deviation"""
        try:
            returns = df['Returns'].fillna(0)
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
            self.logger.info(f"Calculated volatility: {volatility}")
            return volatility
        except Exception as e:
            self.logger.error(f"Error calculating volatility: {str(e)}")
            return 0.01  # Default minimal volatility

    def adjust_strategies_parameters(self, volatility: float):
        """Adjust strategy parameters based on market volatility"""
        try:
            for strategy in self.strategies.values():
                if hasattr(strategy, 'optimize_parameters'):
                    strategy.optimize_parameters({'volatility': volatility})
            self.logger.info("Strategy parameters updated based on volatility")
        except Exception as e:
            self.logger.error(f"Error adjusting parameters: {str(e)}")

    async def _calculate_target_price_async(self, df: pd.DataFrame, ai_signal: Dict[str, Any]) -> float:
        """Calculate target price based on AI signals asynchronously"""
        try:
            current_price = df['Close'].iloc[-1]
            volatility = self.calculate_market_volatility(df)
            target_multiplier = 1 + (ai_signal['confidence'] * volatility * 5)
            return current_price * target_multiplier
        except Exception as e:
            self.logger.error(f"Error calculating target price: {str(e)}")
            return df['Close'].iloc[-1] * 1.02

    async def _calculate_stop_loss_async(self, df: pd.DataFrame, ai_signal: Dict[str, Any]) -> float:
        """Calculate stop loss based on AI signals asynchronously"""
        try:
            current_price = df['Close'].iloc[-1]
            volatility = self.calculate_market_volatility(df)
            stop_multiplier = 1 - (ai_signal['confidence'] * volatility * 3)
            return current_price * stop_multiplier
        except Exception as e:
            self.logger.error(f"Error calculating stop loss: {str(e)}")
            return df['Close'].iloc[-1] * 0.98

    def _format_symbol(self, symbol: str) -> str:
        """Convert symbol to Binance format"""
        return symbol.replace('-', '').replace('/', '')

    def setup_logging(self):
        """Configure logging with proper format and file output"""
        log_filename = f'trading_log_{self.symbol}_{datetime.now().strftime("%Y%m%d")}.log'
        logging.basicConfig(
            filename=log_filename,
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)


    async def execute_trade_async(self, signal: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a trade based on the generated signal asynchronously"""
        try:
            if not signal:
                return {'success': False, 'reason': 'No signal provided'}

            current_time = datetime.now()
            if self.last_action_time and (current_time - self.last_action_time).seconds < 300:
                return {'success': False, 'reason': 'Trade cooldown active'}

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
                    try:
                        await self.notifier.send_trade_notification('BUY', self.symbol, price, position_size)
                    except Exception as e:
                        self.logger.error(f"Notification error (non-critical): {str(e)}")

                return {'success': True, 'action': 'buy', 'price': price, 'size': position_size}

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
                        try:
                            await self.notifier.send_trade_notification(
                                'SELL', self.symbol, price, position_size, profit_loss
                            )
                        except Exception as e:
                            self.logger.error(f"Notification error (non-critical): {str(e)}")

                    self.is_in_position = False
                    self.current_position = None
                    self.last_action_time = current_time
                    return {'success': True, 'action': 'sell', 'price': price, 'profit_loss': profit_loss}

            return {'success': False, 'reason': 'No trade conditions met'}

        except Exception as e:
            self.logger.error(f"Trade execution error: {str(e)}")
            if self.notifier:
                try:
                    await self.notifier.send_error_notification(self.symbol, str(e))
                except Exception as notify_error:
                    self.logger.error(f"Error notification failed: {str(notify_error)}")
            return {'success': False, 'error': str(e)}

    async def run(self, interval: int = 3600):
        """Main trading loop"""
        self.logger.info(f"Starting trading bot for {self.symbol}")
        self.logger.info(f"Initial balance: {self.initial_balance}")

        try:
            while True:
                market_data = self.data_loader.get_historical_data(self.symbol, period='1d', interval='1m')
                sentiment_data = self._get_social_data()
                signal = await self.analyze_market_async(market_data, sentiment_data)
                if signal:
                    result = await self.execute_trade_async(signal)
                    self.logger.info(f"Trade execution result: {result}")

                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            self.logger.info("Trading bot stopped manually")
            self.stop() 
        except Exception as e:
            self.logger.error(f"Critical error in trading bot: {str(e)}")
            if self.notifier:
                await self.notifier.send_error_notification(self.symbol, str(e))
            self.stop() 
        finally:
            self.logger.info(f"Bot stopped. Final balance: {self.balance}")

    def merge_timeframes(self, df_short: pd.DataFrame, df_medium: pd.DataFrame, df_long: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Merge data from different timeframes"""
        try:
            if df_short is None or df_medium is None or df_long is None:
                return None

            df_medium_resampled = df_medium.resample('1min').ffill()
            df_long_resampled = df_long.resample('1min').ffill()

            df_merged = df_short.copy()
            df_merged['SMA_medium'] = df_medium_resampled['Close'].rolling(window=20).mean() #Corrected column name
            df_merged['SMA_long'] = df_long_resampled['Close'].rolling(window=50).mean() #Corrected column name

            return df_merged

        except Exception as e:
            self.logger.error(f"Error merging timeframes: {str(e)}")
            return None

    def _get_social_data(self):
        """Get social media data for sentiment analysis"""
        return {
            'sentiment_score': 0.5,
            'volume_score': 0.5,
            'trend_score': 0.5
        }

    def _start_config_backup(self):
        """Start automatic backup of trading configuration"""
        config = {
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'trading_pair': self.symbol,
            'initial_balance': self.initial_balance,
            'risk_per_trade': self.risk_per_trade,
            'testnet': self.testnet,
            'strategies': {
                name: strategy.get_config()
                for name, strategy in self.strategies.items()
            },
            'portfolio': self.portfolio
        }

        try:
            self.backup_manager.start_auto_backup(config, self.symbol)
            self.logger.info("Automatic configuration backup started")
        except Exception as e:
            self.logger.error(f"Failed to start automatic backup: {str(e)}")

    def stop(self):
        """Stop the trading bot and its components"""
        try:
            # Stop automatic backup
            if hasattr(self, 'backup_manager'):
                self.backup_manager.stop_auto_backup()

            # Additional cleanup code can be added here

            self.logger.info("Trading bot stopped")
        except Exception as e:
            self.logger.error(f"Error stopping trading bot: {str(e)}")

    def restore_config(self, backup_timestamp: str):
        """Restore trading configuration from a backup"""
        try:
            config = self.backup_manager.load_trading_config(backup_timestamp, self.symbol)

            # Update bot configuration
            self.risk_per_trade = config.get('risk_per_trade', self.risk_per_trade)
            self.initial_balance = config.get('initial_balance', self.initial_balance)

            # Restore strategy configurations
            for strategy_name, strategy_config in config.get('strategies', {}).items():
                if strategy_name in self.strategies:
                    self.strategies[strategy_name].set_config(strategy_config)

            self.logger.info(f"Configuration restored from backup: {backup_timestamp}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to restore configuration: {str(e)}")
            return False