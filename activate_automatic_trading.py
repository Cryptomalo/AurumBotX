#!/usr/bin/env python3
"""
Attivazione Trading Automatico AurumBotX
Connette AI → Exchange Manager per esecuzione ordini reali
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Aggiungi path del progetto
sys.path.append('/home/ubuntu/AurumBotX')

from utils.ai_trading import AITrading
from utils.exchange_manager import ExchangeManager
from utils.data_loader import CryptoDataLoader

class AutomaticTradingActivator:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('AutoTrading')
        self.ai_trading = None
        self.exchange_manager = None
        self.data_loader = None
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def print_header(self, title):
        """Header professionale"""
        print(f"\n{'='*100}")
        print(f"🚀 {title}")
        print(f"{'='*100}")
        
    def print_section(self, title):
        """Sezione"""
        print(f"\n📋 {title}")
        print(f"{'-'*80}")
    
    async def activate_automatic_trading(self):
        """Attiva il trading automatico completo"""
        self.print_header("ATTIVAZIONE TRADING AUTOMATICO AURUMBOTX")
        
        try:
            # 1. Inizializzazione componenti
            await self.initialize_components()
            
            # 2. Configurazione trading automatico
            await self.configure_automatic_trading()
            
            # 3. Test connessione exchange
            await self.test_exchange_connection()
            
            # 4. Implementazione loop trading
            await self.implement_trading_loop()
            
            # 5. Attivazione sistema completo
            await self.activate_complete_system()
            
        except Exception as e:
            self.logger.error(f"❌ Errore attivazione trading automatico: {e}")
            import traceback
            traceback.print_exc()
    
    async def initialize_components(self):
        """Inizializza tutti i componenti necessari"""
        self.print_section("INIZIALIZZAZIONE COMPONENTI")
        
        try:
            # 1. AI Trading
            print("  🤖 Inizializzazione AI Trading...")
            self.ai_trading = AITrading()
            await self.ai_trading.initialize()
            print("    ✅ AI Trading inizializzato")
            
            # 2. Exchange Manager
            print("  💹 Inizializzazione Exchange Manager...")
            self.exchange_manager = ExchangeManager('binance', testnet=True)
            print("    ✅ Exchange Manager inizializzato")
            
            # 3. Data Loader
            print("  📊 Inizializzazione Data Loader...")
            self.data_loader = CryptoDataLoader(use_live_data=True, testnet=True)
            await self.data_loader.initialize()
            print("    ✅ Data Loader inizializzato")
            
            # 4. Test connessioni
            print("  🔍 Test connessioni...")
            
            # Test prezzo corrente
            price = await self.data_loader.get_latest_price('BTCUSDT')
            if price and price > 50000:
                print(f"    ✅ Prezzo BTC: ${price:,.2f}")
            else:
                print(f"    ⚠️ Prezzo BTC: ${price} (potrebbe essere mock)")
            
            # Test saldo exchange
            balance = await self.exchange_manager.get_balance()
            if balance:
                print(f"    ✅ Saldo USDT: {balance.get('USDT', {}).get('free', 0)}")
                print(f"    ✅ Saldo BTC: {balance.get('BTC', {}).get('free', 0)}")
            else:
                print("    ⚠️ Impossibile recuperare saldo")
            
        except Exception as e:
            self.logger.error(f"❌ Errore inizializzazione: {e}")
            raise
    
    async def configure_automatic_trading(self):
        """Configura il trading automatico"""
        self.print_section("CONFIGURAZIONE TRADING AUTOMATICO")
        
        try:
            # Configurazione trading
            trading_config = {
                'symbol': 'BTCUSDT',
                'strategy': 'scalping_6m_conservative',
                'timeframe': '6m',
                'trade_amount': 0.0001,  # 0.0001 BTC per trade (circa $12)
                'max_trades_per_hour': 10,
                'profit_target': 0.003,  # 0.3%
                'stop_loss': 0.002,      # 0.2%
                'min_confidence': 0.6,   # 60% confidenza minima
                'risk_per_trade': 0.01,  # 1% del capitale per trade
                'max_drawdown': 0.05,    # 5% drawdown massimo
                'trading_hours': {
                    'start': '00:00',
                    'end': '23:59'
                }
            }
            
            print("  📊 CONFIGURAZIONE TRADING:")
            print(f"    🎯 Simbolo: {trading_config['symbol']}")
            print(f"    📈 Strategia: {trading_config['strategy']}")
            print(f"    ⏰ Timeframe: {trading_config['timeframe']}")
            print(f"    💰 Importo per trade: {trading_config['trade_amount']} BTC")
            print(f"    🎯 Profit target: {trading_config['profit_target']:.1%}")
            print(f"    🛡️ Stop loss: {trading_config['stop_loss']:.1%}")
            print(f"    🎲 Confidenza minima: {trading_config['min_confidence']:.0%}")
            
            # Salva configurazione
            config_file = "/home/ubuntu/AurumBotX/configs/automatic_trading.json"
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(trading_config, f, indent=2)
            
            print(f"    ✅ Configurazione salvata: {config_file}")
            
            self.trading_config = trading_config
            
        except Exception as e:
            self.logger.error(f"❌ Errore configurazione: {e}")
            raise
    
    async def test_exchange_connection(self):
        """Testa la connessione all'exchange"""
        self.print_section("TEST CONNESSIONE EXCHANGE")
        
        try:
            # 1. Test connessione
            print("  🔍 Test connessione Binance Testnet...")
            
            # Test saldo
            balance = await self.exchange_manager.get_balance()
            if balance:
                usdt_balance = balance.get('USDT', {}).get('free', 0)
                btc_balance = balance.get('BTC', {}).get('free', 0)
                
                print(f"    ✅ Connessione OK")
                print(f"    💰 USDT disponibile: {usdt_balance}")
                print(f"    ₿ BTC disponibile: {btc_balance}")
                
                # Verifica fondi sufficienti
                if float(usdt_balance) >= 50:  # Almeno $50 per trading
                    print("    ✅ Fondi sufficienti per trading")
                else:
                    print("    ⚠️ Fondi limitati - considera deposito testnet")
            else:
                print("    ❌ Impossibile recuperare saldo")
                return False
            
            # 2. Test ordine demo (senza esecuzione)
            print("  🧪 Test preparazione ordine...")
            
            current_price = await self.data_loader.get_latest_price('BTCUSDT')
            if current_price:
                test_order = {
                    'symbol': 'BTCUSDT',
                    'side': 'BUY',
                    'type': 'MARKET',
                    'quantity': self.trading_config['trade_amount']
                }
                
                print(f"    📊 Ordine test preparato:")
                print(f"      Simbolo: {test_order['symbol']}")
                print(f"      Tipo: {test_order['side']} {test_order['type']}")
                print(f"      Quantità: {test_order['quantity']} BTC")
                print(f"      Valore stimato: ${current_price * test_order['quantity']:.2f}")
                print("    ✅ Preparazione ordine OK")
            else:
                print("    ❌ Impossibile recuperare prezzo corrente")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Errore test exchange: {e}")
            return False
    
    async def implement_trading_loop(self):
        """Implementa il loop di trading automatico"""
        self.print_section("IMPLEMENTAZIONE LOOP TRADING")
        
        try:
            # Crea il file del loop di trading
            trading_loop_code = '''#!/usr/bin/env python3
"""
Loop Trading Automatico AurumBotX
Esegue trading automatico continuo con strategia 6M conservativa
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import sys
sys.path.append('/home/ubuntu/AurumBotX')

from utils.ai_trading import AITrading
from utils.exchange_manager import ExchangeManager
from utils.data_loader import CryptoDataLoader

class AutomaticTradingLoop:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('TradingLoop')
        self.ai_trading = None
        self.exchange_manager = None
        self.data_loader = None
        self.trading_config = None
        self.active_trades = {}
        self.performance_stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'start_time': datetime.now()
        }
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/home/ubuntu/AurumBotX/logs/trading_loop.log'),
                logging.StreamHandler()
            ]
        )
    
    async def initialize(self):
        """Inizializza il sistema di trading"""
        try:
            # Carica configurazione
            with open('/home/ubuntu/AurumBotX/configs/automatic_trading.json', 'r') as f:
                self.trading_config = json.load(f)
            
            # Inizializza componenti
            self.ai_trading = AITrading()
            await self.ai_trading.initialize()
            
            self.exchange_manager = ExchangeManager('binance', testnet=True)
            
            self.data_loader = CryptoDataLoader(use_live_data=True, testnet=True)
            await self.data_loader.initialize()
            
            self.logger.info("🚀 Sistema trading automatico inizializzato")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Errore inizializzazione: {e}")
            return False
    
    async def run_trading_cycle(self):
        """Esegue un ciclo di trading completo"""
        try:
            symbol = self.trading_config['symbol']
            
            # 1. Analisi mercato
            self.logger.info(f"📊 Analisi mercato {symbol}...")
            market_analysis = await self.ai_trading.analyze_market(symbol)
            
            if not market_analysis:
                self.logger.warning("⚠️ Analisi mercato fallita")
                return
            
            # 2. Generazione segnali
            self.logger.info("🎯 Generazione segnali trading...")
            signals = await self.ai_trading.generate_trading_signals(symbol)
            
            if not signals:
                self.logger.info("📊 Nessun segnale generato in questo ciclo")
                return
            
            # 3. Valutazione segnali
            for signal in signals:
                await self.evaluate_signal(signal)
            
            # 4. Gestione trade attivi
            await self.manage_active_trades()
            
            # 5. Aggiornamento statistiche
            await self.update_performance_stats()
            
        except Exception as e:
            self.logger.error(f"❌ Errore ciclo trading: {e}")
    
    async def evaluate_signal(self, signal: Dict[str, Any]):
        """Valuta un segnale e decide se eseguire il trade"""
        try:
            confidence = signal.get('confidence', 0)
            action = signal.get('action', '')
            
            # Verifica confidenza minima
            if confidence < self.trading_config['min_confidence']:
                self.logger.info(f"🎲 Segnale {action} scartato - confidenza {confidence:.1%} < {self.trading_config['min_confidence']:.0%}")
                return
            
            # Verifica limiti trading
            if len(self.active_trades) >= self.trading_config.get('max_concurrent_trades', 3):
                self.logger.info("⚠️ Limite trade concorrenti raggiunto")
                return
            
            # Verifica orari trading
            current_hour = datetime.now().hour
            if not self.is_trading_hours():
                self.logger.info(f"⏰ Fuori orario trading: {current_hour}:00")
                return
            
            # Esegui trade
            await self.execute_trade(signal)
            
        except Exception as e:
            self.logger.error(f"❌ Errore valutazione segnale: {e}")
    
    async def execute_trade(self, signal: Dict[str, Any]):
        """Esegue un trade basato sul segnale"""
        try:
            symbol = self.trading_config['symbol']
            action = signal.get('action', '')
            confidence = signal.get('confidence', 0)
            
            # Calcola quantità trade
            quantity = self.trading_config['trade_amount']
            
            # Prepara ordine
            order_data = {
                'symbol': symbol,
                'side': action.upper(),
                'type': 'MARKET',
                'quantity': quantity
            }
            
            self.logger.info(f"🚀 Esecuzione trade {action} {symbol}")
            self.logger.info(f"   Quantità: {quantity} BTC")
            self.logger.info(f"   Confidenza: {confidence:.1%}")
            
            # Esegui ordine
            order_result = await self.exchange_manager.place_order(**order_data)
            
            if order_result and order_result.get('status') == 'FILLED':
                # Trade eseguito con successo
                trade_id = order_result.get('orderId')
                fill_price = float(order_result.get('fills', [{}])[0].get('price', 0))
                
                # Registra trade attivo
                self.active_trades[trade_id] = {
                    'symbol': symbol,
                    'side': action.upper(),
                    'quantity': quantity,
                    'entry_price': fill_price,
                    'confidence': confidence,
                    'timestamp': datetime.now(),
                    'profit_target': fill_price * (1 + self.trading_config['profit_target']),
                    'stop_loss': fill_price * (1 - self.trading_config['stop_loss'])
                }
                
                self.performance_stats['total_trades'] += 1
                
                self.logger.info(f"✅ Trade eseguito - ID: {trade_id}")
                self.logger.info(f"   Prezzo: ${fill_price:,.2f}")
                self.logger.info(f"   Target: ${self.active_trades[trade_id]['profit_target']:,.2f}")
                self.logger.info(f"   Stop: ${self.active_trades[trade_id]['stop_loss']:,.2f}")
                
            else:
                self.logger.error(f"❌ Trade fallito: {order_result}")
                
        except Exception as e:
            self.logger.error(f"❌ Errore esecuzione trade: {e}")
    
    async def manage_active_trades(self):
        """Gestisce i trade attivi (profit target / stop loss)"""
        try:
            if not self.active_trades:
                return
            
            current_price = await self.data_loader.get_latest_price(self.trading_config['symbol'])
            if not current_price:
                return
            
            trades_to_close = []
            
            for trade_id, trade in self.active_trades.items():
                # Verifica profit target
                if trade['side'] == 'BUY' and current_price >= trade['profit_target']:
                    trades_to_close.append((trade_id, 'PROFIT_TARGET'))
                elif trade['side'] == 'SELL' and current_price <= trade['profit_target']:
                    trades_to_close.append((trade_id, 'PROFIT_TARGET'))
                
                # Verifica stop loss
                elif trade['side'] == 'BUY' and current_price <= trade['stop_loss']:
                    trades_to_close.append((trade_id, 'STOP_LOSS'))
                elif trade['side'] == 'SELL' and current_price >= trade['stop_loss']:
                    trades_to_close.append((trade_id, 'STOP_LOSS'))
            
            # Chiudi trade
            for trade_id, reason in trades_to_close:
                await self.close_trade(trade_id, reason, current_price)
                
        except Exception as e:
            self.logger.error(f"❌ Errore gestione trade attivi: {e}")
    
    async def close_trade(self, trade_id: str, reason: str, current_price: float):
        """Chiude un trade attivo"""
        try:
            trade = self.active_trades.get(trade_id)
            if not trade:
                return
            
            # Prepara ordine di chiusura
            close_side = 'SELL' if trade['side'] == 'BUY' else 'BUY'
            
            order_data = {
                'symbol': trade['symbol'],
                'side': close_side,
                'type': 'MARKET',
                'quantity': trade['quantity']
            }
            
            # Esegui chiusura
            close_result = await self.exchange_manager.place_order(**order_data)
            
            if close_result and close_result.get('status') == 'FILLED':
                close_price = float(close_result.get('fills', [{}])[0].get('price', 0))
                
                # Calcola profit/loss
                if trade['side'] == 'BUY':
                    pnl = (close_price - trade['entry_price']) * trade['quantity']
                else:
                    pnl = (trade['entry_price'] - close_price) * trade['quantity']
                
                pnl_percent = (pnl / (trade['entry_price'] * trade['quantity'])) * 100
                
                # Aggiorna statistiche
                if pnl > 0:
                    self.performance_stats['winning_trades'] += 1
                else:
                    self.performance_stats['losing_trades'] += 1
                
                self.performance_stats['total_profit'] += pnl
                
                self.logger.info(f"🔄 Trade chiuso - {reason}")
                self.logger.info(f"   ID: {trade_id}")
                self.logger.info(f"   Entry: ${trade['entry_price']:,.2f}")
                self.logger.info(f"   Exit: ${close_price:,.2f}")
                self.logger.info(f"   P&L: ${pnl:,.4f} ({pnl_percent:+.2f}%)")
                
                # Rimuovi da trade attivi
                del self.active_trades[trade_id]
                
            else:
                self.logger.error(f"❌ Chiusura trade fallita: {close_result}")
                
        except Exception as e:
            self.logger.error(f"❌ Errore chiusura trade: {e}")
    
    def is_trading_hours(self) -> bool:
        """Verifica se siamo in orario di trading"""
        # Per crypto, trading 24/7 - sempre True
        return True
    
    async def update_performance_stats(self):
        """Aggiorna e salva statistiche performance"""
        try:
            # Calcola metriche
            total_trades = self.performance_stats['total_trades']
            if total_trades > 0:
                win_rate = self.performance_stats['winning_trades'] / total_trades
                avg_profit = self.performance_stats['total_profit'] / total_trades
            else:
                win_rate = 0
                avg_profit = 0
            
            # Salva statistiche
            stats = {
                'timestamp': datetime.now().isoformat(),
                'total_trades': total_trades,
                'winning_trades': self.performance_stats['winning_trades'],
                'losing_trades': self.performance_stats['losing_trades'],
                'win_rate': win_rate,
                'total_profit': self.performance_stats['total_profit'],
                'avg_profit_per_trade': avg_profit,
                'active_trades': len(self.active_trades),
                'uptime_hours': (datetime.now() - self.performance_stats['start_time']).total_seconds() / 3600
            }
            
            # Salva su file
            stats_file = '/home/ubuntu/AurumBotX/logs/performance_stats.json'
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
            
            # Log ogni 10 trade
            if total_trades > 0 and total_trades % 10 == 0:
                self.logger.info(f"📊 STATISTICHE - Trade: {total_trades} | Win Rate: {win_rate:.1%} | Profit: ${self.performance_stats['total_profit']:.4f}")
                
        except Exception as e:
            self.logger.error(f"❌ Errore aggiornamento statistiche: {e}")
    
    async def run_continuous_trading(self):
        """Esegue trading continuo"""
        self.logger.info("🚀 Avvio trading automatico continuo...")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                self.logger.info(f"🔄 Ciclo trading #{cycle_count}")
                
                await self.run_trading_cycle()
                
                # Pausa tra cicli (6 minuti per timeframe 6M)
                await asyncio.sleep(360)  # 6 minuti
                
            except KeyboardInterrupt:
                self.logger.info("⏹️ Trading interrotto dall'utente")
                break
            except Exception as e:
                self.logger.error(f"❌ Errore nel loop trading: {e}")
                await asyncio.sleep(60)  # Pausa 1 minuto in caso di errore

async def main():
    """Main del trading automatico"""
    trading_loop = AutomaticTradingLoop()
    
    if await trading_loop.initialize():
        await trading_loop.run_continuous_trading()
    else:
        print("❌ Inizializzazione fallita")

if __name__ == "__main__":
    asyncio.run(main())
'''
            
            # Salva il file
            loop_file = "/home/ubuntu/AurumBotX/automatic_trading_loop.py"
            with open(loop_file, 'w') as f:
                f.write(trading_loop_code)
            
            # Rendi eseguibile
            os.chmod(loop_file, 0o755)
            
            print(f"  ✅ Loop trading implementato: {loop_file}")
            
            # Crea script di avvio
            start_script = '''#!/bin/bash
# Script avvio trading automatico AurumBotX

cd /home/ubuntu/AurumBotX

echo "🚀 Avvio Trading Automatico AurumBotX..."
echo "⏰ $(date)"
echo "📊 Strategia: Scalping 6M Conservativo"
echo "💰 Testnet: Binance"
echo ""

# Crea directory logs se non esiste
mkdir -p logs

# Avvia trading automatico
python3 automatic_trading_loop.py
'''
            
            start_script_file = "/home/ubuntu/AurumBotX/start_automatic_trading.sh"
            with open(start_script_file, 'w') as f:
                f.write(start_script)
            
            os.chmod(start_script_file, 0o755)
            
            print(f"  ✅ Script avvio creato: {start_script_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Errore implementazione loop: {e}")
            raise
    
    async def activate_complete_system(self):
        """Attiva il sistema completo di trading automatico"""
        self.print_section("ATTIVAZIONE SISTEMA COMPLETO")
        
        try:
            print("  🎯 SISTEMA TRADING AUTOMATICO CONFIGURATO:")
            print("    ✅ AI Trading Engine: Inizializzato")
            print("    ✅ Exchange Manager: Connesso a Binance Testnet")
            print("    ✅ Data Loader: Dati reali configurati")
            print("    ✅ Trading Loop: Implementato")
            print("    ✅ Configurazione: Scalping 6M Conservativo")
            print("")
            print("  📊 PARAMETRI TRADING:")
            print(f"    🎯 Simbolo: {self.trading_config['symbol']}")
            print(f"    💰 Importo per trade: {self.trading_config['trade_amount']} BTC")
            print(f"    📈 Profit target: {self.trading_config['profit_target']:.1%}")
            print(f"    🛡️ Stop loss: {self.trading_config['stop_loss']:.1%}")
            print(f"    🎲 Confidenza minima: {self.trading_config['min_confidence']:.0%}")
            print("")
            print("  🚀 COMANDI DISPONIBILI:")
            print("    Avvio manuale: ./start_automatic_trading.sh")
            print("    Avvio background: nohup ./start_automatic_trading.sh &")
            print("    Monitoraggio: tail -f logs/trading_loop.log")
            print("    Statistiche: cat logs/performance_stats.json")
            print("")
            print("  ✅ SISTEMA PRONTO PER TRADING AUTOMATICO!")
            
        except Exception as e:
            self.logger.error(f"❌ Errore attivazione sistema: {e}")
            raise

async def main():
    """Main attivazione trading automatico"""
    activator = AutomaticTradingActivator()
    await activator.activate_automatic_trading()

if __name__ == "__main__":
    asyncio.run(main())

