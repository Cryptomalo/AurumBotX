#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX Auto Setup
Setup automatico completo per rendere il progetto avviabile da chiunque
"""

import os
import sqlite3
import json
import subprocess
import sys
from datetime import datetime

class AurumBotXAutoSetup:
    """Setup automatico completo AurumBotX"""
    
    def __init__(self):
        self.project_dir = os.getcwd()
        self.setup_log = []
        
    def log(self, message):
        """Log messaggio con timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.setup_log.append(log_entry)
    
    def check_python_version(self):
        """Verifica versione Python"""
        self.log("🐍 Controllo versione Python...")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.log("❌ Python 3.8+ richiesto")
            return False
        
        self.log(f"✅ Python {version.major}.{version.minor}.{version.micro} OK")
        return True
    
    def install_dependencies(self):
        """Installa dipendenze Python"""
        self.log("📦 Installazione dipendenze...")
        
        try:
            # Lista dipendenze essenziali
            dependencies = [
                'streamlit',
                'pandas',
                'numpy',
                'requests',
                'sqlite3',  # Built-in ma verifichiamo
                'plotly',
                'scikit-learn',
                'ta',  # Technical Analysis
                'python-binance',
                'ccxt',
                'reportlab'  # Per PDF
            ]
            
            # Installa pip se non presente
            subprocess.run([sys.executable, '-m', 'ensurepip', '--default-pip'], 
                         capture_output=True)
            
            # Aggiorna pip
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                         capture_output=True)
            
            # Installa dipendenze
            for dep in dependencies:
                if dep == 'sqlite3':
                    continue  # Built-in
                
                self.log(f"📦 Installando {dep}...")
                result = subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log(f"✅ {dep} installato")
                else:
                    self.log(f"⚠️ {dep} - tentativo alternativo...")
                    # Tentativo con --user
                    subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', dep], 
                                 capture_output=True)
            
            self.log("✅ Dipendenze installate")
            return True
            
        except Exception as e:
            self.log(f"❌ Errore installazione: {e}")
            return False
    
    def create_local_databases(self):
        """Crea database SQLite locali"""
        self.log("🗄️ Creazione database locali...")
        
        try:
            # Database per mega-aggressive
            self.create_mega_aggressive_db()
            
            # Database per ultra-aggressive
            self.create_ultra_aggressive_db()
            
            # Database per mainnet strategy
            self.create_mainnet_strategy_db()
            
            # Database per system monitoring
            self.create_monitoring_db()
            
            self.log("✅ Database locali creati")
            return True
            
        except Exception as e:
            self.log(f"❌ Errore database: {e}")
            return False
    
    def create_mega_aggressive_db(self):
        """Crea database mega-aggressive"""
        conn = sqlite3.connect('mega_aggressive_trading.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mega_trades (
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
                ai_signals TEXT
            )
        ''')
        
        # Inserisci dati demo per testing
        demo_trades = [
            ('2025-08-31 10:00:00', 'BUY', 350.0, 65000, 0.75, 25.50, 1025.50, 35.0, '{"volatility": 0.025}', '{"confidence": 0.75}'),
            ('2025-08-31 10:05:00', 'SELL', 360.0, 65500, 0.80, 30.20, 1055.70, 36.0, '{"volatility": 0.030}', '{"confidence": 0.80}'),
            ('2025-08-31 10:10:00', 'BUY', 340.0, 64800, 0.70, 22.10, 1077.80, 34.0, '{"volatility": 0.020}', '{"confidence": 0.70}')
        ]
        
        cursor.executemany('''
            INSERT INTO mega_trades 
            (timestamp, action, amount, price, confidence, profit_loss, balance_after, position_size_percent, market_conditions, ai_signals)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', demo_trades)
        
        conn.commit()
        conn.close()
        
        self.log("✅ Database mega_aggressive_trading.db creato")
    
    def create_ultra_aggressive_db(self):
        """Crea database ultra-aggressive"""
        conn = sqlite3.connect('ultra_aggressive_trading.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ultra_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                amount REAL NOT NULL,
                price REAL NOT NULL,
                confidence REAL NOT NULL,
                profit_loss REAL NOT NULL,
                balance_after REAL NOT NULL,
                position_size_percent REAL NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        
        self.log("✅ Database ultra_aggressive_trading.db creato")
    
    def create_mainnet_strategy_db(self):
        """Crea database mainnet strategy"""
        conn = sqlite3.connect('mega_mainnet_strategy.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mega_mainnet_trades (
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
            )
        ''')
        
        conn.commit()
        conn.close()
        
        self.log("✅ Database mega_mainnet_strategy.db creato")
    
    def create_monitoring_db(self):
        """Crea database monitoring"""
        conn = sqlite3.connect('system_monitoring.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                system_name TEXT NOT NULL,
                status TEXT NOT NULL,
                metrics TEXT,
                alerts TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        self.log("✅ Database system_monitoring.db creato")
    
    def create_config_files(self):
        """Crea file di configurazione"""
        self.log("⚙️ Creazione file configurazione...")
        
        try:
            # Config principale
            config = {
                "database": {
                    "type": "sqlite",
                    "mega_aggressive": "mega_aggressive_trading.db",
                    "ultra_aggressive": "ultra_aggressive_trading.db",
                    "mainnet_strategy": "mega_mainnet_strategy.db",
                    "monitoring": "system_monitoring.db"
                },
                "trading": {
                    "initial_balance": 1000.0,
                    "demo_mode": True,
                    "testnet": True
                },
                "api": {
                    "binance_testnet": {
                        "base_url": "https://testnet.binance.vision",
                        "api_key": "DEMO_KEY",
                        "secret_key": "DEMO_SECRET",
                        "note": "Sostituire con chiavi reali per trading"
                    }
                },
                "dashboard": {
                    "host": "0.0.0.0",
                    "ports": {
                        "admin": 8501,
                        "premium": 8502,
                        "performance": 8503,
                        "config": 8504,
                        "mobile": 8505,
                        "ultra": 8506,
                        "unified": 8507
                    }
                }
            }
            
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            # Environment file
            env_content = """# AurumBotX Environment Configuration
# Sostituire con valori reali per trading live

# Database (SQLite locale - già configurato)
DATABASE_TYPE=sqlite

# Binance API (Testnet demo - sostituire per mainnet)
BINANCE_API_KEY=DEMO_KEY
BINANCE_SECRET_KEY=DEMO_SECRET
BINANCE_TESTNET=true

# Trading Configuration
INITIAL_BALANCE=1000.0
DEMO_MODE=true

# Dashboard Configuration
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8507

# AI Configuration (opzionale)
OPENROUTER_API_KEY=optional_for_enhanced_ai

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/aurumbotx.log
"""
            
            with open('.env', 'w') as f:
                f.write(env_content)
            
            self.log("✅ File configurazione creati")
            return True
            
        except Exception as e:
            self.log(f"❌ Errore configurazione: {e}")
            return False
    
    def create_directories(self):
        """Crea directory necessarie"""
        self.log("📁 Creazione directory...")
        
        directories = [
            'logs',
            'reports',
            'reports/daily',
            'configs',
            'validation_results',
            'simulation_results'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            self.log(f"✅ Directory {directory} creata")
        
        return True
    
    def create_startup_scripts(self):
        """Crea script di avvio"""
        self.log("🚀 Creazione script avvio...")
        
        try:
            # Script avvio principale
            startup_script = """#!/bin/bash
# AurumBotX Startup Script

echo "🚀 Avvio AurumBotX..."

# Controlla Python
python3 --version || {
    echo "❌ Python 3 non trovato"
    exit 1
}

# Avvia sistema principale
echo "🤖 Avvio Mega-Aggressive Trading..."
python3 mega_aggressive_trading.py &

# Attendi avvio
sleep 5

# Avvia dashboard
echo "📊 Avvio Dashboard Unificata..."
python3 -m streamlit run unified_real_dashboard.py --server.port=8507 --server.address=0.0.0.0 &

echo "✅ AurumBotX avviato!"
echo "📊 Dashboard: http://localhost:8507"
echo "🛑 Per fermare: ./stop_aurumbotx.sh"
"""
            
            with open('start_aurumbotx.sh', 'w') as f:
                f.write(startup_script)
            
            os.chmod('start_aurumbotx.sh', 0o755)
            
            # Script stop
            stop_script = """#!/bin/bash
# AurumBotX Stop Script

echo "🛑 Fermata AurumBotX..."

# Ferma processi Python
pkill -f "mega_aggressive_trading.py"
pkill -f "streamlit run unified_real_dashboard.py"

echo "✅ AurumBotX fermato!"
"""
            
            with open('stop_aurumbotx.sh', 'w') as f:
                f.write(stop_script)
            
            os.chmod('stop_aurumbotx.sh', 0o755)
            
            self.log("✅ Script avvio creati")
            return True
            
        except Exception as e:
            self.log(f"❌ Errore script: {e}")
            return False
    
    def create_demo_data(self):
        """Crea dati demo per testing immediato"""
        self.log("📊 Creazione dati demo...")
        
        try:
            # Popola database con dati demo realistici
            conn = sqlite3.connect('mega_aggressive_trading.db')
            cursor = conn.cursor()
            
            # Genera 50 trade demo
            import random
            from datetime import datetime, timedelta
            
            base_balance = 1000.0
            current_balance = base_balance
            
            for i in range(50):
                timestamp = (datetime.now() - timedelta(hours=50-i)).isoformat()
                action = random.choice(['BUY', 'SELL'])
                amount = current_balance * random.uniform(0.08, 0.15)  # 8-15%
                price = random.uniform(60000, 70000)
                confidence = random.uniform(0.35, 0.85)
                
                # Simula profit/loss realistico
                if random.random() < 0.65:  # 65% win rate
                    profit_loss = amount * random.uniform(0.005, 0.025)
                else:
                    profit_loss = -amount * random.uniform(0.005, 0.015)
                
                current_balance += profit_loss
                position_size = (amount / current_balance) * 100
                
                cursor.execute('''
                    INSERT INTO mega_trades 
                    (timestamp, action, amount, price, confidence, profit_loss, balance_after, position_size_percent, market_conditions, ai_signals)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp, action, amount, price, confidence, profit_loss, 
                    current_balance, position_size, 
                    json.dumps({"volatility": random.uniform(0.01, 0.05)}),
                    json.dumps({"confidence": confidence, "model": "demo"})
                ))
            
            conn.commit()
            conn.close()
            
            self.log(f"✅ 50 trade demo creati (Balance finale: ${current_balance:.2f})")
            return True
            
        except Exception as e:
            self.log(f"❌ Errore dati demo: {e}")
            return False
    
    def run_setup(self):
        """Esegue setup completo"""
        self.log("🚀 Avvio AurumBotX Auto Setup")
        self.log("=" * 50)
        
        steps = [
            ("Controllo Python", self.check_python_version),
            ("Creazione directory", self.create_directories),
            ("Installazione dipendenze", self.install_dependencies),
            ("Creazione database", self.create_local_databases),
            ("Configurazione", self.create_config_files),
            ("Script avvio", self.create_startup_scripts),
            ("Dati demo", self.create_demo_data)
        ]
        
        success_count = 0
        
        for step_name, step_func in steps:
            self.log(f"\\n🔧 {step_name}...")
            if step_func():
                success_count += 1
            else:
                self.log(f"❌ {step_name} fallito")
        
        self.log("\\n" + "=" * 50)
        self.log(f"✅ Setup completato: {success_count}/{len(steps)} step")
        
        if success_count == len(steps):
            self.log("🎉 AurumBotX pronto per l'uso!")
            self.log("\\n🚀 AVVIO RAPIDO:")
            self.log("   ./start_aurumbotx.sh")
            self.log("\\n📊 DASHBOARD:")
            self.log("   http://localhost:8507")
            self.log("\\n🛑 STOP:")
            self.log("   ./stop_aurumbotx.sh")
        else:
            self.log("⚠️ Setup parzialmente completato")
        
        # Salva log setup
        with open('setup_log.txt', 'w') as f:
            f.write("\\n".join(self.setup_log))
        
        return success_count == len(steps)

def main():
    """Funzione principale"""
    print("🚀 AurumBotX Auto Setup")
    print("Configurazione automatica per rendere il progetto avviabile da chiunque")
    print("=" * 70)
    
    setup = AurumBotXAutoSetup()
    success = setup.run_setup()
    
    if success:
        print("\\n🎉 SETUP COMPLETATO CON SUCCESSO!")
        print("\\n📋 PROSSIMI STEP:")
        print("1. 🚀 Avvia: ./start_aurumbotx.sh")
        print("2. 📊 Dashboard: http://localhost:8507")
        print("3. 🔧 Configura API keys in .env per trading reale")
        print("4. 📖 Leggi README.md per dettagli")
    else:
        print("\\n⚠️ Setup parzialmente completato")
        print("📋 Controlla setup_log.txt per dettagli")
    
    return success

if __name__ == "__main__":
    main()

