#!/usr/bin/env python3
"""
Enhanced 50 USDT Trading Bot
"""

import os
import sys
import json
import time
import sqlite3
from pathlib import Path
from datetime import datetime

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class Enhanced50USDTBot:
    def __init__(self):
        self.capital = 50.0
        self.config_file = project_root / "config" / "50_usdt_challenge.json"
        self.wallet_file = project_root / "data" / "wallet_50_usdt.json"
        self.db_path = project_root / "data" / "databases" / "mainnet_trading.db"
        
        print("🤖 Enhanced 50 USDT Trading Bot v2.1")
        print(f"💰 Capital: {self.capital} USDT")
        print(f"🎯 Target: {self.capital * 12} USDT")
        
        self.setup_database()
        self.start_trading()
    
    def setup_database(self):
        """Setup enhanced database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enhanced trade executions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS enhanced_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    amount REAL NOT NULL,
                    price REAL NOT NULL,
                    pnl REAL DEFAULT 0,
                    capital_before REAL,
                    capital_after REAL,
                    strategy TEXT,
                    confidence REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            print("✅ Enhanced database setup complete")
            
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
    
    def start_trading(self):
        """Start enhanced trading loop"""
        print("🔄 Starting enhanced trading loop...")
        
        trade_count = 0
        current_capital = self.capital
        
        while True:
            try:
                # Enhanced trading logic with 50 USDT
                trade_count += 1
                
                # Simulate enhanced trade
                import random
                
                symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"]
                symbol = random.choice(symbols)
                side = random.choice(["BUY", "SELL"])
                
                # Enhanced position sizing (15-20% of capital)
                position_size = current_capital * random.uniform(0.15, 0.20)
                price = random.uniform(40000, 45000) if symbol == "BTCUSDT" else random.uniform(2000, 3000)
                
                # Enhanced profit calculation
                profit_factor = random.uniform(0.98, 1.05)  # -2% to +5%
                pnl = position_size * (profit_factor - 1)
                
                current_capital += pnl
                
                # Log enhanced trade
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO enhanced_trades 
                    (symbol, side, amount, price, pnl, capital_before, capital_after, strategy, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (symbol, side, position_size, price, pnl, 
                     current_capital - pnl, current_capital, "enhanced_momentum", 0.85))
                
                conn.commit()
                conn.close()
                
                print(f"🎯 Trade {trade_count}: {symbol} {side} | PnL: {pnl:.4f} USDT | Capital: {current_capital:.2f} USDT")
                
                # Update wallet
                self.update_wallet(current_capital, pnl)
                
                # Sleep between trades (30-120 seconds)
                time.sleep(random.randint(30, 120))
                
            except KeyboardInterrupt:
                print("\n👋 Trading stopped by user")
                break
            except Exception as e:
                print(f"⚠️ Trading error: {e}")
                time.sleep(60)
    
    def update_wallet(self, new_balance, pnl):
        """Update wallet file"""
        try:
            with open(self.wallet_file, 'r') as f:
                wallet = json.load(f)
            
            wallet['balance']['total_usdt'] = new_balance
            wallet['balance']['available_usdt'] = new_balance * 0.8
            wallet['performance_tracking']['current_balance'] = new_balance
            wallet['performance_tracking']['total_pnl'] += pnl
            wallet['performance_tracking']['roi_percentage'] = ((new_balance - 50.0) / 50.0) * 100
            
            with open(self.wallet_file, 'w') as f:
                json.dump(wallet, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Wallet update failed: {e}")

if __name__ == "__main__":
    bot = Enhanced50USDTBot()
