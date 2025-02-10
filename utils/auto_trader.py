import logging
from datetime import datetime
import time
import pandas as pd
from utils.data_loader import CryptoDataLoader
from utils.indicators import TechnicalIndicators
from utils.trading_bot import TradingBot
from utils.database import get_db, TradingStrategy, SimulationResult

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
        self.trading_bot = TradingBot()
        
        # Setup logging
        self.setup_logging()
        
        # Stato del trading
        self.is_in_position = False
        self.current_position = None
        self.last_action_time = None
        
    def setup_logging(self):
        """Configura il sistema di logging"""
        logging.basicConfig(
            filename=f'trading_log_{self.symbol}_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def analyze_market(self):
        """Analizza il mercato e genera segnali di trading"""
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
            
            # Ottieni predizioni
            self.trading_bot.train(df)
            predictions = self.trading_bot.predict(df)
            
            # Analisi del segnale finale
            latest_pred = predictions.iloc[-1]
            current_price = df['Close'].iloc[-1]
            
            return {
                'prediction': latest_pred,
                'price': current_price,
                'rsi': df['RSI'].iloc[-1],
                'macd': df['MACD'].iloc[-1]
            }
            
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
            prediction = signal['prediction']
            rsi = signal['rsi']
            
            # Logica di trading
            if not self.is_in_position:  # Non siamo in posizione
                if prediction > 0.7 and rsi < 70:  # Segnale di acquisto
                    # Calcola la size della posizione basata sul risk management
                    position_size = (self.balance * self.risk_per_trade) / price
                    
                    self.logger.info(f"ACQUISTO: Prezzo={price:.2f}, Size={position_size:.6f}")
                    self.is_in_position = True
                    self.current_position = {
                        'entry_price': price,
                        'size': position_size,
                        'entry_time': current_time
                    }
                    self.last_action_time = current_time
                    
            else:  # Siamo in posizione
                if prediction < 0.3 or rsi > 80:  # Segnale di vendita
                    if self.current_position:
                        entry_price = self.current_position['entry_price']
                        position_size = self.current_position['size']
                        profit_loss = (price - entry_price) * position_size
                        
                        self.balance += profit_loss
                        self.logger.info(
                            f"VENDITA: Prezzo={price:.2f}, P/L={profit_loss:.2f}, "
                            f"Bilancio={self.balance:.2f}"
                        )
                        
                        self.is_in_position = False
                        self.current_position = None
                        self.last_action_time = current_time
                        
        except Exception as e:
            self.logger.error(f"Errore nell'esecuzione del trade: {str(e)}")
            
    def run(self, interval=3600):
        """
        Avvia il bot di trading
        
        Args:
            interval: Intervallo di controllo in secondi (default 1 ora)
        """
        self.logger.info(f"Avvio bot di trading per {self.symbol}")
        self.logger.info(f"Bilancio iniziale: {self.initial_balance}")
        
        try:
            while True:
                signal = self.analyze_market()
                self.execute_trade(signal)
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.info("Bot di trading fermato manualmente")
        except Exception as e:
            self.logger.error(f"Errore critico nel bot di trading: {str(e)}")
        finally:
            self.logger.info(f"Bot fermato. Bilancio finale: {self.balance}")
