#!/usr/bin/env python3
"""
AurumBotX Real-Time Bot Monitor
Sistema di monitoraggio continuo con alert automatici

Author: AurumBotX Team
Date: 13 Settembre 2025
Version: 2.0
"""

import os
import sys
import time
import json
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class RealTimeMonitor:
    def __init__(self):
        self.project_root = project_root
        self.db_path = self.project_root / "data" / "databases" / "mainnet_trading.db"
        self.wallet_path = self.project_root / "data" / "wallet_50_usdt.json"
        self.log_path = self.project_root / "logs" / "monitor.log"
        
        # Monitoring state
        self.last_trade_count = 0
        self.last_balance = 50.0
        self.last_check_time = datetime.now()
        self.alerts_sent = []
        
        # Thresholds for alerts
        self.thresholds = {
            'max_loss_per_trade': 2.0,  # USDT
            'max_daily_loss': 5.0,      # USDT
            'min_win_rate': 40.0,       # %
            'max_drawdown': 10.0,       # %
            'process_check_interval': 30,  # seconds
            'performance_check_interval': 60,  # seconds
        }
        
        print("🔍 AurumBotX Real-Time Monitor v2.0")
        print("=" * 50)
        print(f"📁 Project: {self.project_root}")
        print(f"🗄️ Database: {self.db_path}")
        print(f"💰 Wallet: {self.wallet_path}")
        print("=" * 50)
        
    def log_message(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        print(log_entry)
        
        # Write to log file
        try:
            with open(self.log_path, 'a') as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"⚠️ Log write error: {e}")
    
    def check_bot_processes(self):
        """Check if bot processes are running"""
        try:
            result = subprocess.run(
                ["ps", "aux"], 
                capture_output=True, 
                text=True
            )
            
            processes = result.stdout
            
            # Check for key processes
            bot_processes = {
                'start_50_usdt_challenge': False,
                'start_50_usdt_trading': False,
            }
            
            for process_name in bot_processes.keys():
                if process_name in processes:
                    bot_processes[process_name] = True
            
            # Alert if processes are missing
            for process, running in bot_processes.items():
                if not running:
                    self.send_alert(f"🚨 PROCESS DOWN: {process} not running!", "CRITICAL")
                    return False
            
            return True
            
        except Exception as e:
            self.send_alert(f"❌ Process check failed: {e}", "ERROR")
            return False
    
    def check_database_health(self):
        """Check database connectivity and integrity"""
        try:
            if not self.db_path.exists():
                self.send_alert("🚨 DATABASE MISSING: mainnet_trading.db not found!", "CRITICAL")
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Test query
            cursor.execute("SELECT COUNT(*) FROM enhanced_trades")
            trade_count = cursor.fetchone()[0]
            
            conn.close()
            
            self.log_message(f"✅ Database healthy: {trade_count} trades")
            return True
            
        except Exception as e:
            self.send_alert(f"❌ Database error: {e}", "ERROR")
            return False
    
    def analyze_trading_performance(self):
        """Analyze current trading performance"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all trades
            cursor.execute("SELECT * FROM enhanced_trades ORDER BY created_at DESC")
            trades = cursor.fetchall()
            
            if not trades:
                self.log_message("ℹ️ No trades found yet")
                conn.close()
                return True
            
            # Calculate metrics
            total_trades = len(trades)
            total_pnl = sum(trade[5] for trade in trades if trade[5])
            winning_trades = len([t for t in trades if t[5] > 0])
            losing_trades = len([t for t in trades if t[5] < 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Check for new trades
            if total_trades > self.last_trade_count:
                new_trades = total_trades - self.last_trade_count
                latest_trade = trades[0]
                
                self.log_message(f"🎯 NEW TRADE: {latest_trade[1]} {latest_trade[2]} | PnL: {latest_trade[5]:.4f} USDT")
                
                # Alert for significant trades
                if latest_trade[5] > 0.1:
                    self.send_alert(f"💰 BIG WIN: +{latest_trade[5]:.4f} USDT on {latest_trade[1]}", "SUCCESS")
                elif latest_trade[5] < -self.thresholds['max_loss_per_trade']:
                    self.send_alert(f"🚨 BIG LOSS: {latest_trade[5]:.4f} USDT on {latest_trade[1]}", "WARNING")
                
                self.last_trade_count = total_trades
            
            # Performance alerts
            if win_rate < self.thresholds['min_win_rate'] and total_trades >= 5:
                self.send_alert(f"⚠️ LOW WIN RATE: {win_rate:.1f}% (threshold: {self.thresholds['min_win_rate']}%)", "WARNING")
            
            if total_pnl < -self.thresholds['max_daily_loss']:
                self.send_alert(f"🚨 DAILY LOSS LIMIT: {total_pnl:.4f} USDT", "CRITICAL")
            
            # Log current performance
            self.log_message(f"📊 Performance: {total_trades} trades | PnL: {total_pnl:.4f} USDT | Win Rate: {win_rate:.1f}%")
            
            conn.close()
            return True
            
        except Exception as e:
            self.send_alert(f"❌ Performance analysis failed: {e}", "ERROR")
            return False
    
    def check_wallet_status(self):
        """Check wallet balance and updates"""
        try:
            if not self.wallet_path.exists():
                self.send_alert("🚨 WALLET MISSING: wallet_50_usdt.json not found!", "CRITICAL")
                return False
            
            with open(self.wallet_path, 'r') as f:
                wallet = json.load(f)
            
            current_balance = wallet['balance']['total_usdt']
            roi = wallet['performance_tracking']['roi_percentage']
            
            # Check for balance changes
            if abs(current_balance - self.last_balance) > 0.01:
                balance_change = current_balance - self.last_balance
                
                if balance_change > 0:
                    self.log_message(f"💰 BALANCE UP: {current_balance:.2f} USDT (+{balance_change:.4f})")
                else:
                    self.log_message(f"📉 BALANCE DOWN: {current_balance:.2f} USDT ({balance_change:.4f})")
                
                self.last_balance = current_balance
            
            # Milestone alerts
            milestones = [55, 60, 65, 70, 75, 80, 90, 100]
            for milestone in milestones:
                if current_balance >= milestone and f"milestone_{milestone}" not in self.alerts_sent:
                    self.send_alert(f"🎉 MILESTONE: {milestone} USDT reached! Current: {current_balance:.2f} USDT", "SUCCESS")
                    self.alerts_sent.append(f"milestone_{milestone}")
            
            # Drawdown alert
            initial_capital = 50.0
            drawdown = ((initial_capital - current_balance) / initial_capital * 100)
            if drawdown > self.thresholds['max_drawdown']:
                self.send_alert(f"🚨 MAX DRAWDOWN: {drawdown:.1f}% (threshold: {self.thresholds['max_drawdown']}%)", "CRITICAL")
            
            self.log_message(f"💳 Wallet: {current_balance:.2f} USDT | ROI: {roi:.2f}%")
            return True
            
        except Exception as e:
            self.send_alert(f"❌ Wallet check failed: {e}", "ERROR")
            return False
    
    def send_alert(self, message, level="INFO"):
        """Send alert message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format alert based on level
        if level == "CRITICAL":
            alert = f"🚨 CRITICAL [{timestamp}]: {message}"
        elif level == "WARNING":
            alert = f"⚠️ WARNING [{timestamp}]: {message}"
        elif level == "SUCCESS":
            alert = f"🎉 SUCCESS [{timestamp}]: {message}"
        elif level == "ERROR":
            alert = f"❌ ERROR [{timestamp}]: {message}"
        else:
            alert = f"ℹ️ INFO [{timestamp}]: {message}"
        
        print("\n" + "="*60)
        print(alert)
        print("="*60 + "\n")
        
        # Log alert
        self.log_message(message, level)
        
        # Prevent duplicate alerts
        alert_key = f"{level}_{message[:50]}"
        if alert_key not in self.alerts_sent:
            self.alerts_sent.append(alert_key)
            
            # Keep only last 100 alerts to prevent memory issues
            if len(self.alerts_sent) > 100:
                self.alerts_sent = self.alerts_sent[-50:]
    
    def generate_status_report(self):
        """Generate comprehensive status report"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "system_status": "operational",
                "alerts": [],
                "performance": {},
                "processes": {},
                "wallet": {}
            }
            
            # Check processes
            processes_ok = self.check_bot_processes()
            report["processes"]["status"] = "healthy" if processes_ok else "issues"
            
            # Check database
            db_ok = self.check_database_health()
            report["system_status"] = "operational" if db_ok else "degraded"
            
            # Get performance data
            if db_ok:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM enhanced_trades")
                trade_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT SUM(pnl) FROM enhanced_trades")
                total_pnl = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT COUNT(*) FROM enhanced_trades WHERE pnl > 0")
                winning_trades = cursor.fetchone()[0] or 0
                
                win_rate = (winning_trades / trade_count * 100) if trade_count > 0 else 0
                
                report["performance"] = {
                    "total_trades": trade_count,
                    "total_pnl": total_pnl,
                    "win_rate": win_rate,
                    "winning_trades": winning_trades
                }
                
                conn.close()
            
            # Get wallet data
            if self.wallet_path.exists():
                with open(self.wallet_path, 'r') as f:
                    wallet = json.load(f)
                
                report["wallet"] = {
                    "balance": wallet['balance']['total_usdt'],
                    "roi": wallet['performance_tracking']['roi_percentage']
                }
            
            return report
            
        except Exception as e:
            self.send_alert(f"❌ Status report failed: {e}", "ERROR")
            return None
    
    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        self.log_message("🔄 Starting monitoring cycle...")
        
        # Check all systems
        processes_ok = self.check_bot_processes()
        db_ok = self.check_database_health()
        performance_ok = self.analyze_trading_performance()
        wallet_ok = self.check_wallet_status()
        
        # Overall system health
        if all([processes_ok, db_ok, performance_ok, wallet_ok]):
            self.log_message("✅ All systems healthy")
            return True
        else:
            self.send_alert("⚠️ System health issues detected", "WARNING")
            return False
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        self.log_message("🚀 Starting real-time monitoring...")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                
                self.log_message(f"🔄 Monitoring cycle #{cycle_count}")
                
                # Run monitoring cycle
                self.run_monitoring_cycle()
                
                # Generate status report every 10 cycles
                if cycle_count % 10 == 0:
                    report = self.generate_status_report()
                    if report:
                        self.log_message(f"📊 Status Report: {json.dumps(report, indent=2)}")
                
                # Wait before next cycle
                time.sleep(self.thresholds['performance_check_interval'])
                
        except KeyboardInterrupt:
            self.log_message("👋 Monitoring stopped by user")
        except Exception as e:
            self.send_alert(f"❌ Monitoring error: {e}", "CRITICAL")

def main():
    """Main monitoring function"""
    monitor = RealTimeMonitor()
    
    try:
        monitor.start_monitoring()
    except Exception as e:
        print(f"❌ Monitor startup failed: {e}")

if __name__ == "__main__":
    main()

