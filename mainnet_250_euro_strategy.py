#!/usr/bin/env python3
"""
AurumBotX Mainnet Strategy - €250 Capital
Strategia Mega-Mainnet adattata per capitale €250
"""

import sqlite3
import time
from datetime import datetime
import random
import json

class Mainnet250EuroStrategy:
    """Strategia Mainnet con capitale €250"""
    
    def __init__(self):
        self.db_name = "mainnet_250_euro.db"
        self.log_file = "logs/mainnet_250_euro.log"
        self.initial_balance = 250.0
        self.current_balance = self.initial_balance
        self.conn = None
        self.cursor = None
        self.trade_count = 0
        
        self.setup_database()
        self.log("🚀 Avvio Mainnet Strategy - €250 Capital")
    
    def log(self, message):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def setup_database(self):
        """Setup database SQLite"""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS mainnet_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                amount REAL NOT NULL,
                price REAL NOT NULL,
                confidence REAL NOT NULL,
                profit_loss REAL NOT NULL,
                balance_after REAL NOT NULL,
                position_size_percent REAL NOT NULL,
                market_conditions TEXT,
                ai_signals TEXT,
                risk_metrics TEXT
            );
        """)
        self.conn.commit()
        
        # Recupera ultimo balance
        self.cursor.execute("SELECT balance_after FROM mainnet_trades ORDER BY id DESC LIMIT 1")
        last_balance = self.cursor.fetchone()
        if last_balance:
            self.current_balance = last_balance[0]
            self.log(f"💰 Balance recuperato: €{self.current_balance:.2f}")
        else:
            self.log(f"💰 Balance iniziale: €{self.initial_balance:.2f}")
    
    def get_market_data(self):
        """Simula dati mercato mainnet"""
        # Volatilità reale (1-5% per ora)
        price_change = random.uniform(-0.02, 0.02)
        current_price = 65000 * (1 + price_change)
        
        # AI Confidence (più conservativa)
        confidence = random.uniform(0.4, 0.9)
        
        # Segnale AI
        action = "BUY" if random.random() > 0.5 else "SELL"
        
        return current_price, confidence, action
    
    def calculate_position_size(self, confidence):
        """Calcola position size dinamica"""
        # Base size 8-15%
        base_size = 0.08 + (0.07 * confidence)
        
        # Aggiustamento per balance
        if self.current_balance < 500:
            base_size *= 0.8 # Riduci rischio per capitali bassi
        
        return min(base_size, 0.20) # Max 20%
    
    def execute_trade(self):
        """Esegue un trade"""
        self.trade_count += 1
        self.log(f"\n🔄 Ciclo Trade #{self.trade_count}")
        
        price, confidence, action = self.get_market_data()
        
        if confidence < 0.55: # Soglia più alta per mainnet
            self.log(f"⚠️ Confidence {confidence:.2f} troppo bassa, no trade")
            return
        
        position_size_percent = self.calculate_position_size(confidence)
        trade_amount_euro = self.current_balance * position_size_percent
        
        # Profit/Loss realistico (0.4-1.5%)
        profit_percent = random.uniform(-0.01, 0.015) * (1 if action == "BUY" else -1)
        profit_loss = trade_amount_euro * profit_percent
        
        # Slippage e costi (0.1%)
        costs = trade_amount_euro * 0.001
        profit_loss -= costs
        
        self.current_balance += profit_loss
        
        # Log trade
        self.log(f"🔥 Eseguito {action} {trade_amount_euro:.2f}€ @ {price:.2f}€")
        self.log(f"  - Confidence: {confidence:.2f}")
        self.log(f"  - Position Size: {position_size_percent*100:.1f}%")
        self.log(f"  - Profit/Loss: {profit_loss:+.2f}€")
        self.log(f"  - Balance: €{self.current_balance:.2f}")
        
        # Salva in database
        self.cursor.execute("""
            INSERT INTO mainnet_trades (timestamp, action, amount, price, confidence, profit_loss, balance_after, position_size_percent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            action,
            trade_amount_euro,
            price,
            confidence,
            profit_loss,
            self.current_balance,
            position_size_percent * 100
        ))
        self.conn.commit()
    
    def run(self):
        """Avvia ciclo di trading"""
        while True:
            try:
                self.execute_trade()
                time.sleep(random.uniform(30, 90)) # Frequenza più bassa
            except KeyboardInterrupt:
                self.log("🛑 Bot fermato manualmente")
                self.conn.close()
                break
            except Exception as e:
                self.log(f"❌ ERRORE CRITICO: {e}")
                time.sleep(60)

def main():
    """Funzione principale"""
    strategy = Mainnet250EuroStrategy()
    strategy.run()

if __name__ == "__main__":
    main()

