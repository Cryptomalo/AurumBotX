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
from utils.wallet_manager import WalletManager # Assuming this import is needed

class AutoTrader:
    def __init__(self, symbol, initial_balance=10000, risk_per_trade=0.02, testnet=False):
        self.logger = logging.getLogger(__name__) # Logger initialized here
        self.symbol = symbol
        self.initial_balance = initial_balance
        self.risk_per_trade = risk_per_trade
        self.testnet = testnet
        self.logger.info(f"Inizializzazione bot in modalità {'testnet' if testnet else 'mainnet'}")
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
        self.wallet_manager = WalletManager(user_id=1)  # user_id temporaneo

        # Initialize strategies
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


    def calculate_market_volatility(self, df):
        """Calcola la volatilità del mercato utilizzando la deviazione standard"""
        try:
            returns = df['Close'].pct_change().dropna()
            volatility = returns.std()
            self.logger.info(f"Volatilità calcolata: {volatility}")
            return volatility
        except Exception as e:
            self.logger.error(f"Errore nel calcolo della volatilità: {str(e)}")
            return None

    def adjust_strategies_parameters(self, volatility):
        """Adatta i parametri delle strategie in base alla volatilità"""
        if volatility is None:
            return

        try:
            # Adjust scalping strategy
            self.strategies['scalping'].params.update({
                'profit_target': max(0.003, min(0.01, volatility * 2)),
                'stop_loss': max(0.002, min(0.008, volatility * 1.5))
            })

            # Adjust swing trading strategy
            self.strategies['swing'].params.update({
                'profit_target': max(0.01, min(0.2, volatility * 10)),
                'stop_loss': max(0.008, min(0.15, volatility * 8))
            })

            # Adjust meme coin strategy
            self.strategies['meme_coin'].params.update({
                'profit_target': max(0.05, min(0.3, volatility * 15)),
                'max_loss': max(0.03, min(0.2, volatility * 10))
            })

            self.logger.info("Parametri delle strategie aggiornati in base alla volatilità")
        except Exception as e:
            self.logger.error(f"Errore nell'aggiustamento dei parametri: {str(e)}")

    def merge_timeframes(self, df_short, df_medium, df_long):
        """Unisce i dati da diversi timeframe"""
        try:
            if df_short is None or df_medium is None or df_long is None:
                return None

            # Resample to shortest timeframe
            df_medium_resampled = df_medium.resample('1min').ffill()
            df_long_resampled = df_long.resample('1min').ffill()

            # Merge dataframes
            df_merged = df_short.copy()
            df_merged['sma_medium'] = df_medium_resampled['Close'].rolling(window=20).mean()
            df_merged['sma_long'] = df_long_resampled['Close'].rolling(window=50).mean()

            return df_merged

        except Exception as e:
            self.logger.error(f"Errore nella fusione dei timeframe: {str(e)}")
            return None

    def _get_social_data(self):
        """Ottiene dati dai social media per l'analisi del sentiment"""
        try:
            # Placeholder for social data analysis
            return {
                'sentiment_score': 0.5,
                'volume_score': 0.5,
                'trend_score': 0.5
            }
        except Exception as e:
            self.logger.error(f"Errore nell'ottenimento dei dati social: {str(e)}")
            return None

    def _calculate_target_price(self, df, ai_signal):
        """Calcola il prezzo target basato sui segnali AI"""
        try:
            current_price = df['Close'].iloc[-1]
            volatility = self.calculate_market_volatility(df)

            if volatility is None:
                return current_price * 1.02  # Default 2% target

            # Adjust target based on AI confidence and volatility
            target_multiplier = 1 + (ai_signal['confidence'] * volatility * 5)
            return current_price * target_multiplier

        except Exception as e:
            self.logger.error(f"Errore nel calcolo del prezzo target: {str(e)}")
            return df['Close'].iloc[-1] * 1.02  # Default 2% target

    def _calculate_stop_loss(self, df, ai_signal):
        """Calcola lo stop loss basato sui segnali AI"""
        try:
            current_price = df['Close'].iloc[-1]
            volatility = self.calculate_market_volatility(df)

            if volatility is None:
                return current_price * 0.98  # Default 2% stop loss

            # Adjust stop loss based on AI confidence and volatility
            stop_multiplier = 1 - (ai_signal['confidence'] * volatility * 3)
            return current_price * stop_multiplier

        except Exception as e:
            self.logger.error(f"Errore nel calcolo dello stop loss: {str(e)}")
            return df['Close'].iloc[-1] * 0.98  # Default 2% stop loss

    def setup_logging(self):
        logging.basicConfig(
            filename=f'trading_log_{self.symbol}_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def connect_wallet(self, wallet_address: str, chain_type: str = 'ETH'):
        """Collega un wallet specifico per il trading"""
        try:
            success = self.wallet_manager.add_wallet(wallet_address, chain_type)
            if success:
                self.logger.info(f"Wallet {wallet_address} collegato con successo")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Errore nel collegamento del wallet: {str(e)}")
            return False

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

            if df is not None and not df.empty:
                df = self.indicators.add_sma(df)
                df = self.indicators.add_rsi(df)
                df = self.indicators.add_macd(df)
            else:
                self.logger.error("DataFrame vuoto o None")
                return None

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
                return False

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
                if signal: #Check if signal is not None before executing trade.
                    self.execute_trade(signal)
                time.sleep(interval)

        except KeyboardInterrupt:
            self.logger.info("Trading bot stopped manually")
        except Exception as e:
            self.logger.error(f"Critical error in trading bot: {str(e)}")
            self.notifier.send_error_notification(self.symbol, str(e))
        finally:
            self.logger.info(f"Bot stopped. Final balance: {self.balance}")