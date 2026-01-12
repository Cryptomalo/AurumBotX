#!/usr/bin/env python3
"""
AurumBotX Mega-Aggressive Trading System
Sistema di trading mega-aggressivo con position size 25% e target 20-50 euro per trade
"""

import os
import sys
import time
import random
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
import math

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/mega_aggressive.log'),
        logging.StreamHandler()
    ]
)

class MegaDataGenerator:
    """Generatore dati mega-volatili per trading aggressivo"""
    
    def __init__(self):
        self.logger = logging.getLogger('MegaDataGen')
        self.base_price = 50000  # Prezzo base BTC
        
    def generate_mega_volatile_data(self, symbol="BTCUSDT", count=20):
        """Genera dati con volatilità estrema per profitti 20-50 euro"""
        try:
            data = []
            current_price = self.base_price
            
            for i in range(count):
                # Volatilità estrema: 15-25% per candela
                volatility = random.uniform(0.15, 0.25)
                direction = random.choice([-1, 1])
                
                # Movimento prezzo estremo
                price_change = current_price * volatility * direction
                current_price = max(20000, min(150000, current_price + price_change))
                
                # Volume alto per liquidità
                volume = random.uniform(1000, 5000)
                
                timestamp = datetime.now() - timedelta(minutes=(count-i)*2)
                
                candle = {
                    'timestamp': timestamp.isoformat(),
                    'symbol': symbol,
                    'open': current_price * random.uniform(0.98, 1.02),
                    'high': current_price * random.uniform(1.05, 1.15),
                    'low': current_price * random.uniform(0.85, 0.95),
                    'close': current_price,
                    'volume': volume,
                    'volatility': volatility
                }
                
                data.append(candle)
            
            self.logger.info(f"✅ Dati mega-volatili generati: {count} candele per {symbol}")
            self.logger.info(f"📊 Range prezzo: ${min(d['close'] for d in data):.0f} - ${max(d['close'] for d in data):.0f}")
            self.logger.info(f"⚡ Volatilità media: {np.mean([d['volatility'] for d in data])*100:.1f}%")
            
            return data
            
        except Exception as e:
            self.logger.error(f"❌ Errore generazione dati: {e}")
            return []

class MegaAI:
    """AI mega-aggressiva per segnali ad alto profitto"""
    
    def __init__(self):
        self.logger = logging.getLogger('MegaAI')
        
    def generate_mega_signal(self, data, current_balance):
        """Genera segnale mega-aggressivo per profitti 20-50 euro"""
        try:
            if not data:
                return None, 0.0
            
            # Analisi volatilità estrema
            latest = data[-1]
            volatility = latest['volatility']
            price = latest['close']
            
            # Calcola trend mega-aggressivo
            prices = [d['close'] for d in data[-5:]]
            trend_strength = abs(prices[-1] - prices[0]) / prices[0]
            
            # Segnale basato su volatilità estrema
            if volatility > 0.18:  # Volatilità molto alta
                if trend_strength > 0.10:  # Trend forte
                    signal = "BUY" if prices[-1] > prices[-2] else "SELL"
                    confidence = min(0.95, 0.60 + volatility + trend_strength)
                else:
                    signal = "SELL" if random.random() > 0.4 else "BUY"
                    confidence = min(0.90, 0.50 + volatility)
            else:
                # Forza segnale anche con volatilità media
                signal = random.choice(["BUY", "SELL"])
                confidence = min(0.85, 0.40 + volatility + random.uniform(0.1, 0.3))
            
            self.logger.info(f"🎯 Segnale mega-aggressivo: {signal} (conf: {confidence:.1%})")
            
            return signal, confidence
            
        except Exception as e:
            self.logger.error(f"❌ Errore generazione segnale: {e}")
            return None, 0.0

