"""
AurumBotX - Wallet Runner Optimized 5 Trades/Day
Strategy with Dynamic Holding and High-Quality Trades
"""

import json
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
import sys

class WalletRunner5Trades:
    def __init__(self, config_path):
        """Initialize optimized wallet runner"""
        self.config_path = config_path
        self.load_config()
        self.setup_state()
        self.daily_trades_count = 0
        self.last_reset_day = datetime.now().date()
        
    def load_config(self):
        """Load configuration from JSON"""
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        
        print(f"✅ Configuration loaded: {self.config['wallet_name']}")
        print(f"   Cycle interval: {self.config['cycle_config']['interval_hours']}h")
        print(f"   Confidence threshold: {self.config['strategy']['confidence_threshold']*100}%")
        print(f"   Take profit: {self.config['risk_management']['take_profit_percent']*100}%")
        
    def setup_state(self):
        """Setup state directory and file"""
        wallet_name = self.config['wallet_name'].lower().replace(' ', '_').replace('/', '_')
        self.state_dir = Path(f"/home/ubuntu/AurumBotX/demo_trading/{wallet_name}")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.state_dir / "state.json"
        self.log_file = self.state_dir / "trading.log"
        
        if self.state_file.exists():
            self.load_state()
        else:
            self.init_state()
            
    def init_state(self):
        """Initialize new state"""
        self.state = {
            "start_time": datetime.now().isoformat(),
            "initial_capital": self.config['initial_capital'],
            "current_capital": self.config['initial_capital'],
            "current_level": "TURTLE",
            "statistics": {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "total_pnl": 0.0,
                "roi_percentage": 0.0,
                "current_streak": 0,
                "max_win_streak": 0,
                "max_loss_streak": 0,
                "daily_pnl": 0.0,
                "daily_trades": 0
            },
            "trades_history": [],
            "open_positions": []
        }
        self.save_state()
        
    def load_state(self):
        """Load existing state"""
        with open(self.state_file, 'r') as f:
            self.state = json.load(f)
        print(f"📊 State loaded: {self.state['statistics']['total_trades']} trades")
        
    def save_state(self):
        """Save state to file"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
            
    def log(self, message):
        """Log message"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        with open(self.log_file, 'a') as f:
            f.write(log_msg + '\n')
            
    def reset_daily_counter(self):
        """Reset daily trade counter if new day"""
        today = datetime.now().date()
        if today != self.last_reset_day:
            self.daily_trades_count = 0
            self.last_reset_day = today
            self.state['statistics']['daily_pnl'] = 0.0
            self.state['statistics']['daily_trades'] = 0
            self.log("🌅 New day - daily counters reset")
            
    def analyze_market(self, pair):
        """Analyze market for trading opportunity"""
        # Simulated analysis (in real version: use real market data)
        confidence = random.uniform(0.50, 0.95)
        trend_strength = random.uniform(0.8, 1.5)
        volatility = random.uniform(0.01, 0.03)
        direction = random.choice(['buy', 'sell'])
        
        expected_profit = (trend_strength - 1.0) * 0.15  # Simplified
        
        return {
            'pair': pair,
            'confidence': confidence,
            'trend_strength': trend_strength,
            'volatility': volatility,
            'direction': direction,
            'expected_profit': expected_profit
        }
        
    def should_trade(self, analysis):
        """Decide if should execute trade"""
        level_config = self.config['levels'][self.state['current_level']]
        
        # Check confidence threshold
        if analysis['confidence'] < level_config['confidence_threshold']:
            return False, f"Confidence too low: {analysis['confidence']:.1%} < {level_config['confidence_threshold']:.1%}"
            
        # Check expected profit
        min_expected = self.config['strategy']['min_expected_profit']
        if analysis['expected_profit'] < min_expected:
            return False, f"Expected profit too low: {analysis['expected_profit']:.1%} < {min_expected:.1%}"
            
        # Check daily trade limit
        if self.daily_trades_count >= self.config['cycle_config']['max_daily_trades']:
            return False, f"Daily trade limit reached: {self.daily_trades_count}/{self.config['cycle_config']['max_daily_trades']}"
            
        # Check safety limits
        if self.state['statistics']['daily_pnl'] / self.state['initial_capital'] <= -self.config['safety_limits']['daily_loss_limit_percent']:
            return False, "Daily loss limit reached"
            
        return True, "All conditions met"
        
    def execute_trade(self, analysis):
        """Execute trade entry"""
        level_config = self.config['levels'][self.state['current_level']]
        
        position_size_usd = self.state['current_capital'] * level_config['position_size_percent']
        entry_price = 50000  # Simulated (in real: get from exchange)
        
        position = {
            'entry_time': datetime.now().isoformat(),
            'pair': analysis['pair'],
            'direction': analysis['direction'],
            'entry_price': entry_price,
            'position_size_usd': position_size_usd,
            'amount': position_size_usd / entry_price,
            'stop_loss_percent': level_config['stop_loss_percent'],
            'take_profit_percent': level_config['take_profit_percent'],
            'confidence': analysis['confidence'],
            'level': self.state['current_level'],
            'status': 'open'
        }
        
        self.state['open_positions'].append(position)
        self.daily_trades_count += 1
        
        self.log(f"📈 ENTRY: {position['pair']} {position['direction'].upper()} ${position['position_size_usd']:.2f} @ ${entry_price:,.0f} (confidence: {analysis['confidence']:.1%})")
        
        return position
        
    def monitor_position(self, position):
        """Monitor open position and check exit conditions"""
        # Simulated price movement
        current_price = position['entry_price'] * random.uniform(0.96, 1.12)
        
        # Calculate P&L
        if position['direction'] == 'buy':
            pnl_percent = (current_price - position['entry_price']) / position['entry_price']
        else:  # sell
            pnl_percent = (position['entry_price'] - current_price) / position['entry_price']
            
        pnl_usd = position['position_size_usd'] * pnl_percent
        
        # Check exit conditions
        should_exit = False
        exit_reason = None
        
        # Take profit
        if pnl_percent >= position['take_profit_percent']:
            should_exit = True
            exit_reason = "take_profit"
            
        # Stop loss
        elif pnl_percent <= -position['stop_loss_percent']:
            should_exit = True
            exit_reason = "stop_loss"
            
        # Timeout (24h max)
        entry_time = datetime.fromisoformat(position['entry_time'])
        holding_hours = (datetime.now() - entry_time).total_seconds() / 3600
        if holding_hours >= self.config['cycle_config']['max_holding_hours']:
            should_exit = True
            exit_reason = "timeout"
            
        if should_exit:
            self.close_position(position, current_price, pnl_usd, pnl_percent, exit_reason)
            return True
            
        return False
        
    def close_position(self, position, exit_price, pnl_usd, pnl_percent, reason):
        """Close position and record trade"""
        # Calculate fee
        fee = position['position_size_usd'] * 0.001  # 0.1% round-trip
        net_pnl = pnl_usd - fee
        
        # Update capital
        self.state['current_capital'] += net_pnl
        
        # Record trade
        trade = {
            'timestamp': datetime.now().isoformat(),
            'pair': position['pair'],
            'direction': position['direction'],
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'amount': position['amount'],
            'position_size_usd': position['position_size_usd'],
            'pnl': net_pnl,
            'pnl_percentage': pnl_percent * 100,
            'fee': fee,
            'confidence': position['confidence'],
            'level': position['level'],
            'exit_reason': reason,
            'is_win': net_pnl > 0
        }
        
        self.state['trades_history'].append(trade)
        
        # Update statistics
        stats = self.state['statistics']
        stats['total_trades'] += 1
        stats['daily_trades'] += 1
        stats['total_pnl'] += net_pnl
        stats['daily_pnl'] += net_pnl
        stats['roi_percentage'] = (self.state['current_capital'] / self.state['initial_capital'] - 1) * 100
        
        if trade['is_win']:
            stats['winning_trades'] += 1
            stats['current_streak'] = max(1, stats['current_streak'] + 1) if stats['current_streak'] >= 0 else 1
            stats['max_win_streak'] = max(stats['max_win_streak'], stats['current_streak'])
        else:
            stats['losing_trades'] += 1
            stats['current_streak'] = min(-1, stats['current_streak'] - 1) if stats['current_streak'] <= 0 else -1
            stats['max_loss_streak'] = max(stats['max_loss_streak'], abs(stats['current_streak']))
            
        stats['win_rate'] = (stats['winning_trades'] / stats['total_trades'] * 100) if stats['total_trades'] > 0 else 0
        
        # Calculate profit factor
        total_wins = sum(t['pnl'] for t in self.state['trades_history'] if t['is_win'])
        total_losses = abs(sum(t['pnl'] for t in self.state['trades_history'] if not t['is_win']))
        stats['profit_factor'] = (total_wins / total_losses) if total_losses > 0 else 0
        
        # Remove from open positions
        self.state['open_positions'] = [p for p in self.state['open_positions'] if p != position]
        
        # Log
        emoji = "✅" if trade['is_win'] else "❌"
        self.log(f"{emoji} EXIT ({reason}): {trade['pair']} {net_pnl:+.4f} ({pnl_percent*100:+.2f}%) - Capital: ${self.state['current_capital']:.2f}")
        
        self.save_state()
        
    def run_cycle(self):
        """Run one trading cycle"""
        self.reset_daily_counter()
        
        cycle_num = self.state['statistics']['total_trades'] + 1
        self.log(f"\n{'='*70}")
        self.log(f"🔄 CYCLE #{cycle_num} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"{'='*70}")
        
        # Monitor open positions first
        for position in list(self.state['open_positions']):
            self.monitor_position(position)
            
        # Analysis phase
        self.log("🔍 Market analysis phase...")
        time.sleep(2)  # Simulate analysis
        
        # Select pair
        pairs = self.config['trading_pairs']
        pair = random.choice(pairs)
        
        # Analyze
        analysis = self.analyze_market(pair)
        
        # Decision
        should_trade, reason = self.should_trade(analysis)
        
        if should_trade:
            self.log(f"✅ GO: {reason}")
            position = self.execute_trade(analysis)
            
            # Hold until exit conditions met
            self.log("⏳ Holding position...")
            while position in self.state['open_positions']:
                time.sleep(60)  # Check every 1 min
                self.monitor_position(position)
        else:
            self.log(f"⏭️  NO-GO: {reason}")
            
        self.save_state()
        
    def run(self):
        """Main run loop"""
        self.log(f"\n🚀 Starting {self.config['wallet_name']}")
        self.log(f"   Initial capital: ${self.config['initial_capital']:.2f}")
        self.log(f"   Cycle interval: {self.config['cycle_config']['interval_hours']}h")
        self.log(f"   Max daily trades: {self.config['cycle_config']['max_daily_trades']}")
        
        try:
            while True:
                self.run_cycle()
                
                # Wait for next cycle
                interval_seconds = self.config['cycle_config']['interval_hours'] * 3600
                next_cycle = datetime.now() + timedelta(seconds=interval_seconds)
                self.log(f"⏰ Next cycle at {next_cycle.strftime('%H:%M:%S')}")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            self.log("\n🛑 Stopping wallet...")
            self.save_state()
            self.log("✅ State saved. Goodbye!")
            
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 wallet_runner_5trades.py <config_file>")
        sys.exit(1)
        
    config_path = sys.argv[1]
    runner = WalletRunner5Trades(config_path)
    runner.run()
