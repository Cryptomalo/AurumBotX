import logging
from datetime import datetime
import time
import pandas as pd
from utils.data_loader import CryptoDataLoader
from utils.indicators import TechnicalIndicators
from utils.strategies.base_strategy import BaseStrategy
from utils.strategies.meme_coin_sniping import MemeCoinSnipingStrategy
from utils.strategies.scalping import ScalpingStrategy
from utils.strategies.swing_trading import SwingTradingStrategy
from utils.database import get_db, TradingStrategy, SimulationResult
from utils.notifications import TradingNotifier
from typing import Dict

class AutoTrader:
    def __init__(self, symbol, initial_balance=10000, risk_per_trade=0.02):
        """
        Inizializza il bot di trading automatico

        Args:
            symbol: Simbolo della crypto (es. 'BTC-USD')
            initial_balance: Bilancio iniziale
            risk_per_trade: Percentuale di rischio per trade (default 2%)
        """
        self.symbol = symbol
        self.initial_balance = initial_balance
        self.risk_per_trade = risk_per_trade
        self.balance = initial_balance

        # Inizializza i componenti
        self.data_loader = CryptoDataLoader()
        self.indicators = TechnicalIndicators()
        self.notifier = TradingNotifier()

        # Setup logging
        self.setup_logging()

        # Inizializza le strategie
        self.strategies: Dict[str, BaseStrategy] = {
            'meme_coin': MemeCoinSnipingStrategy({
                'min_liquidity': 200000,  # Increased minimum liquidity
                'sentiment_threshold': 0.75,  # More strict sentiment requirement
                'profit_target': 0.15,  # Higher profit target
                'max_loss': 0.05,
                'volume_threshold': 100000,  # Minimum volume requirement
                'momentum_period': 12  # Momentum calculation period
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

        # Stato del trading
        self.is_in_position = False
        self.current_position = None
        self.last_action_time = None
        self.active_strategy = None

    def setup_logging(self):
        """Configura il sistema di logging"""
        logging.basicConfig(
            filename=f'trading_log_{self.symbol}_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def analyze_market(self):
        """Analizza il mercato usando tutte le strategie attive"""
        try:
            # Carica i dati recenti
            df = self.data_loader.get_historical_data(self.symbol, period='7d')
            if df is None or df.empty:
                self.logger.error("Impossibile ottenere i dati di mercato")
                return None

            # Aggiungi indicatori tecnici
            df = self.indicators.add_sma(df)
            df = self.indicators.add_rsi(df)
            df = self.indicators.add_macd(df)

            # Analizza con ogni strategia
            best_signal = None
            best_confidence = 0

            for strategy_name, strategy in self.strategies.items():
                if not strategy.is_strategy_active():
                    continue

                analysis = strategy.analyze_market(df)
                signal = strategy.generate_signals(analysis)

                # Valida il trade
                portfolio_status = {
                    'available_capital': self.balance,
                    'total_capital': self.initial_balance,
                    'current_spread': 0.001,  # Esempio di spread
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
            self.logger.error(f"Errore nell'analisi del mercato: {str(e)}")
            return None

    def execute_trade(self, signal):
        """
        Esegue un'operazione di trading basata sul segnale

        Args:
            signal: Dizionario contenente l'analisi di mercato
        """
        try:
            if signal is None:
                return

            current_time = datetime.now()

            # Evita trading troppo frequente
            if self.last_action_time and (current_time - self.last_action_time).seconds < 3600:
                return

            price = signal['price']
            action = signal['action']
            confidence = signal['confidence']

            # Logica di trading
            if not self.is_in_position and action == 'buy':  # Non siamo in posizione
                # Calcola la size della posizione basata sul risk management
                position_size = (self.balance * self.risk_per_trade * signal['size_factor'])

                self.logger.info(
                    f"ACQUISTO con strategia {self.active_strategy}: "
                    f"Prezzo={price:.2f}, Size={position_size:.6f}"
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

                # Invia notifica
                self.notifier.send_trade_notification(
                    'BUY',
                    self.symbol,
                    price,
                    position_size
                )

            elif self.is_in_position:  # Siamo in posizione
                if (action == 'sell' or 
                    price >= self.current_position['target_price'] or 
                    price <= self.current_position['stop_loss']):

                    if self.current_position:
                        entry_price = self.current_position['entry_price']
                        position_size = self.current_position['size']
                        profit_loss = (price - entry_price) * position_size

                        self.balance += profit_loss
                        self.logger.info(
                            f"VENDITA con strategia {self.current_position['strategy']}: "
                            f"Prezzo={price:.2f}, P/L={profit_loss:.2f}, "
                            f"Bilancio={self.balance:.2f}"
                        )

                        # Invia notifica
                        self.notifier.send_trade_notification(
                            'SELL',
                            self.symbol,
                            price,
                            position_size,
                            profit_loss
                        )

                        self.is_in_position = False
                        self.current_position = None
                        self.last_action_time = current_time

        except Exception as e:
            self.logger.error(f"Errore nell'esecuzione del trade: {str(e)}")
            self.notifier.send_error_notification(self.symbol, str(e))

    def activate_strategy(self, strategy_name: str):
        """Attiva una strategia specifica"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].activate()
            self.logger.info(f"Strategia {strategy_name} attivata")

    def deactivate_strategy(self, strategy_name: str):
        """Disattiva una strategia specifica"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].deactivate()
            self.logger.info(f"Strategia {strategy_name} disattivata")

    def run(self, interval=3600):
        """
        Avvia il bot di trading

        Args:
            interval: Intervallo di controllo in secondi (default 1 ora)
        """
        self.logger.info(f"Avvio bot di trading per {self.symbol}")
        self.logger.info(f"Bilancio iniziale: {self.initial_balance}")

        # Attiva tutte le strategie all'avvio
        for strategy_name in self.strategies:
            self.activate_strategy(strategy_name)

        try:
            while True:
                signal = self.analyze_market()
                self.execute_trade(signal)
                time.sleep(interval)

        except KeyboardInterrupt:
            self.logger.info("Bot di trading fermato manualmente")
        except Exception as e:
            self.logger.error(f"Errore critico nel bot di trading: {str(e)}")
            self.notifier.send_error_notification(self.symbol, str(e))
        finally:
            self.logger.info(f"Bot fermato. Bilancio finale: {self.balance}")