#!/usr/bin/env python3
"""
AurumBotX 24/7 Monitoring System
Sistema di monitoraggio continuo per AurumBotX con logging avanzato e recovery automatico
"""

import os
import sys
import asyncio
import logging
import signal
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import traceback

# Aggiungi il percorso del progetto
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

class AurumBotMonitor:
    def __init__(self):
        self.setup_logging()
        self.running = True
        self.stats = {
            'start_time': datetime.now(),
            'cycles_completed': 0,
            'signals_generated': 0,
            'trades_executed': 0,
            'errors_count': 0,
            'last_signal': None,
            'last_trade': None,
            'uptime': 0
        }
        self.config = {
            'cycle_interval': 60,  # 60 secondi tra i cicli
            'health_check_interval': 300,  # 5 minuti
            'log_stats_interval': 900,  # 15 minuti
            'auto_restart_on_error': True,
            'max_consecutive_errors': 5,
            'enable_trading': False,  # Inizialmente solo monitoraggio
            'trading_pairs': ['BTCUSDT'],
            'strategies': ['swing_trading']  # Strategia conservativa
        }
        self.consecutive_errors = 0
        
    def setup_logging(self):
        """Configura logging avanzato"""
        # Crea directory logs se non esiste
        Path('logs').mkdir(exist_ok=True)
        
        # Configurazione logging
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Logger principale
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(f'logs/monitor_24_7_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        
        # Logger specifici
        self.logger = logging.getLogger('AurumBotMonitor')
        self.trade_logger = logging.getLogger('TradeLogger')
        self.error_logger = logging.getLogger('ErrorLogger')
        
        # Handler per trade log separato
        trade_handler = logging.FileHandler(f'logs/trades_{datetime.now().strftime("%Y%m%d")}.log')
        trade_handler.setFormatter(logging.Formatter(log_format))
        self.trade_logger.addHandler(trade_handler)
        
        # Handler per error log separato
        error_handler = logging.FileHandler(f'logs/errors_{datetime.now().strftime("%Y%m%d")}.log')
        error_handler.setFormatter(logging.Formatter(log_format))
        self.error_logger.addHandler(error_handler)
        
    async def initialize_components(self):
        """Inizializza tutti i componenti del bot"""
        try:
            from utils.ai_trading import AITrading
            from utils.data_loader import CryptoDataLoader
            from utils.exchange_manager import ExchangeManager
            from utils.strategies.swing_trading import SwingTradingStrategy
            
            self.logger.info("🚀 Inizializzazione componenti AurumBotX...")
            
            # Inizializza componenti core
            self.ai_trading = AITrading()
            self.data_loader = CryptoDataLoader(use_live_data=True)
            self.exchange_manager = ExchangeManager(
                exchange_id='binance',
                api_key=os.getenv('BINANCE_API_KEY'),
                api_secret=os.getenv('BINANCE_SECRET_KEY'),
                testnet=True
            )
            
            # Inizializza strategia
            strategy_config = {
                'profit_target': 0.05,  # 5%
                'stop_loss': 0.03,      # 3%
                'trend_period': 20,
                'min_trend_strength': 0.6
            }
            self.strategy = SwingTradingStrategy(strategy_config)
            
            # Addestra il modello AI
            self.logger.info("🧠 Addestramento modello AI...")
            historical_data = await self.data_loader.get_historical_data('BTCUSDT', '30d', '1h')
            await self.ai_trading.prediction_model.train_async(historical_data, 'Close', 5)
            
            self.logger.info("✅ Tutti i componenti inizializzati con successo")
            return True
            
        except Exception as e:
            self.error_logger.error(f"❌ Errore inizializzazione: {str(e)}")
            self.error_logger.error(traceback.format_exc())
            return False
    
    async def monitoring_cycle(self):
        """Ciclo principale di monitoraggio"""
        try:
            cycle_start = time.time()
            self.stats['cycles_completed'] += 1
            
            self.logger.info(f"📊 CICLO {self.stats['cycles_completed']} - {datetime.now().strftime('%H:%M:%S')}")
            
            # 1. Health check componenti
            await self.health_check()
            
            # 2. Analisi mercato per ogni pair
            for pair in self.config['trading_pairs']:
                await self.analyze_market(pair)
            
            # 3. Aggiorna statistiche
            cycle_time = time.time() - cycle_start
            self.stats['uptime'] = (datetime.now() - self.stats['start_time']).total_seconds()
            
            # Reset consecutive errors su successo
            self.consecutive_errors = 0
            
            self.logger.info(f"✅ Ciclo completato in {cycle_time:.2f}s")
            
        except Exception as e:
            self.consecutive_errors += 1
            self.stats['errors_count'] += 1
            self.error_logger.error(f"❌ Errore nel ciclo {self.stats['cycles_completed']}: {str(e)}")
            self.error_logger.error(traceback.format_exc())
            
            # Auto-restart se troppi errori consecutivi
            if (self.consecutive_errors >= self.config['max_consecutive_errors'] and 
                self.config['auto_restart_on_error']):
                self.logger.warning(f"⚠️ Troppi errori consecutivi ({self.consecutive_errors}), riavvio componenti...")
                await self.restart_components()
    
    async def analyze_market(self, pair):
        """Analizza il mercato per una coppia specifica"""
        try:
            # Analisi mercato
            market_analysis = await self.ai_trading.analyze_market(pair)
            if not market_analysis:
                self.logger.warning(f"⚠️ Nessuna analisi mercato per {pair}")
                return
            
            price = market_analysis['market_data']['price']
            rsi = market_analysis['market_data']['rsi']
            sentiment = market_analysis['sentiment']['sentiment']
            
            self.logger.info(f"💹 {pair}: ${price:,.2f} | RSI: {rsi:.2f} | Sentiment: {sentiment}")
            
            # Generazione segnali
            signals = await self.ai_trading.generate_trading_signals(pair)
            if signals:
                signal = signals[0]
                self.stats['signals_generated'] += 1
                self.stats['last_signal'] = {
                    'timestamp': datetime.now().isoformat(),
                    'pair': pair,
                    'action': signal['action'],
                    'confidence': signal['confidence'],
                    'price': signal['price']
                }
                
                self.logger.info(f"🎯 Segnale {pair}: {signal['action'].upper()} | "
                               f"Confidenza: {signal['confidence']:.1%} | "
                               f"Prezzo: ${signal['price']:,.2f}")
                
                # Log trade separato
                self.trade_logger.info(f"SIGNAL|{pair}|{signal['action']}|{signal['confidence']:.3f}|{signal['price']:.2f}")
                
                # Esecuzione trade se abilitata
                if self.config['enable_trading'] and signal['confidence'] >= 0.7:
                    await self.execute_trade(pair, signal)
            
            # Verifica saldo
            balance = await self.exchange_manager.get_balance()
            if 'USDT' in balance:
                usdt_balance = balance['USDT']['free']
                self.logger.info(f"💵 Saldo USDT: {usdt_balance:,.2f}")
            
        except Exception as e:
            self.error_logger.error(f"❌ Errore analisi {pair}: {str(e)}")
    
    async def execute_trade(self, pair, signal):
        """Esegue un trade basato sul segnale"""
        try:
            # Validazione trade con strategia
            portfolio = await self.exchange_manager.get_balance()
            is_valid = await self.strategy.validate_trade(signal, portfolio)
            
            if not is_valid:
                self.logger.warning(f"⚠️ Trade {pair} non valido secondo strategia")
                return
            
            # Calcola position size
            position_size = await self.strategy._calculate_position_size(
                signal['price'], 
                signal['confidence']
            )
            
            # Esegui ordine (simulato in testnet)
            if signal['action'] == 'buy':
                quantity = (position_size * 10000) / signal['price']  # Usa saldo testnet
                order_result = await self.exchange_manager.place_order(
                    pair, 'market', 'buy', quantity
                )
            elif signal['action'] == 'sell':
                # Vendi tutto il BTC disponibile
                btc_balance = portfolio.get('BTC', {}).get('free', 0)
                if btc_balance > 0.00001:  # Minimo per trade
                    order_result = await self.exchange_manager.place_order(
                        pair, 'market', 'sell', btc_balance
                    )
                else:
                    self.logger.warning(f"⚠️ Saldo BTC insufficiente per vendita")
                    return
            
            if order_result and order_result.get('status') == 'FILLED':
                self.stats['trades_executed'] += 1
                self.stats['last_trade'] = {
                    'timestamp': datetime.now().isoformat(),
                    'pair': pair,
                    'action': signal['action'],
                    'quantity': order_result.get('executedQty', 0),
                    'price': order_result.get('price', signal['price']),
                    'order_id': order_result.get('orderId')
                }
                
                self.logger.info(f"✅ Trade eseguito: {signal['action'].upper()} {pair} | "
                               f"ID: {order_result.get('orderId')}")
                
                # Log trade dettagliato
                self.trade_logger.info(f"EXECUTED|{pair}|{signal['action']}|"
                                     f"{order_result.get('executedQty')}|"
                                     f"{order_result.get('price')}|"
                                     f"{order_result.get('orderId')}")
            
        except Exception as e:
            self.error_logger.error(f"❌ Errore esecuzione trade {pair}: {str(e)}")
    
    async def health_check(self):
        """Verifica salute dei componenti"""
        try:
            # Test connessione exchange
            balance = await self.exchange_manager.get_balance()
            if not balance:
                raise Exception("Connessione exchange fallita")
            
            # Test data loader
            latest_price = await self.data_loader.get_latest_price('BTCUSDT')
            if not latest_price:
                raise Exception("Data loader non risponde")
            
            # Test AI trading
            if not hasattr(self.ai_trading, 'prediction_model'):
                raise Exception("AI trading non inizializzato")
            
        except Exception as e:
            self.error_logger.error(f"❌ Health check fallito: {str(e)}")
            raise
    
    async def restart_components(self):
        """Riavvia i componenti in caso di errori"""
        try:
            self.logger.info("🔄 Riavvio componenti...")
            
            # Chiudi connessioni esistenti
            if hasattr(self, 'exchange_manager'):
                await self.exchange_manager.close()
            
            # Reinizializza
            success = await self.initialize_components()
            if success:
                self.consecutive_errors = 0
                self.logger.info("✅ Componenti riavviati con successo")
            else:
                self.logger.error("❌ Riavvio componenti fallito")
                
        except Exception as e:
            self.error_logger.error(f"❌ Errore riavvio: {str(e)}")
    
    def log_statistics(self):
        """Log statistiche periodiche"""
        uptime_hours = self.stats['uptime'] / 3600
        
        stats_msg = f"""
📊 STATISTICHE AURUMBOTX 24/7
{'='*40}
⏱️  Uptime: {uptime_hours:.1f} ore
🔄 Cicli completati: {self.stats['cycles_completed']}
🎯 Segnali generati: {self.stats['signals_generated']}
💹 Trade eseguiti: {self.stats['trades_executed']}
❌ Errori totali: {self.stats['errors_count']}
📈 Ultimo segnale: {self.stats['last_signal']['action'] if self.stats['last_signal'] else 'Nessuno'}
💰 Ultimo trade: {self.stats['last_trade']['action'] if self.stats['last_trade'] else 'Nessuno'}
🔧 Trading abilitato: {'Sì ✅' if self.config['enable_trading'] else 'No ⚠️'}
"""
        self.logger.info(stats_msg)
        
        # Salva statistiche su file
        with open(f'logs/stats_{datetime.now().strftime("%Y%m%d")}.json', 'w') as f:
            json.dump(self.stats, f, indent=2, default=str)
    
    def setup_signal_handlers(self):
        """Configura gestori per segnali di sistema"""
        def signal_handler(signum, frame):
            self.logger.info(f"🛑 Ricevuto segnale {signum}, arresto graceful...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """Loop principale del monitoraggio 24/7"""
        self.setup_signal_handlers()
        
        self.logger.info("🚀 AVVIO MONITORAGGIO AURUMBOTX 24/7")
        self.logger.info("="*50)
        
        # Inizializzazione
        if not await self.initialize_components():
            self.logger.error("❌ Inizializzazione fallita, arresto")
            return
        
        last_health_check = time.time()
        last_stats_log = time.time()
        
        try:
            while self.running:
                # Ciclo di monitoraggio
                await self.monitoring_cycle()
                
                # Health check periodico
                if time.time() - last_health_check > self.config['health_check_interval']:
                    await self.health_check()
                    last_health_check = time.time()
                
                # Log statistiche periodico
                if time.time() - last_stats_log > self.config['log_stats_interval']:
                    self.log_statistics()
                    last_stats_log = time.time()
                
                # Attesa prima del prossimo ciclo
                await asyncio.sleep(self.config['cycle_interval'])
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Interruzione da tastiera")
        except Exception as e:
            self.error_logger.error(f"❌ Errore critico nel loop principale: {str(e)}")
            self.error_logger.error(traceback.format_exc())
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Pulizia finale"""
        try:
            self.logger.info("🧹 Pulizia finale...")
            
            # Log statistiche finali
            self.log_statistics()
            
            # Chiudi connessioni
            if hasattr(self, 'exchange_manager'):
                await self.exchange_manager.close()
            
            self.logger.info("✅ Monitoraggio terminato correttamente")
            
        except Exception as e:
            self.error_logger.error(f"❌ Errore durante cleanup: {str(e)}")

if __name__ == "__main__":
    monitor = AurumBotMonitor()
    asyncio.run(monitor.run())
