"""
AurumBotX - Live Paper Trading Wallet Runner
Paper trading con dati di mercato LIVE da MEXC + AI + Filtri Bear Market
"""

import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
import sys
from openai import OpenAI

class LivePaperTradingWallet:
    def __init__(self, config_path):
        """Initialize live paper trading wallet"""
        self.config_path = config_path
        self.load_config()
        self.setup_state()
        self.setup_ai()
        self.daily_trades_count = 0
        self.last_reset_day = datetime.now().date()
        self.mexc_base_url = "https://api.mexc.com/api/v3"
        
    def load_config(self):
        """Load configuration from JSON"""
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        
        print(f"✅ Configuration loaded: {self.config['wallet_name']}")
        print(f"   Capital: €{self.config['initial_capital']:,.2f}")
        print(f"   Mode: LIVE PAPER TRADING (real market data)")
        
    def setup_ai(self):
        """Setup OpenAI client for AI analysis"""
        try:
            self.ai_client = OpenAI()
            print("✅ AI client initialized")
        except Exception as e:
            print(f"⚠️  AI client error: {e}")
            self.ai_client = None
            
    def setup_state(self):
        """Setup state directory and file"""
        wallet_name = self.config['wallet_name'].lower().replace(' ', '_').replace('€', 'eur')
        self.state_dir = Path(f"/home/ubuntu/AurumBotX/live_paper_trading/{wallet_name}")
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
                "daily_trades": 0,
                "bear_market_trades_skipped": 0,
                "low_confidence_skipped": 0
            },
            "trades_history": [],
            "open_positions": [],
            "market_context": {
                "last_trend_check": None,
                "current_trend": "unknown",
                "ma_50": None,
                "ma_200": None
            }
        }
        self.save_state()
        
    def load_state(self):
        """Load existing state"""
        with open(self.state_file, 'r') as f:
            self.state = json.load(f)
        print(f"📊 State loaded: {self.state['statistics']['total_trades']} trades, €{self.state['current_capital']:.2f}")
        
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
            
    def get_live_price(self, pair):
        """Get live price from MEXC"""
        try:
            symbol = pair.replace('/', '')
            url = f"{self.mexc_base_url}/ticker/24hr"
            response = requests.get(url, params={"symbol": symbol}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'symbol': pair,
                    'price': float(data['lastPrice']),
                    'change_24h': float(data['priceChangePercent']),
                    'volume_24h': float(data['volume']),
                    'high_24h': float(data['highPrice']),
                    'low_24h': float(data['lowPrice']),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                self.log(f"⚠️  MEXC API error: {response.status_code}")
                return None
        except Exception as e:
            self.log(f"⚠️  Error fetching price for {pair}: {e}")
            return None
            
    def detect_market_trend(self, pair):
        """Detect market trend using price action and AI"""
        market_data = self.get_live_price(pair)
        if not market_data:
            return "unknown", 50.0
            
        # Simple trend detection based on 24h change
        change_24h = market_data['change_24h']
        
        if change_24h > 2.0:
            trend = "strong_bullish"
            confidence = min(95.0, 70.0 + abs(change_24h) * 5)
        elif change_24h > 0.5:
            trend = "bullish"
            confidence = 65.0 + abs(change_24h) * 10
        elif change_24h < -2.0:
            trend = "strong_bearish"
            confidence = min(95.0, 70.0 + abs(change_24h) * 5)
        elif change_24h < -0.5:
            trend = "bearish"
            confidence = 65.0 + abs(change_24h) * 10
        else:
            trend = "sideways"
            confidence = 55.0
            
        return trend, confidence
        
    def ai_analyze_with_context(self, pair, market_data, trend):
        """Use AI to analyze trade opportunity with market context"""
        if not self.ai_client:
            # Fallback to simple analysis
            return self.simple_analysis(pair, market_data, trend)
            
        try:
            prompt = f"""Analyze this crypto trading opportunity:

Pair: {pair}
Current Price: ${market_data['price']:,.2f}
24h Change: {market_data['change_24h']:+.2f}%
24h High: ${market_data['high_24h']:,.2f}
24h Low: ${market_data['low_24h']:,.2f}
Detected Trend: {trend}

Should we trade? If yes, BUY or SELL?
Provide: 
1. Action (BUY/SELL/HOLD)
2. Confidence (0-100)
3. Brief reason (one sentence)

Format: ACTION|CONFIDENCE|REASON"""

            response = self.ai_client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": "You are an expert crypto trader. Be conservative and prioritize capital preservation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            answer = response.choices[0].message.content.strip()
            parts = answer.split('|')
            
            if len(parts) >= 3:
                action = parts[0].strip().upper()
                confidence = float(parts[1].strip())
                reason = parts[2].strip()
                
                return {
                    'action': action if action in ['BUY', 'SELL', 'HOLD'] else 'HOLD',
                    'confidence': confidence / 100.0,
                    'reason': reason,
                    'ai_used': True
                }
            else:
                return self.simple_analysis(pair, market_data, trend)
                
        except Exception as e:
            self.log(f"⚠️  AI analysis error: {e}")
            return self.simple_analysis(pair, market_data, trend)
            
    def simple_analysis(self, pair, market_data, trend):
        """Simple fallback analysis without AI"""
        change = market_data['change_24h']
        
        if trend in ['strong_bullish', 'bullish'] and change > 1.0:
            return {
                'action': 'BUY',
                'confidence': min(0.85, 0.65 + abs(change) * 0.05),
                'reason': f"Bullish trend with {change:+.2f}% momentum",
                'ai_used': False
            }
        elif trend in ['strong_bearish', 'bearish'] and change < -1.0:
            return {
                'action': 'SELL',
                'confidence': min(0.85, 0.65 + abs(change) * 0.05),
                'reason': f"Bearish trend with {change:+.2f}% momentum",
                'ai_used': False
            }
        else:
            return {
                'action': 'HOLD',
                'confidence': 0.50,
                'reason': "No clear trend or insufficient momentum",
                'ai_used': False
            }
            
    def reset_daily_counter(self):
        """Reset daily trade counter if new day"""
        today = datetime.now().date()
        if today != self.last_reset_day:
            self.daily_trades_count = 0
            self.last_reset_day = today
            self.state['statistics']['daily_pnl'] = 0.0
            self.state['statistics']['daily_trades'] = 0
            self.log("🌅 New day - daily counters reset")
            
    def should_trade(self, analysis, trend):
        """Decide if should execute trade with bear market filter"""
        level_config = self.config['levels'][self.state['current_level']]
        
        # BEAR MARKET FILTER
        if trend in ['strong_bearish', 'bearish']:
            # In bear market, increase confidence threshold
            bear_threshold = 0.85  # 85% confidence required in bear market
            if analysis['confidence'] < bear_threshold:
                self.state['statistics']['bear_market_trades_skipped'] += 1
                return False, f"Bear market detected - confidence {analysis['confidence']:.1%} < {bear_threshold:.0%}"
                
            # In bear market, only allow SELL trades
            if analysis['action'] == 'BUY':
                self.state['statistics']['bear_market_trades_skipped'] += 1
                return False, "Bear market - BUY trades disabled"
        
        # Check action
        if analysis['action'] == 'HOLD':
            return False, "AI recommends HOLD"
            
        # Check confidence threshold
        if analysis['confidence'] < level_config['confidence_threshold']:
            self.state['statistics']['low_confidence_skipped'] += 1
            return False, f"Confidence too low: {analysis['confidence']:.1%} < {level_config['confidence_threshold']:.1%}"
            
        # Check daily trade limit
        if self.daily_trades_count >= self.config['cycle_config']['max_daily_trades']:
            return False, f"Daily trade limit reached: {self.daily_trades_count}/{self.config['cycle_config']['max_daily_trades']}"
            
        # Check safety limits
        if self.state['statistics']['daily_pnl'] / self.state['initial_capital'] <= -self.config['safety_limits']['daily_loss_limit_percent']:
            return False, "Daily loss limit reached"
            
        return True, f"All conditions met ({analysis['reason']})"
        
    def execute_trade(self, pair, analysis, entry_price):
        """Execute trade entry with live price"""
        level_config = self.config['levels'][self.state['current_level']]
        
        position_size_usd = self.state['current_capital'] * level_config['position_size_percent']
        
        position = {
            'entry_time': datetime.now().isoformat(),
            'pair': pair,
            'direction': analysis['action'].lower(),
            'entry_price': entry_price,
            'position_size_usd': position_size_usd,
            'amount': position_size_usd / entry_price,
            'stop_loss_percent': level_config['stop_loss_percent'],
            'take_profit_percent': level_config['take_profit_percent'],
            'confidence': analysis['confidence'],
            'ai_reason': analysis['reason'],
            'ai_used': analysis['ai_used'],
            'level': self.state['current_level'],
            'status': 'open'
        }
        
        self.state['open_positions'].append(position)
        self.daily_trades_count += 1
        
        ai_badge = "🤖 AI" if analysis['ai_used'] else "📊 Rule"
        self.log(f"📈 ENTRY [{ai_badge}]: {position['pair']} {position['direction'].upper()} €{position['position_size_usd']:.2f} @ ${entry_price:,.2f}")
        self.log(f"   Confidence: {analysis['confidence']:.1%} | Reason: {analysis['reason']}")
        
        return position
        
    def monitor_position(self, position):
        """Monitor open position with live price"""
        # Get current live price
        market_data = self.get_live_price(position['pair'])
        if not market_data:
            return False
            
        current_price = market_data['price']
        
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
            'ai_reason': position.get('ai_reason', 'N/A'),
            'ai_used': position.get('ai_used', False),
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
        self.log(f"{emoji} EXIT ({reason}): {trade['pair']} €{net_pnl:+.4f} ({pnl_percent*100:+.2f}%) - Capital: €{self.state['current_capital']:.2f}")
        
        self.save_state()
        
    def run_cycle(self):
        """Run one trading cycle with live data"""
        self.reset_daily_counter()
        
        cycle_num = len(self.state['trades_history']) + len(self.state['open_positions']) + 1
        self.log(f"\n{'='*70}")
        self.log(f"🔄 CYCLE #{cycle_num} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"{'='*70}")
        
        # Monitor open positions first
        for position in list(self.state['open_positions']):
            self.monitor_position(position)
            
        # Analysis phase
        self.log("🔍 Market analysis phase (LIVE DATA)...")
        
        # Select pair
        pairs = self.config['trading_pairs']
        for pair in pairs:
            # Get live market data
            market_data = self.get_live_price(pair)
            if not market_data:
                continue
                
            # Detect trend
            trend, trend_confidence = self.detect_market_trend(pair)
            
            self.log(f"📊 {pair}: ${market_data['price']:,.2f} ({market_data['change_24h']:+.2f}% 24h) - Trend: {trend}")
            
            # AI analysis
            analysis = self.ai_analyze_with_context(pair, market_data, trend)
            
            # Decision
            should_trade, reason = self.should_trade(analysis, trend)
            
            if should_trade:
                self.log(f"✅ GO: {reason}")
                position = self.execute_trade(pair, analysis, market_data['price'])
                
                # Hold until exit conditions met
                self.log("⏳ Holding position (monitoring every 1 min)...")
                while position in self.state['open_positions']:
                    time.sleep(60)  # Check every 1 min
                    if not self.monitor_position(position):
                        break
                        
                break  # One trade per cycle
            else:
                self.log(f"⏭️  NO-GO: {reason}")
                
        self.save_state()
        
    def run(self):
        """Main run loop"""
        self.log(f"\n🚀 Starting {self.config['wallet_name']}")
        self.log(f"   Initial capital: €{self.config['initial_capital']:,.2f}")
        self.log(f"   Mode: LIVE PAPER TRADING")
        self.log(f"   Cycle interval: {self.config['cycle_config']['interval_hours']}h")
        self.log(f"   Max daily trades: {self.config['cycle_config']['max_daily_trades']}")
        self.log(f"   Bear market filter: ACTIVE")
        self.log(f"   Keep-alive: ENABLED (anti-hibernation)")
        
        try:
            while True:
                self.run_cycle()
                
                # Wait for next cycle with keep-alive to prevent sandbox hibernation
                interval_seconds = self.config['cycle_config']['interval_hours'] * 3600
                next_cycle = datetime.now() + timedelta(seconds=interval_seconds)
                self.log(f"⏰ Next cycle at {next_cycle.strftime('%H:%M:%S')}")
                
                # Sleep in chunks with keep-alive heartbeat every 5 minutes
                elapsed = 0
                chunk_size = 300  # 5 minutes
                while elapsed < interval_seconds:
                    sleep_time = min(chunk_size, interval_seconds - elapsed)
                    time.sleep(sleep_time)
                    elapsed += sleep_time
                    
                    # Keep-alive heartbeat (silent, no log spam)
                    if elapsed < interval_seconds:
                        # Touch a file to keep filesystem active
                        heartbeat_file = self.state_dir / ".heartbeat"
                        heartbeat_file.touch()
                        # Every 30 min, log a heartbeat
                        if elapsed % 1800 == 0:
                            remaining_hours = (interval_seconds - elapsed) / 3600
                            self.log(f"💓 Heartbeat: {remaining_hours:.1f}h until next cycle")
                
        except KeyboardInterrupt:
            self.log("\n🛑 Stopping wallet...")
            self.save_state()
            self.log("✅ State saved. Goodbye!")
            
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 wallet_runner_live.py <config_file>")
        sys.exit(1)
        
    config_path = sys.argv[1]
    runner = LivePaperTradingWallet(config_path)
    runner.run()
