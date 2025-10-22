#!/usr/bin/env python3
"""
AurumBotX Mainnet Trading Setup
Setup completo per trading reale su Binance

Author: AurumBotX Team
Date: 13 Settembre 2025
Version: 1.0
"""

import os
import sys
import json
import time
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class MainnetSetup:
    def __init__(self):
        self.start_time = datetime.now()
        self.setup_steps = []
        
    def log_step(self, step, status, details=""):
        """Log setup step"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icon = "✅" if status == "success" else "❌" if status == "error" else "⚠️"
        print(f"{timestamp} {status_icon} {step}: {details}")
        
        self.setup_steps.append({
            'step': step,
            'status': status,
            'timestamp': timestamp,
            'details': details
        })
    
    def check_prerequisites(self):
        """Check system prerequisites"""
        print("\n🔍 VERIFICA PREREQUISITI MAINNET")
        print("-" * 50)
        
        # Check trading engine
        engine_path = "src/core/trading_engine_usdt_sqlalchemy.py"
        if os.path.exists(engine_path):
            self.log_step("Trading Engine", "success", "File presente")
        else:
            self.log_step("Trading Engine", "error", "File mancante")
            return False
        
        # Check API server
        api_path = "src/api/api_server_usdt.py"
        if os.path.exists(api_path):
            self.log_step("API Server", "success", "File presente")
        else:
            self.log_step("API Server", "error", "File mancante")
            return False
        
        # Check database
        db_path = "src/api/data/aurumbotx_usdt.db"
        if os.path.exists(db_path):
            self.log_step("Database", "success", "Database presente")
        else:
            self.log_step("Database", "warning", "Database sarà creato")
        
        return True
    
    def create_env_template(self):
        """Create environment template for API keys"""
        print("\n🔑 CONFIGURAZIONE API KEYS")
        print("-" * 50)
        
        env_template = """# AurumBotX Mainnet Configuration
# IMPORTANTE: Inserire le proprie API keys Binance

# Binance API Configuration
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here

# Trading Configuration
TRADING_MODE=mainnet
INITIAL_CAPITAL=30.0
CURRENCY=USDT

# Security Configuration
ENCRYPTION_KEY=aurumbotx_secure_key_2025
JWT_SECRET=aurumbotx_jwt_secret_key

# Telegram Configuration (optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Risk Management
MAX_RISK_PER_TRADE=0.02
MAX_DAILY_RISK=0.08
EMERGENCY_STOP_LOSS=0.20