class MegaAggressiveEngine:
    """Engine di trading mega-aggressivo"""
    
    def __init__(self):
        self.logger = logging.getLogger('MegaEngine')
        self.db_name = 'mega_aggressive_trading.db'
        self.balance = 1000.0
        self.initial_balance = 1000.0
        
        # Parametri mega-aggressivi
        self.min_confidence = 0.20  # Soglia molto bassa
        self.base_position_size = 0.25  # 25% del capitale (1/4)
        self.max_position_size = 0.35   # Fino a 35% in casi estremi
        self.target_profit_min = 20.0   # Minimo 20 euro per trade
        self.target_profit_max = 50.0   # Massimo 50 euro per trade
        
        # Generatori
        self.data_gen = MegaDataGenerator()
        self.ai = MegaAI()
        
        # Setup database
        self.setup_database()
        
    def setup_database(self):
        """Setup database mega-aggressivo"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mega_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    amount REAL NOT NULL,
                    price REAL NOT NULL,
                    profit_loss REAL NOT NULL,
                    fee REAL NOT NULL,
                    balance_before REAL NOT NULL,
                    balance_after REAL NOT NULL,
                    position_size_percent REAL NOT NULL,
                    confidence REAL NOT NULL,
                    volatility REAL NOT NULL,
                    target_profit REAL NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info("✅ Database mega-aggressivo inizializzato")
            
        except Exception as e:
            self.logger.error(f"❌ Errore setup database: {e}")
    
    def calculate_mega_position_size(self, confidence, volatility, target_profit):
        """Calcola position size mega-aggressiva per target 20-50 euro"""
        try:
            # Base: 25% del capitale
            base_size = self.base_position_size
            
            # Moltiplicatori per raggiungere target profit
            confidence_multiplier = 1.0 + (confidence - 0.5) * 0.5  # 0.75 - 1.25
            volatility_multiplier = 1.0 + volatility * 0.8  # 1.0 - 1.2
            
            # Calcola size per raggiungere target profit
            target_multiplier = target_profit / 20.0  # 1.0 - 2.5 per 20-50 euro
            
            # Position size finale
            position_size = base_size * confidence_multiplier * volatility_multiplier * target_multiplier
            
            # Limiti di sicurezza
            position_size = max(0.15, min(self.max_position_size, position_size))
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"❌ Errore calcolo position size: {e}")
            return self.base_position_size
    
    def execute_mega_trade(self, signal, confidence, price, volatility):
        """Esegue trade mega-aggressivo"""
        try:
            # Target profit dinamico basato su confidence e volatilità
            target_profit = self.target_profit_min + (self.target_profit_max - self.target_profit_min) * confidence
            
            # Calcola position size mega-aggressiva
            position_size_percent = self.calculate_mega_position_size(confidence, volatility, target_profit)
            
            # Calcola importo trade
            trade_amount = self.balance * position_size_percent
            
            # Simula esecuzione con profitto amplificato
            profit_factor = random.uniform(0.8, 1.5)  # Fattore di amplificazione
            base_profit = trade_amount * volatility * profit_factor
            
            # Applica direzione del segnale
            if signal == "BUY":
                profit_loss = base_profit * random.uniform(0.5, 2.0)
            else:  # SELL
                profit_loss = base_profit * random.uniform(0.3, 1.8)
            
            # Aggiungi variabilità per realismo
            if random.random() < 0.25:  # 25% chance di perdita
                profit_loss *= -random.uniform(0.3, 0.8)
            
            # Scala per raggiungere target 20-50 euro
            if abs(profit_loss) < target_profit * 0.5:
                profit_loss *= target_profit / max(abs(profit_loss), 1.0)
            
            # Fee proporzionale
            fee = trade_amount * 0.001  # 0.1% fee
            
            # Aggiorna balance
            balance_before = self.balance
            self.balance += profit_loss - fee
            
            # Salva trade
            self.save_mega_trade(signal, trade_amount, price, profit_loss, fee, 
                               balance_before, self.balance, position_size_percent, 
                               confidence, volatility, target_profit)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Errore esecuzione trade: {e}")
            return False
    
    def save_mega_trade(self, action, amount, price, profit_loss, fee, 
                       balance_before, balance_after, position_size_percent, 
                       confidence, volatility, target_profit):
        """Salva trade mega-aggressivo nel database"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO mega_trades 
                (timestamp, action, amount, price, profit_loss, fee, 
                 balance_before, balance_after, position_size_percent, 
                 confidence, volatility, target_profit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                action,
                amount,
                price,
                profit_loss,
                fee,
                balance_before,
                balance_after,
                position_size_percent * 100,  # Salva come percentuale
                confidence,
                volatility,
                target_profit
            ))
            
            conn.commit()
            conn.close()
            
            # Log dettagliato
            profit_emoji = "💚" if profit_loss > 0 else "❤️"
            self.logger.info(f"💰 TRADE MEGA-AGGRESSIVO ESEGUITO!")
            self.logger.info(f"📊 {action} ${amount:.2f} @ ${price:.0f} (pos: {position_size_percent*100:.1f}%)")
            self.logger.info(f"{profit_emoji} P&L: ${profit_loss:.2f}, Fee: ${fee:.2f}")
            self.logger.info(f"💰 Balance: ${balance_before:.2f} → ${balance_after:.2f}")
            self.logger.info(f"🎯 Target: ${target_profit:.2f}, Volatility: {volatility:.1%}")
            
        except Exception as e:
            self.logger.error(f"❌ Errore salvataggio trade: {e}")
    
    def get_mega_stats(self):
        """Ottieni statistiche mega-aggressive"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_trades,
                    COUNT(CASE WHEN profit_loss > 0 THEN 1 END) as winning_trades,
                    SUM(profit_loss) as total_pnl,
                    SUM(fee) as total_fees,
                    AVG(profit_loss) as avg_pnl,
                    AVG(position_size_percent) as avg_position_size,
                    AVG(target_profit) as avg_target_profit
                FROM mega_trades
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] > 0:
                total_trades, winning_trades, total_pnl, total_fees, avg_pnl, avg_pos_size, avg_target = result
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                roi = ((self.balance - self.initial_balance) / self.initial_balance * 100)
                
                self.logger.info(f"📊 Stats Mega-Aggressive: {total_trades} trades, "
                               f"{win_rate:.1f}% win rate, ${total_fees:.2f} fees, {roi:.2f}% ROI")
                self.logger.info(f"💰 Avg P&L: ${avg_pnl:.2f}, Avg Target: ${avg_target:.2f}, Avg Pos: {avg_pos_size:.1f}%")
            
        except Exception as e:
            self.logger.error(f"❌ Errore statistiche: {e}")
    
    def run_mega_cycle(self):
        """Esegue ciclo mega-aggressivo"""
        try:
            start_time = time.time()
            
            # Genera dati mega-volatili
            data = self.data_gen.generate_mega_volatile_data()
            if not data:
                return False
            
            # Genera segnale mega-aggressivo
            signal, confidence = self.ai.generate_mega_signal(data, self.balance)
            if not signal:
                return False
            
            # Controlla soglia minima
            if confidence < self.min_confidence:
                self.logger.info(f"⚠️ Confidence troppo bassa: {confidence:.1%} < {self.min_confidence:.1%}")
                return False
            
            # Esegui trade mega-aggressivo
            latest_price = data[-1]['close']
            latest_volatility = data[-1]['volatility']
            
            success = self.execute_mega_trade(signal, confidence, latest_price, latest_volatility)
            
            if success:
                self.get_mega_stats()
            
            # Log timing
            elapsed = time.time() - start_time
            self.logger.info(f"✅ Ciclo mega-aggressivo completato in {elapsed:.2f}s")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Errore ciclo mega-aggressivo: {e}")
            return False

def main():
    """Funzione principale"""
    print("🔥 AurumBotX Mega-Aggressive Trading System")
    print("=" * 60)
    print("💰 OBIETTIVO: 20-50 euro per trade")
    print("📊 POSITION SIZE: 25% del capitale (1/4)")
    print("⚡ VOLATILITÀ: Estrema (15-25%)")
    print("🎯 TARGET: Profitti amplificati")
    print("=" * 60)
    
    # Setup
    os.makedirs('logs', exist_ok=True)
    
    # Inizializza engine
    engine = MegaAggressiveEngine()
    
    try:
        cycle_count = 0
        while True:
            cycle_count += 1
            
            print(f"\n🔄 CICLO MEGA-AGGRESSIVO #{cycle_count}")
            print("-" * 40)
            
            # Esegui ciclo
            success = engine.run_mega_cycle()
            
            if success:
                print("✅ Trade mega-aggressivo eseguito!")
            else:
                print("⚠️ Nessun trade eseguito questo ciclo")
            
            # Pausa tra cicli (60 secondi per maggiore aggressività)
            print(f"⏰ Prossimo ciclo in 60 secondi...")
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n🛑 Sistema mega-aggressivo fermato dall'utente")
        engine.get_mega_stats()
    except Exception as e:
        print(f"\n❌ Errore sistema: {e}")

if __name__ == "__main__":
    main()

