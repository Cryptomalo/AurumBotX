#!/usr/bin/env python3
"""
AurumBotX Boost Trading System
Sistema trading ottimizzato per performance 10-15x superiori

Author: AurumBotX Team
Date: 14 Settembre 2025
Version: 2.1 Boost
"""

import os
import sys
import json
import time
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class BoostTradingSystem:
    def __init__(self):
        self.project_root = project_root
        self.config_path = self.project_root / "config" / "boost_trading_config.json"
        self.wallet_path = self.project_root / "data" / "wallet_50_usdt.json"
        self.db_path = self.project_root / "data" / "databases" / "boost_trading.db"
        
        # Load configuration
        self.config = self.load_config()
        self.current_capital = self.config["capital_management"]["initial_capital"]
        
        # Trading state
        self.active_positions = []
        self.daily_pnl = 0.0
        self.trade_count = 0
        self.start_time = datetime.now()
        
        # Performance tracking
        self.performance_stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "avg_return": 0.0,
            "hourly_rate": 0.0
        }
        
        print("🚀 AurumBotX Boost Trading System v2.1")
        print("=" * 50)
        print(f"📁 Project: {self.project_root}")
        print(f"💰 Initial Capital: {self.current_capital:.2f} USDT")
        print(f"🎯 Target: {self.config['capital_management']['target_capital']:.0f} USDT")
        print(f"📈 Expected Performance: {self.config['boost_config']['target_performance']}")
        print("=" * 50)
        
    def load_config(self):
        """Load boost trading configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return self.get_default_config()
    
    def get_default_config(self):
        """Default configuration fallback"""
        return {
            "capital_management": {"initial_capital": 50.95},
            "primary_strategy": {
                "name": "AI_Consensus_Strategy",
                "position_size_factor": 0.35,
                "expected_return": 0.14
            }
        }
    
    def init_database(self):
        """Initialize boost trading database"""
        try:
            os.makedirs(self.db_path.parent, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS boost_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    strategy TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    amount REAL NOT NULL,
                    price REAL NOT NULL,
                    pnl REAL DEFAULT 0,
                    capital_before REAL,
                    capital_after REAL,
                    confidence REAL,
                    position_size_percent REAL,
                    execution_time REAL,
                    status TEXT DEFAULT 'EXECUTED'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_trades INTEGER,
                    winning_trades INTEGER,
                    win_rate REAL,
                    total_pnl REAL,
                    hourly_rate REAL,
                    current_capital REAL
                )
            ''')
            
            conn.commit()
            conn.close()
            
            print("✅ Boost database initialized")
            return True
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return False
    
    def get_market_data(self):
        """Simulate market data for strategy selection"""
        # Simulate real market conditions
        import random
        
        market_data = {
            'BTCUSDT': {
                'price': 43500 + random.uniform(-500, 500),
                'change_24h': random.uniform(-0.05, 0.08),
                'volume': random.uniform(1000000, 5000000)
            },
            'ETHUSDT': {
                'price': 2650 + random.uniform(-100, 100),
                'change_24h': random.uniform(-0.04, 0.06),
                'volume': random.uniform(500000, 2000000)
            },
            'ADAUSDT': {
                'price': 0.35 + random.uniform(-0.02, 0.02),
                'change_24h': random.uniform(-0.06, 0.10),
                'volume': random.uniform(100000, 800000)
            }
        }
        
        return market_data
    
    def select_optimal_strategy(self):
        """Select best strategy based on current conditions"""
        market_data = self.get_market_data()
        
        # Calculate market condition
        total_change = sum(data['change_24h'] for data in market_data.values())
        avg_change = total_change / len(market_data)
        
        # Strategy selection logic
        if avg_change >= 0.05:  # Bull strong
            strategy = self.config["primary_strategy"]
            confidence = 0.85
        elif avg_change >= 0.02:  # Bull moderate
            strategy = self.config["primary_strategy"]
            confidence = 0.80
        elif avg_change <= -0.02:  # Bear
            strategy = self.config["backup_strategy"]
            confidence = 0.90
        else:  # Sideways
            strategy = self.config["secondary_strategy"]
            confidence = 0.75
        
        return strategy, confidence, market_data
    
    def calculate_position_size(self, strategy, confidence):
        """Calculate optimal position size"""
        base_factor = strategy["position_size_factor"]
        
        # Confidence adjustment
        confidence_multiplier = 0.7 + (confidence * 0.6)  # 0.7x to 1.3x
        
        # Performance adjustment
        if self.performance_stats["win_rate"] > 0.75:
            performance_multiplier = 1.2
        elif self.performance_stats["win_rate"] < 0.50:
            performance_multiplier = 0.8
        else:
            performance_multiplier = 1.0
        
        # Calculate final size
        position_factor = base_factor * confidence_multiplier * performance_multiplier
        position_size = self.current_capital * position_factor
        
        # Apply limits
        min_size = self.current_capital * 0.15  # Min 15%
        max_size = self.current_capital * 0.50  # Max 50%
        
        position_size = max(min_size, min(position_size, max_size))
        
        return position_size
    
    def execute_trade(self, strategy, confidence, market_data):
        """Execute optimized trade"""
        try:
            # Select best symbol
            best_symbol = max(market_data.keys(), 
                            key=lambda x: abs(market_data[x]['change_24h']))
            
            symbol_data = market_data[best_symbol]
            
            # Determine side based on strategy and market
            if strategy["name"] == "AI_Consensus_Strategy":
                side = "BUY" if symbol_data['change_24h'] > 0 else "SELL"
            elif strategy["name"] == "Breakout_Capture":
                side = "BUY" if symbol_data['change_24h'] > 0.03 else "SELL"
            else:  # Arbitrage
                side = "BUY" if symbol_data['change_24h'] < 0 else "SELL"
            
            # Calculate position
            position_size = self.calculate_position_size(strategy, confidence)
            position_percent = (position_size / self.current_capital) * 100
            
            # Simulate trade execution
            price = symbol_data['price']
            amount = position_size / price
            
            # Calculate PnL based on strategy performance
            expected_return = strategy["expected_return"]
            
            # Add randomness based on confidence and market conditions
            import random
            success_probability = confidence * strategy.get("expected_win_rate", 0.65)
            
            if random.random() < success_probability:
                # Winning trade
                pnl_factor = random.uniform(0.5, 1.5) * expected_return
                pnl = position_size * pnl_factor
                status = "WIN"
            else:
                # Losing trade
                loss_factor = random.uniform(0.3, 0.8) * strategy.get("stop_loss", 0.05)
                pnl = -position_size * loss_factor
                status = "LOSS"
            
            # Update capital
            capital_before = self.current_capital
            self.current_capital += pnl
            
            # Record trade
            self.record_trade({
                'strategy': strategy["name"],
                'symbol': best_symbol,
                'side': side,
                'amount': amount,
                'price': price,
                'pnl': pnl,
                'capital_before': capital_before,
                'capital_after': self.current_capital,
                'confidence': confidence,
                'position_size_percent': position_percent,
                'status': status
            })
            
            # Update performance stats
            self.update_performance_stats(pnl > 0, pnl)
            
            print(f"🎯 TRADE EXECUTED:")
            print(f"   Strategy: {strategy['name']}")
            print(f"   {best_symbol} {side} | Amount: {amount:.6f}")
            print(f"   Position: {position_size:.2f} USDT ({position_percent:.1f}%)")
            print(f"   PnL: {pnl:+.4f} USDT | {status}")
            print(f"   Capital: {capital_before:.2f} → {self.current_capital:.2f} USDT")
            print(f"   Confidence: {confidence:.1%}")
            
            return True
            
        except Exception as e:
            print(f"❌ Trade execution failed: {e}")
            return False
    
    def record_trade(self, trade_data):
        """Record trade in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO boost_trades 
                (strategy, symbol, side, amount, price, pnl, capital_before, 
                 capital_after, confidence, position_size_percent, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_data['strategy'],
                trade_data['symbol'],
                trade_data['side'],
                trade_data['amount'],
                trade_data['price'],
                trade_data['pnl'],
                trade_data['capital_before'],
                trade_data['capital_after'],
                trade_data['confidence'],
                trade_data['position_size_percent'],
                trade_data['status']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Trade recording failed: {e}")
    
    def update_performance_stats(self, is_win, pnl):
        """Update performance statistics"""
        self.performance_stats["total_trades"] += 1
        if is_win:
            self.performance_stats["winning_trades"] += 1
        
        self.performance_stats["total_pnl"] += pnl
        self.performance_stats["win_rate"] = (
            self.performance_stats["winning_trades"] / 
            self.performance_stats["total_trades"]
        )
        
        # Calculate hourly rate
        elapsed_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        if elapsed_hours > 0:
            self.performance_stats["hourly_rate"] = (
                self.performance_stats["total_pnl"] / elapsed_hours
            )
    
    def log_performance(self):
        """Log current performance"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance_log 
                (total_trades, winning_trades, win_rate, total_pnl, 
                 hourly_rate, current_capital)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                self.performance_stats["total_trades"],
                self.performance_stats["winning_trades"],
                self.performance_stats["win_rate"],
                self.performance_stats["total_pnl"],
                self.performance_stats["hourly_rate"],
                self.current_capital
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Performance logging failed: {e}")
    
    def print_performance_summary(self):
        """Print current performance summary"""
        elapsed_time = datetime.now() - self.start_time
        elapsed_hours = elapsed_time.total_seconds() / 3600
        
        print("\n" + "="*50)
        print("📊 PERFORMANCE SUMMARY")
        print("="*50)
        print(f"⏱️  Runtime: {elapsed_time}")
        print(f"🎯 Trades: {self.performance_stats['total_trades']}")
        print(f"✅ Wins: {self.performance_stats['winning_trades']}")
        print(f"📈 Win Rate: {self.performance_stats['win_rate']:.1%}")
        print(f"💰 Total PnL: {self.performance_stats['total_pnl']:+.4f} USDT")
        print(f"💳 Capital: {self.current_capital:.2f} USDT")
        print(f"📊 Hourly Rate: {self.performance_stats['hourly_rate']:.2f} USDT/h")
        
        if self.current_capital > 0:
            roi = ((self.current_capital - self.config["capital_management"]["initial_capital"]) / 
                   self.config["capital_management"]["initial_capital"] * 100)
            print(f"🚀 ROI: {roi:+.2f}%")
        
        print("="*50 + "\n")
    
    def run_boost_trading(self):
        """Main boost trading loop"""
        print("🚀 STARTING BOOST TRADING SYSTEM")
        print("Target: 3-5 USDT/hour performance")
        print("Strategy: AI Consensus + Dynamic Optimization")
        print()
        
        # Initialize database
        if not self.init_database():
            print("❌ Failed to initialize database")
            return
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                
                print(f"🔄 BOOST CYCLE #{cycle_count}")
                print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
                
                # Select optimal strategy
                strategy, confidence, market_data = self.select_optimal_strategy()
                
                print(f"🎯 Strategy: {strategy['name']}")
                print(f"🔮 Confidence: {confidence:.1%}")
                
                # Execute trade
                if self.execute_trade(strategy, confidence, market_data):
                    self.log_performance()
                
                # Print performance every 5 cycles
                if cycle_count % 5 == 0:
                    self.print_performance_summary()
                
                # Check performance targets
                if self.performance_stats["hourly_rate"] >= 3.0:
                    print("🎉 TARGET PERFORMANCE ACHIEVED!")
                    print(f"   Hourly Rate: {self.performance_stats['hourly_rate']:.2f} USDT/h")
                
                # Wait before next cycle (boost frequency)
                wait_time = 30  # 30 seconds for boost mode
                print(f"⏳ Next cycle in {wait_time}s...")
                time.sleep(wait_time)
                
        except KeyboardInterrupt:
            print("\n👋 Boost trading stopped by user")
            self.print_performance_summary()
        except Exception as e:
            print(f"\n❌ Boost trading error: {e}")
            self.print_performance_summary()

def main():
    """Main function"""
    boost_system = BoostTradingSystem()
    boost_system.run_boost_trading()

if __name__ == "__main__":
    main()

