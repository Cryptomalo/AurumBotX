#!/usr/bin/env python3
"""
🚀 TEST TRADING AUTOMATICO AURUMBOTX
Capitale Iniziale: 1000€
Modalità: 24/7 Operativo
Monitoraggio: Performance Visive + Trade Tracking
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timedelta
import pandas as pd
import sqlite3

# Aggiungi path per import
sys.path.append('.')

# Import moduli AurumBotX
from utils.data_loader import CryptoDataLoader
from utils.exchange_manager import ExchangeManager
from utils.ai_trading import AITrading
from utils.database_manager import DatabaseManager

class TradingTest1000Euro:
    def __init__(self):
        self.initial_capital = 1000.0  # 1000€ capitale iniziale
        self.current_balance = 1000.0
        self.trades_executed = []
        self.performance_data = []
        self.start_time = datetime.now()
        
        # Setup database per tracking
        self.setup_test_database()
        
        # Inizializza componenti
        self.data_loader = None
        self.exchange_manager = None
        self.ai_trading = None
        
        print(f"🚀 INIZIALIZZAZIONE TEST TRADING AUTOMATICO")
        print(f"💰 Capitale Iniziale: {self.initial_capital}€")
        print(f"📅 Inizio Test: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
    
    def setup_test_database(self):
        """Setup database per tracking test"""
        try:
            conn = sqlite3.connect('test_trading_1000_euro.db')
            cursor = conn.cursor()
            
            # Tabella trade
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    symbol TEXT,
                    action TEXT,
                    amount REAL,
                    price REAL,
                    confidence REAL,
                    profit_loss REAL,
                    balance_after REAL,
                    status TEXT
                )
            ''')
            
            # Tabella performance
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    balance REAL,
                    total_profit REAL,
                    roi_percentage REAL,
                    trades_count INTEGER,
                    win_rate REAL
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ Database test inizializzato")
        except Exception as e:
            print(f"❌ Errore setup database: {e}")
    
    async def initialize_components(self):
        """Inizializza componenti trading"""
        try:
            print("🔧 Inizializzazione componenti...")
            
            # Data Loader
            self.data_loader = CryptoDataLoader()
            print("✅ Data Loader inizializzato")
            
            # Exchange Manager (Testnet)
            self.exchange_manager = ExchangeManager('binance', testnet=True)
            print("✅ Exchange Manager inizializzato (Testnet)")
            
            # AI Trading
            self.ai_trading = AITrading()
            print("✅ AI Trading inizializzato")
            
            # Test connessioni
            price = await self.data_loader.get_latest_price('BTCUSDT')
            print(f"✅ Prezzo BTC corrente: ${price:,.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione: {e}")
            return False
    
    def calculate_position_size(self, price, confidence):
        """Calcola dimensione posizione basata su capitale e confidenza"""
        # Risk management: max 2% del capitale per trade
        max_risk_per_trade = self.current_balance * 0.02
        
        # Aggiusta per confidenza (più confidenza = posizione più grande)
        confidence_multiplier = min(confidence / 0.7, 1.5)  # Max 1.5x
        
        # Calcola importo in USD
        trade_amount_usd = max_risk_per_trade * confidence_multiplier
        
        # Converti in BTC
        trade_amount_btc = trade_amount_usd / price
        
        # Minimo 0.00001 BTC per Binance
        trade_amount_btc = max(trade_amount_btc, 0.00001)
        
        return trade_amount_btc, trade_amount_usd
    
    def execute_simulated_trade(self, signal, price, confidence):
        """Esegui trade simulato con capitale reale tracking"""
        try:
            action = signal.lower()
            amount_btc, amount_usd = self.calculate_position_size(price, confidence)
            
            # Simula esecuzione trade
            if action == 'buy':
                if self.current_balance >= amount_usd:
                    # Esegui BUY
                    self.current_balance -= amount_usd
                    profit_loss = 0  # Profit/loss sarà calcolato alla vendita
                    status = 'EXECUTED'
                else:
                    status = 'INSUFFICIENT_BALANCE'
                    profit_loss = 0
            
            elif action == 'sell':
                # Simula SELL (assumiamo di avere posizione)
                # Per semplicità, generiamo profit/loss casuale basato su confidenza
                profit_percentage = (confidence - 0.5) * 0.02  # -1% a +1% circa
                profit_loss = amount_usd * profit_percentage
                self.current_balance += amount_usd + profit_loss
                status = 'EXECUTED'
            
            else:
                status = 'HOLD'
                profit_loss = 0
            
            # Registra trade
            trade_record = {
                'timestamp': datetime.now().isoformat(),
                'symbol': 'BTCUSDT',
                'action': action.upper(),
                'amount': amount_btc,
                'price': price,
                'confidence': confidence,
                'profit_loss': profit_loss,
                'balance_after': self.current_balance,
                'status': status
            }
            
            self.trades_executed.append(trade_record)
            
            # Salva in database
            self.save_trade_to_db(trade_record)
            
            # Log trade
            print(f"📊 TRADE ESEGUITO:")
            print(f"   Action: {action.upper()}")
            print(f"   Amount: {amount_btc:.5f} BTC (${amount_usd:.2f})")
            print(f"   Price: ${price:,.2f}")
            print(f"   Confidence: {confidence:.1%}")
            print(f"   P&L: ${profit_loss:.2f}")
            print(f"   Balance: ${self.current_balance:.2f}")
            print(f"   Status: {status}")
            print("-" * 40)
            
            return trade_record
            
        except Exception as e:
            print(f"❌ Errore esecuzione trade: {e}")
            return None
    
    def save_trade_to_db(self, trade):
        """Salva trade in database"""
        try:
            conn = sqlite3.connect('test_trading_1000_euro.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trades (timestamp, symbol, action, amount, price, confidence, profit_loss, balance_after, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade['timestamp'],
                trade['symbol'],
                trade['action'],
                trade['amount'],
                trade['price'],
                trade['confidence'],
                trade['profit_loss'],
                trade['balance_after'],
                trade['status']
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Errore salvataggio trade: {e}")
    
    def save_performance_to_db(self):
        """Salva performance corrente in database"""
        try:
            total_profit = self.current_balance - self.initial_capital
            roi_percentage = (total_profit / self.initial_capital) * 100
            
            executed_trades = [t for t in self.trades_executed if t['status'] == 'EXECUTED']
            winning_trades = [t for t in executed_trades if t['profit_loss'] > 0]
            win_rate = (len(winning_trades) / len(executed_trades) * 100) if executed_trades else 0
            
            conn = sqlite3.connect('test_trading_1000_euro.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance (timestamp, balance, total_profit, roi_percentage, trades_count, win_rate)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                self.current_balance,
                total_profit,
                roi_percentage,
                len(executed_trades),
                win_rate
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Errore salvataggio performance: {e}")
    
    def print_performance_summary(self):
        """Stampa riassunto performance"""
        total_profit = self.current_balance - self.initial_capital
        roi_percentage = (total_profit / self.initial_capital) * 100
        
        executed_trades = [t for t in self.trades_executed if t['status'] == 'EXECUTED']
        winning_trades = [t for t in executed_trades if t['profit_loss'] > 0]
        losing_trades = [t for t in executed_trades if t['profit_loss'] < 0]
        
        win_rate = (len(winning_trades) / len(executed_trades) * 100) if executed_trades else 0
        
        uptime = datetime.now() - self.start_time
        
        print("\n" + "="*60)
        print("📊 PERFORMANCE SUMMARY")
        print("="*60)
        print(f"💰 Capitale Iniziale: {self.initial_capital:.2f}€")
        print(f"💰 Balance Corrente: {self.current_balance:.2f}€")
        print(f"📈 Profit/Loss Totale: {total_profit:.2f}€")
        print(f"📊 ROI: {roi_percentage:.2f}%")
        print(f"🎯 Trade Totali: {len(self.trades_executed)}")
        print(f"✅ Trade Eseguiti: {len(executed_trades)}")
        print(f"🟢 Trade Vincenti: {len(winning_trades)}")
        print(f"🔴 Trade Perdenti: {len(losing_trades)}")
        print(f"📊 Win Rate: {win_rate:.1f}%")
        print(f"⏱️ Uptime: {uptime}")
        print("="*60)
    
    async def trading_loop(self):
        """Loop principale trading 24/7"""
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                cycle_start = time.time()
                
                print(f"\n🔄 CICLO {cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                # Ottieni prezzo corrente
                current_price = await self.data_loader.get_latest_price('BTCUSDT')
                print(f"💹 Prezzo BTC: ${current_price:,.2f}")
                
                # Genera segnale AI
                signal_data = await self.ai_trading.generate_trading_signals('BTCUSDT')
                
                if signal_data and 'action' in signal_data:
                    action = signal_data['action']
                    confidence = signal_data.get('confidence', 0.6)
                    
                    print(f"🎯 Segnale: {action.upper()} | Confidenza: {confidence:.1%}")
                    
                    # Esegui trade se confidenza sufficiente
                    if confidence >= 0.6 and action.lower() in ['buy', 'sell']:
                        trade_result = self.execute_simulated_trade(action, current_price, confidence)
                        
                        if trade_result:
                            # Salva performance
                            self.save_performance_to_db()
                    else:
                        print(f"⏸️ Segnale ignorato (confidenza {confidence:.1%} < 60%)")
                else:
                    print("⚠️ Nessun segnale generato")
                
                # Performance summary ogni 10 cicli
                if cycle_count % 10 == 0:
                    self.print_performance_summary()
                
                # Tempo ciclo
                cycle_time = time.time() - cycle_start
                print(f"⏱️ Ciclo completato in {cycle_time:.2f}s")
                
                # Attendi prossimo ciclo (5 minuti)
                await asyncio.sleep(300)  # 5 minuti
                
            except KeyboardInterrupt:
                print("\n🛑 Test interrotto dall'utente")
                break
            except Exception as e:
                print(f"❌ Errore nel ciclo trading: {e}")
                await asyncio.sleep(60)  # Attendi 1 minuto prima di riprovare
        
        # Performance finale
        self.print_performance_summary()
    
    async def run_test(self):
        """Avvia test trading automatico"""
        print("🚀 AVVIO TEST TRADING AUTOMATICO 24/7")
        print("💰 Capitale: 1000€")
        print("🎯 Modalità: Simulazione Realistica")
        print("📊 Monitoraggio: Performance Visive")
        print("\n⏱️ Inizializzazione componenti...")
        
        # Inizializza componenti
        if not await self.initialize_components():
            print("❌ Errore inizializzazione. Test terminato.")
            return
        
        print("\n✅ Tutti i componenti inizializzati con successo!")
        print("🔄 Avvio loop trading 24/7...")
        print("📊 Performance verranno salvate ogni ciclo")
        print("📈 Summary ogni 10 cicli")
        print("\n🛑 Premi Ctrl+C per fermare il test")
        print("="*60)
        
        # Avvia loop trading
        await self.trading_loop()

async def main():
    """Funzione principale"""
    test = TradingTest1000Euro()
    await test.run_test()

if __name__ == "__main__":
    asyncio.run(main())