# API Configuration
API_PORT=8005
API_HOST=0.0.0.0
"""
        
        try:
            with open('.env.mainnet', 'w') as f:
                f.write(env_template)
            
            self.log_step("ENV Template", "success", "Creato .env.mainnet")
            
            print("\n📝 ISTRUZIONI API KEYS:")
            print("1. Vai su Binance.com → Account → API Management")
            print("2. Crea nuova API Key con permessi SPOT TRADING")
            print("3. Copia API Key e Secret Key")
            print("4. Modifica file .env.mainnet con le tue keys")
            print("5. IMPORTANTE: NON abilitare withdrawals per sicurezza")
            
        except Exception as e:
            self.log_step("ENV Template", "error", str(e))
    
    def create_mainnet_config(self):
        """Create mainnet trading configuration"""
        print("\n⚙️ CONFIGURAZIONE MAINNET TRADING")
        print("-" * 50)
        
        mainnet_config = {
            "trading_mode": "mainnet",
            "exchange": "binance",
            "initial_capital": 30.0,
            "currency": "USDT",
            "challenge_name": "30_usdt_mainnet_challenge",
            "target_amount": 240.0,
            "growth_multiplier": 8.0,
            
            "phases": {
                "phase_1": {
                    "name": "Aggressive Growth",
                    "balance_range": [30, 60],
                    "risk_per_trade": 0.35,
                    "stop_loss": 0.10,
                    "max_positions": 2,
                    "target": "30 → 60 USDT"
                },
                "phase_2": {
                    "name": "Moderate Expansion",
                    "balance_range": [60, 120],
                    "risk_per_trade": 0.25,
                    "stop_loss": 0.08,
                    "max_positions": 3,
                    "target": "60 → 120 USDT"
                },
                "phase_3": {
                    "name": "Conservative Growth",
                    "balance_range": [120, 240],
                    "risk_per_trade": 0.15,
                    "stop_loss": 0.06,
                    "max_positions": 4,
                    "target": "120 → 240 USDT"
                }
            },
            
            "trading_pairs": [
                "BTCUSDT",
                "ETHUSDT",
                "ADAUSDT",
                "SOLUSDT"
            ],
            
            "risk_management": {
                "max_daily_loss": 0.05,
                "max_drawdown": 0.15,
                "emergency_stop_loss": 0.20,
                "position_sizing": "dynamic",
                "correlation_limit": 0.7
            },
            
            "ai_configuration": {
                "confidence_threshold": 0.70,
                "analysis_frequency": "4_hours",
                "market_sentiment_weight": 0.4,
                "technical_analysis_weight": 0.6
            },
            
            "performance_targets": {
                "monthly_return": 0.20,
                "win_rate": 0.70,
                "sharpe_ratio": 2.0,
                "max_consecutive_losses": 3,
                "expected_completion": "3_months"
            },
            
            "schedule": {
                "trading_hours": "24/7",
                "analysis_interval": "4_hours",
                "risk_check_interval": "30_minutes",
                "report_frequency": "daily"
            },
            
            "notifications": {
                "telegram_enabled": True,
                "email_enabled": False,
                "trade_notifications": True,
                "error_notifications": True,
                "daily_reports": True
            }
        }
        
        try:
            config_path = "config/mainnet_trading.json"
            with open(config_path, 'w') as f:
                json.dump(mainnet_config, f, indent=2)
            
            self.log_step("Mainnet Config", "success", f"Creato {config_path}")
            
        except Exception as e:
            self.log_step("Mainnet Config", "error", str(e))
    
    def create_mainnet_launcher(self):
        """Create mainnet trading launcher script"""
        print("\n🚀 CREAZIONE LAUNCHER MAINNET")
        print("-" * 50)
        
        launcher_code = '''#!/usr/bin/env python3
"""
AurumBotX Mainnet Trading Launcher
Avvia il trading reale su Binance

Usage: python start_mainnet_trading.py
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime

