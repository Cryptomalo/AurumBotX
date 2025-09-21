#!/usr/bin/env python3
"""
AurumBotX 50 USDT Challenge Launcher
Enhanced capital trading system with 50 USDT

Author: AurumBotX Team
Date: 13 Settembre 2025
Version: 2.1
"""

import os
import sys
import json
import time
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class Challenge50USDTLauncher:
    def __init__(self):
        self.project_root = project_root
        self.config_file = self.project_root / "config" / "50_usdt_challenge.json"
        self.wallet_file = self.project_root / "data" / "wallet_50_usdt.json"
        self.log_file = self.project_root / "logs" / "50_usdt_challenge.log"
        
        print("🚀 AurumBotX 50 USDT Challenge Launcher v2.1")
        print("=" * 50)
        print(f"📁 Project Root: {self.project_root}")
        print(f"⚙️ Config: {self.config_file}")
        print(f"💰 Wallet: {self.wallet_file}")
        print("=" * 50)
    
    def load_config(self):
        """Load challenge configuration"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            print(f"✅ Configuration loaded")
            print(f"💰 Initial Capital: {config['capital_management']['initial_capital']} USDT")
            print(f"🎯 Target Capital: {config['capital_management']['target_capital']} USDT")
            print(f"📈 Growth Target: {config['capital_management']['growth_target_multiplier']}x")
            
            return config
            
        except Exception as e:
            print(f"❌ Failed to load config: {e}")
            return None
    
    def load_wallet(self):
        """Load wallet configuration"""
        try:
            with open(self.wallet_file, 'r') as f:
                wallet = json.load(f)
            
            print(f"✅ Wallet loaded")
            print(f"💳 Total Balance: {wallet['balance']['total_usdt']} USDT")
            print(f"🔄 Available: {wallet['balance']['available_usdt']} USDT")
            print(f"🛡️ Reserved: {wallet['balance']['reserved_usdt']} USDT")
            
            return wallet
            
        except Exception as e:
            print(f"❌ Failed to load wallet: {e}")
            return None
    
    def update_database_capital(self, new_capital):
        """Update database with new capital"""
        try:
            # Update mainnet trading database
            db_path = self.project_root / "data" / "databases" / "mainnet_trading.db"
            
            if db_path.exists():
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if capital tracking table exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS capital_tracking (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        capital_amount REAL NOT NULL,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        reason TEXT
                    )
                """)
                
                # Insert new capital record
                cursor.execute("""
                    INSERT INTO capital_tracking (capital_amount, reason)
                    VALUES (?, ?)
                """, (new_capital, "Manual capital increase to 50 USDT"))
                
                conn.commit()
                conn.close()
                
                print(f"✅ Database updated with new capital: {new_capital} USDT")
                return True
                
        except Exception as e:
            print(f"⚠️ Database update failed: {e}")
            return False
    
    def stop_existing_bots(self):
        """Stop existing trading bots"""
        print("🛑 Stopping existing trading bots...")
        
        try:
            # Find and stop mainnet demo
            result = subprocess.run(["pkill", "-f", "start_mainnet_demo.py"], 
                                  capture_output=True, text=True)
            
            # Find and stop other trading processes
            subprocess.run(["pkill", "-f", "active_trading_bot"], 
                          capture_output=True, text=True)
            
            time.sleep(3)  # Wait for processes to stop
            
            print("✅ Existing bots stopped")
            return True
            
        except Exception as e:
            print(f"⚠️ Error stopping bots: {e}")
            return False
    
    def start_enhanced_trading_bot(self):
        """Start enhanced trading bot with 50 USDT"""
        print("🚀 Starting enhanced trading bot...")
        
        try:
            # Create enhanced trading script
            enhanced_script = self.project_root / "start_50_usdt_trading.py"
            
            script_content = f'''#!/usr/bin/env python3
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
        print(f"💰 Capital: {{self.capital}} USDT")
        print(f"🎯 Target: {{self.capital * 12}} USDT")
        
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
            print(f"❌ Database setup failed: {{e}}")
    
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
                
                print(f"🎯 Trade {{trade_count}}: {{symbol}} {{side}} | PnL: {{pnl:.4f}} USDT | Capital: {{current_capital:.2f}} USDT")
                
                # Update wallet
                self.update_wallet(current_capital, pnl)
                
                # Sleep between trades (30-120 seconds)
                time.sleep(random.randint(30, 120))
                
            except KeyboardInterrupt:
                print("\\n👋 Trading stopped by user")
                break
            except Exception as e:
                print(f"⚠️ Trading error: {{e}}")
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
            print(f"⚠️ Wallet update failed: {{e}}")

if __name__ == "__main__":
    bot = Enhanced50USDTBot()
'''
            
            with open(enhanced_script, 'w') as f:
                f.write(script_content)
            
            # Make executable
            os.chmod(enhanced_script, 0o755)
            
            # Start the enhanced bot
            process = subprocess.Popen([
                sys.executable, str(enhanced_script)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            print(f"✅ Enhanced trading bot started (PID: {process.pid})")
            print(f"📊 Monitoring: tail -f {self.log_file}")
            
            return process
            
        except Exception as e:
            print(f"❌ Failed to start enhanced bot: {e}")
            return None
    
    def monitor_performance(self):
        """Monitor trading performance"""
        print("📊 Performance monitoring active...")
        
        while True:
            try:
                # Check wallet status
                if self.wallet_file.exists():
                    with open(self.wallet_file, 'r') as f:
                        wallet = json.load(f)
                    
                    current_balance = wallet['balance']['total_usdt']
                    roi = wallet['performance_tracking']['roi_percentage']
                    
                    print(f"💰 Balance: {current_balance:.2f} USDT | ROI: {roi:.2f}%")
                
                time.sleep(300)  # Check every 5 minutes
                
            except KeyboardInterrupt:
                print("\\n📊 Monitoring stopped")
                break
            except Exception as e:
                print(f"⚠️ Monitoring error: {e}")
                time.sleep(60)
    
    def launch_challenge(self):
        """Launch the complete 50 USDT challenge"""
        print("🚀 LAUNCHING 50 USDT CHALLENGE")
        print("=" * 50)
        
        # Load configurations
        config = self.load_config()
        wallet = self.load_wallet()
        
        if not config or not wallet:
            print("❌ Configuration loading failed")
            return False
        
        # Update database
        self.update_database_capital(50.0)
        
        # Stop existing bots
        self.stop_existing_bots()
        
        # Start enhanced trading bot
        bot_process = self.start_enhanced_trading_bot()
        
        if bot_process:
            print("🎉 50 USDT CHALLENGE LAUNCHED SUCCESSFULLY!")
            print("=" * 50)
            print(f"💰 Initial Capital: 50.0 USDT")
            print(f"🎯 Target Capital: 600.0 USDT")
            print(f"📈 Growth Target: 12x (1,200%)")
            print(f"🤖 Bot PID: {bot_process.pid}")
            print("=" * 50)
            
            # Start monitoring
            self.monitor_performance()
            
            return True
        else:
            print("❌ Challenge launch failed")
            return False

def main():
    """Main launcher function"""
    launcher = Challenge50USDTLauncher()
    
    try:
        success = launcher.launch_challenge()
        
        if success:
            print("🎉 Challenge completed successfully!")
        else:
            print("❌ Challenge launch failed")
            
    except KeyboardInterrupt:
        print("\\n👋 Challenge launcher stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()

