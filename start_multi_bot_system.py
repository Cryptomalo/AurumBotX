#!/usr/bin/env python3
"""
AurumBotX Multi-Bot System Launcher
Avvia 8 bot simultanei con strategie diverse

Author: AurumBotX Team
Date: 12 Settembre 2025
Version: 1.0
"""

import json
import subprocess
import time
import os
import sys
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class MultiBotLauncher:
    def __init__(self, config_file="config/multi_bot_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.processes = {}
        
    def load_config(self):
        """Load multi-bot configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return None
    
    def create_bot_script(self, bot_config):
        """Create individual bot script"""
        bot_id = bot_config['bot_id']
        script_content = f'''#!/usr/bin/env python3
"""
AurumBotX Bot #{bot_id} - {bot_config['name']}
Strategy: {bot_config['strategy']}
"""

import sys
import os
import time
import json
import logging
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import AurumBotX components
from src.core.trading_engine_usdt_sqlalchemy import TradingEngineUSDT
from src.strategies.strategy_network import StrategyNetwork
from src.core.risk_manager_usdt import RiskManagerUSDT

class Bot{bot_id}:
    def __init__(self):
        self.bot_id = {bot_id}
        self.name = "{bot_config['name']}"
        self.strategy = "{bot_config['strategy']}"
        self.capital = {bot_config['capital']}
        self.port = {bot_config['port']}
        self.pairs = {bot_config['pairs']}
        self.risk_per_trade = {bot_config['risk_per_trade']}
        self.max_positions = {bot_config['max_positions']}
        self.timeframe = "{bot_config['timeframe']}"
        
        # Initialize components
        self.trading_engine = TradingEngineUSDT(
            db_path=f"data/bot_{bot_id}_trading.db"
        )
        self.strategy_network = StrategyNetwork()
        self.risk_manager = RiskManagerUSDT()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - Bot{bot_id} - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/bot_{bot_id}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(f'Bot{bot_id}')
        
    def start_trading(self):
        """Start bot trading loop"""
        self.logger.info(f"🚀 Starting {{self.name}} - Strategy: {{self.strategy}}")
        self.logger.info(f"💰 Capital: {{self.capital}} USDT")
        self.logger.info(f"📊 Pairs: {{self.pairs}}")
        self.logger.info(f"⚖️ Risk per trade: {{self.risk_per_trade*100}}%")
        
        try:
            while True:
                # Execute trading logic based on strategy
                self.execute_strategy()
                
                # Wait based on timeframe
                sleep_time = self.get_sleep_time()
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Bot stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Bot error: {{e}}")
    
    def execute_strategy(self):
        """Execute trading strategy"""
        try:
            if self.strategy == "momentum_trading":
                self.momentum_strategy()
            elif self.strategy == "scalping":
                self.scalping_strategy()
            elif self.strategy == "mean_reversion":
                self.mean_reversion_strategy()
            elif self.strategy == "breakout_trading":
                self.breakout_strategy()
            elif self.strategy == "grid_trading":
                self.grid_strategy()
            elif self.strategy == "meme_coin_hunting":
                self.meme_coin_strategy()
            elif self.strategy == "dca_strategy":
                self.dca_strategy()
            elif self.strategy == "ai_sentiment_trading":
                self.ai_sentiment_strategy()
            else:
                self.logger.warning(f"⚠️ Unknown strategy: {{self.strategy}}")
                
        except Exception as e:
            self.logger.error(f"❌ Strategy execution error: {{e}}")
    
    def momentum_strategy(self):
        """Momentum trading strategy"""
        self.logger.info("📈 Executing momentum strategy")
        # Implement momentum logic here
        
    def scalping_strategy(self):
        """Scalping strategy"""
        self.logger.info("⚡ Executing scalping strategy")
        # Implement scalping logic here
        
    def mean_reversion_strategy(self):
        """Mean reversion strategy"""
        self.logger.info("🔄 Executing mean reversion strategy")
        # Implement mean reversion logic here
        
    def breakout_strategy(self):
        """Breakout trading strategy"""
        self.logger.info("💥 Executing breakout strategy")
        # Implement breakout logic here
        
    def grid_strategy(self):
        """Grid trading strategy"""
        self.logger.info("🔲 Executing grid strategy")
        # Implement grid logic here
        
    def meme_coin_strategy(self):
        """Meme coin hunting strategy"""
        self.logger.info("🐕 Executing meme coin strategy")
        # Implement meme coin logic here
        
    def dca_strategy(self):
        """Dollar Cost Averaging strategy"""
        self.logger.info("📊 Executing DCA strategy")
        # Implement DCA logic here
        
    def ai_sentiment_strategy(self):
        """AI sentiment trading strategy"""
        self.logger.info("🤖 Executing AI sentiment strategy")
        # Implement AI sentiment logic here
    
    def get_sleep_time(self):
        """Get sleep time based on timeframe"""
        timeframe_map = {{
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "30m": 1800,
            "1h": 3600,
            "4h": 14400
        }}
        return timeframe_map.get(self.timeframe, 300)

if __name__ == "__main__":
    bot = Bot{bot_id}()
    bot.start_trading()
'''
        
        # Save bot script
        script_path = f"scripts/bot_{bot_id}.py"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(script_path, 0o755)
        return script_path
    
    def start_bot(self, bot_config):
        """Start individual bot"""
        bot_id = bot_config['bot_id']
        bot_name = bot_config['name']
        
        print(f"🚀 Starting Bot #{bot_id}: {bot_name}")
        
        # Create bot script
        script_path = self.create_bot_script(bot_config)
        
        # Start bot process
        log_file = f"logs/bot_{bot_id}.log"
        cmd = f"python {script_path}"
        
        try:
            process = subprocess.Popen(
                cmd.split(),
                stdout=open(log_file, 'a'),
                stderr=subprocess.STDOUT,
                cwd=project_root
            )
            
            self.processes[bot_id] = {
                'process': process,
                'config': bot_config,
                'started': datetime.now(),
                'log_file': log_file
            }
            
            print(f"✅ Bot #{bot_id} started (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start Bot #{bot_id}: {e}")
            return False
    
    def start_all_bots(self):
        """Start all bots"""
        print("🚀 AurumBotX Multi-Bot System Starting...")
        print("=" * 60)
        
        if not self.config:
            print("❌ No configuration loaded")
            return False
        
        bots = self.config.get('bots', [])
        total_bots = len(bots)
        
        print(f"📊 Total Bots: {total_bots}")
        print(f"💰 Total Capital: {self.config['multi_bot_system']['total_capital']} USDT")
        print(f"💵 Capital per Bot: {self.config['multi_bot_system']['capital_per_bot']} USDT")
        print("=" * 60)
        
        success_count = 0
        
        for bot_config in bots:
            if self.start_bot(bot_config):
                success_count += 1
            time.sleep(2)  # Delay between starts
        
        print("=" * 60)
        print(f"✅ Successfully started: {success_count}/{total_bots} bots")
        
        if success_count > 0:
            self.show_status()
            return True
        else:
            print("❌ No bots started successfully")
            return False
    
    def show_status(self):
        """Show current status of all bots"""
        print("\\n📊 MULTI-BOT STATUS:")
        print("-" * 80)
        print(f"{'ID':<3} {'Name':<20} {'Strategy':<20} {'PID':<8} {'Status':<10}")
        print("-" * 80)
        
        for bot_id, bot_info in self.processes.items():
            process = bot_info['process']
            config = bot_info['config']
            
            if process.poll() is None:
                status = "🟢 RUNNING"
            else:
                status = "🔴 STOPPED"
            
            print(f"{bot_id:<3} {config['name']:<20} {config['strategy']:<20} {process.pid:<8} {status:<10}")
        
        print("-" * 80)
        print(f"Total Active Bots: {len([p for p in self.processes.values() if p['process'].poll() is None])}")
    
    def stop_all_bots(self):
        """Stop all running bots"""
        print("🛑 Stopping all bots...")
        
        for bot_id, bot_info in self.processes.items():
            process = bot_info['process']
            if process.poll() is None:
                print(f"🛑 Stopping Bot #{bot_id}...")
                process.terminate()
                time.sleep(1)
                if process.poll() is None:
                    process.kill()
                print(f"✅ Bot #{bot_id} stopped")
        
        print("✅ All bots stopped")

def main():
    """Main function"""
    print("🤖 AurumBotX Multi-Bot System Launcher")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    launcher = MultiBotLauncher()
    
    try:
        if launcher.start_all_bots():
            print("\\n🎯 Multi-Bot System is now running!")
            print("📊 Monitor logs: tail -f logs/bot_*.log")
            print("🛑 Stop all: Ctrl+C")
            
            # Keep running until interrupted
            while True:
                time.sleep(60)
                launcher.show_status()
                
    except KeyboardInterrupt:
        print("\\n🛑 Shutdown requested...")
        launcher.stop_all_bots()
        print("✅ Multi-Bot System stopped")
    except Exception as e:
        print(f"❌ System error: {e}")
        launcher.stop_all_bots()

if __name__ == "__main__":
    main()