# Load environment variables
def load_env():
    """Load environment variables from .env.mainnet"""
    if os.path.exists('.env.mainnet'):
        with open('.env.mainnet', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def check_api_keys():
    """Check if API keys are configured"""
    api_key = os.getenv('BINANCE_API_KEY', '')
    secret_key = os.getenv('BINANCE_SECRET_KEY', '')
    
    if not api_key or api_key == 'your_binance_api_key_here':
        print("❌ ERRORE: BINANCE_API_KEY non configurata")
        print("📝 Modifica il file .env.mainnet con le tue API keys")
        return False
    
    if not secret_key or secret_key == 'your_binance_secret_key_here':
        print("❌ ERRORE: BINANCE_SECRET_KEY non configurata")
        print("📝 Modifica il file .env.mainnet con le tue API keys")
        return False
    
    print("✅ API Keys configurate correttamente")
    return True

def test_binance_connection():
    """Test Binance API connection"""
    try:
        from binance.client import Client
        
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        client = Client(api_key, secret_key, testnet=False)
        
        # Test connection
        account_info = client.get_account()
        
        print("✅ Connessione Binance OK")
        print(f"📊 Account Status: {account_info['accountType']}")
        
        # Check USDT balance
        usdt_balance = 0
        for balance in account_info['balances']:
            if balance['asset'] == 'USDT':
                usdt_balance = float(balance['free'])
                break
        
        print(f"💰 USDT Balance: {usdt_balance:.2f} USDT")
        
        if usdt_balance < 30:
            print("⚠️ WARNING: Balance insufficiente per 30 USDT Challenge")
            print("💡 Deposita almeno 30 USDT per iniziare")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ ERRORE Connessione Binance: {e}")
        return False

def start_trading_engine():
    """Start the trading engine"""
    print("\\n🚀 AVVIO TRADING ENGINE MAINNET")
    print("-" * 50)
    
    try:
        # Start API server
        print("⚡ Avvio API Server...")
        api_process = subprocess.Popen([
            'python', 'src/api/api_server_usdt.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(3)
        
        # Start trading engine
        print("🤖 Avvio Trading Engine...")
        trading_process = subprocess.Popen([
            'python', 'src/core/trading_engine_usdt_sqlalchemy.py', '--config', 'config/mainnet_trading.json'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        
        time.sleep(2)
        
        print("✅ Sistema avviato con successo!")
        print("📊 Monitoring: https://8005-i7bmjtw6ur40fabqcok6m-51cc44c0.manusvm.computer/health")
        print("🎛️ Dashboard: https://8501-i7bmjtw6ur40fabqcok6m-51cc44c0.manusvm.computer")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRORE Avvio Sistema: {e}")
        return False

def main():
    """Main launcher function"""
    print("🚀 AURUMBOTX MAINNET TRADING LAUNCHER")
    print("=" * 60)
    print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Load environment
    load_env()
    
    # Check API keys
    if not check_api_keys():
        return False
    
    # Test Binance connection
    if not test_binance_connection():
        return False
    
    # Start trading
    if not start_trading_engine():
        return False
    
    print("\\n🎉 MAINNET TRADING ATTIVO!")
    print("💰 30 USDT Challenge iniziata")
    print("🎯 Target: 240 USDT (8x growth)")
    print("⏱️ Timeframe: 2-3 mesi")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\\n❌ Setup fallito. Controlla configurazione.")
        sys.exit(1)
'''
        
        try:
            launcher_path = "start_mainnet_trading.py"
            with open(launcher_path, 'w') as f:
                f.write(launcher_code)
            
            # Make executable
            os.chmod(launcher_path, 0o755)
            
            self.log_step("Mainnet Launcher", "success", f"Creato {launcher_path}")
            
        except Exception as e:
            self.log_step("Mainnet Launcher", "error", str(e))
    
    def create_quick_start_guide(self):
        """Create quick start guide"""
        print("\n📖 CREAZIONE GUIDA QUICK START")
        print("-" * 50)
        
        guide = """# 🚀 AurumBotX Mainnet Trading - Quick Start Guide

## ⚡ SETUP RAPIDO (5 MINUTI)

### 1. CONFIGURAZIONE API BINANCE
```bash
# Modifica file .env.mainnet
nano .env.mainnet

# Inserisci le tue API keys:
BINANCE_API_KEY=la_tua_api_key
BINANCE_SECRET_KEY=la_tua_secret_key
```

### 2. VERIFICA BALANCE
- Deposita almeno 30 USDT su Binance Spot Wallet
- Verifica che le API keys abbiano permessi SPOT TRADING
- NON abilitare withdrawals per sicurezza

### 3. AVVIO TRADING
```bash
# Avvia trading mainnet
python start_mainnet_trading.py
```

### 4. MONITORING
- **Dashboard**: https://8501-i7bmjtw6ur40fabqcok6m-51cc44c0.manusvm.computer
- **API Health**: https://8005-i7bmjtw6ur40fabqcok6m-51cc44c0.manusvm.computer/health
- **Telegram**: @AurumBotX_Bot

## 🎯 30 USDT CHALLENGE

### STRATEGIA 3 FASI:
1. **Aggressive** (30→60 USDT): 35% risk, 10% stop loss
2. **Moderate** (60→120 USDT): 25% risk, 8% stop loss  
3. **Conservative** (120→240 USDT): 15% risk, 6% stop loss

### TARGET:
- **Capitale Iniziale**: 30 USDT
- **Target Finale**: 240 USDT
- **Growth**: 8x (800%)
- **Timeframe**: 2-3 mesi

## 🛡️ SICUREZZA

### PROTEZIONI ATTIVE:
- Stop loss automatici
- Risk management dinamico
- Emergency stop system
- Real-time monitoring

### CONTROLLI MANUALI:
- **Stop Trading**: Telegram `/stop`
- **Emergency Stop**: Dashboard red button
- **API Disable**: Binance dashboard

## 📊 MONITORING

### METRICHE CHIAVE:
- **Balance**: Real-time USDT
- **P&L**: Profit/Loss giornaliero
- **Win Rate**: % trades vincenti
- **Drawdown**: Perdita massima

### NOTIFICHE:
- **Telegram**: Trade alerts
- **Dashboard**: Real-time updates
- **Email**: Daily reports (optional)

## 🚨 TROUBLESHOOTING

### ERRORI COMUNI:
1. **API Keys Invalid**: Verifica keys su Binance
2. **Insufficient Balance**: Deposita più USDT
3. **Connection Error**: Controlla internet
4. **Permission Denied**: Abilita SPOT trading

### SUPPORTO:
- **Telegram**: @AurumBotX_Bot
- **Logs**: `tail -f logs/trading.log`
- **Health Check**: API endpoint /health

---

**🎉 BUON TRADING CON AURUMBOTX!**
"""
        
        try:
            guide_path = "MAINNET_QUICK_START.md"
            with open(guide_path, 'w') as f:
                f.write(guide)
            
            self.log_step("Quick Start Guide", "success", f"Creato {guide_path}")
            
        except Exception as e:
            self.log_step("Quick Start Guide", "error", str(e))
    
    def generate_setup_report(self):
        """Generate setup completion report"""
        print("\n📊 REPORT SETUP MAINNET")
        print("-" * 50)
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        success_count = len([s for s in self.setup_steps if s['status'] == 'success'])
        total_count = len(self.setup_steps)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        report = {
            'setup_session': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'total_steps': total_count,
                'success_rate': success_rate
            },
            'setup_steps': self.setup_steps,
            'files_created': [
                '.env.mainnet',
                'config/mainnet_trading.json',
                'start_mainnet_trading.py',
                'MAINNET_QUICK_START.md'
            ],
            'next_actions': [
                "1. Configurare API keys in .env.mainnet",
                "2. Depositare 30+ USDT su Binance",
                "3. Eseguire: python start_mainnet_trading.py",
                "4. Monitorare dashboard e performance"
            ]
        }
        
        try:
            report_path = f"reports/mainnet_setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.log_step("Setup Report", "success", f"Salvato in {report_path}")
            
        except Exception as e:
            self.log_step("Setup Report", "error", str(e))
        
        return report
    
    def run_complete_setup(self):
        """Run complete mainnet setup"""
        print("🚀 AURUMBOTX MAINNET SETUP")
        print("=" * 60)
        print(f"⏰ Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎯 Obiettivo: Trading Reale 30 USDT → 240 USDT")
        print("=" * 60)
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("\n❌ SETUP FALLITO: Prerequisiti mancanti")
            return False
        
        # Run setup steps
        self.create_env_template()
        self.create_mainnet_config()
        self.create_mainnet_launcher()
        self.create_quick_start_guide()
        
        # Generate report
        report = self.generate_setup_report()
        
        # Summary
        print("\n🎉 SETUP MAINNET COMPLETATO!")
        print("=" * 60)
        print(f"✅ Successi: {len([s for s in self.setup_steps if s['status'] == 'success'])}")
        print(f"⚠️ Warning: {len([s for s in self.setup_steps if s['status'] == 'warning'])}")
        print(f"❌ Errori: {len([s for s in self.setup_steps if s['status'] == 'error'])}")
        print(f"📊 Success Rate: {report['setup_session']['success_rate']:.1f}%")
        
        print("\n🎯 PROSSIMI PASSI:")
        for i, action in enumerate(report['next_actions'], 1):
            print(f"  {action}")
        
        print("\n🚀 PRONTO PER TRADING MAINNET!")
        
        return True

def main():
    """Main setup function"""
    setup = MainnetSetup()
    success = setup.run_complete_setup()
    
    if success:
        print("\n💰 30 USDT CHALLENGE READY!")
        print("🎯 Target: 240 USDT (8x growth)")
        print("⏱️ Timeframe: 2-3 mesi")
    else:
        print("\n❌ Setup incompleto. Controlla errori sopra.")

if __name__ == "__main__":
    main()

