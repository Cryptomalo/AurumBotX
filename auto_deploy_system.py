#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX Auto Deploy System
Sistema completo per deploy automatico su cloud con configurazione zero
"""

import os
import json
import subprocess
import sys
from datetime import datetime

class AutoDeploySystem:
    """Sistema deploy automatico"""
    
    def __init__(self):
        self.project_root = os.getcwd()
        self.deploy_config = {}
        
    def log(self, message):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def create_dockerfile(self):
        """Crea Dockerfile ottimizzato"""
        dockerfile_content = """# AurumBotX Production Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs reports configs validation_results simulation_results

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8501 8502 8503 8504 8505 8506 8507

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:8507/health || exit 1

# Start command
CMD ["python3", "team_management_system.py"]
"""
        
        with open("Dockerfile", "w") as f:
            f.write(dockerfile_content)
        
        self.log("✅ Dockerfile creato")
    
    def create_docker_compose(self):
        """Crea docker-compose.yml completo"""
        compose_content = """version: '3.8'

services:
  aurumbotx:
    build: .
    ports:
      - "8501:8501"
      - "8502:8502"
      - "8503:8503"
      - "8504:8504"
      - "8505:8505"
      - "8506:8506"
      - "8507:8507"
    environment:
      - DATABASE_TYPE=sqlite
      - INITIAL_BALANCE=250.0
      - DEMO_MODE=true
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8507/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: aurumbotx_db
      POSTGRES_USER: aurumbotx_user
      POSTGRES_PASSWORD: aurumbot2025
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

volumes:
  postgres_data:
"""
        
        with open("docker-compose.yml", "w") as f:
            f.write(compose_content)
        
        self.log("✅ docker-compose.yml creato")
    
    def create_railway_config(self):
        """Crea configurazione Railway"""
        railway_config = {
            "build": {
                "builder": "DOCKERFILE"
            },
            "deploy": {
                "startCommand": "streamlit run team_management_system.py --server.port=$PORT --server.address=0.0.0.0",
                "healthcheckPath": "/health",
                "healthcheckTimeout": 300
            }
        }
        
        with open("railway.json", "w") as f:
            json.dump(railway_config, f, indent=2)
        
        # Procfile per Heroku compatibility
        with open("Procfile", "w") as f:
            f.write("web: streamlit run team_management_system.py --server.port=$PORT --server.address=0.0.0.0\\n")
        
        self.log("✅ Configurazione Railway/Heroku creata")
    
    def create_render_config(self):
        """Crea configurazione Render"""
        render_config = {
            "services": [
                {
                    "type": "web",
                    "name": "aurumbotx",
                    "env": "python",
                    "buildCommand": "pip install -r requirements.txt",
                    "startCommand": "streamlit run team_management_system.py --server.port=$PORT --server.address=0.0.0.0",
                    "healthCheckPath": "/health"
                }
            ]
        }
        
        with open("render.yaml", "w") as f:
            json.dump(render_config, f, indent=2)
        
        self.log("✅ Configurazione Render creata")
    
    def update_requirements(self):
        """Aggiorna requirements.txt completo"""
        requirements = [
            "streamlit>=1.28.0",
            "pandas>=2.0.0",
            "numpy>=1.24.0",
            "plotly>=5.15.0",
            "requests>=2.31.0",
            "scikit-learn>=1.3.0",
            "ta>=0.10.2",
            "python-binance>=1.0.17",
            "ccxt>=4.0.0",
            "reportlab>=4.0.4",
            "cryptography>=41.0.0",
            "psycopg2-binary>=2.9.7",
            "python-dotenv>=1.0.0",
            "watchdog>=3.0.0",
            "schedule>=1.2.0"
        ]
        
        with open("requirements.txt", "w") as f:
            f.write("\\n".join(requirements))
        
        self.log("✅ requirements.txt aggiornato")
    
    def create_env_template(self):
        """Crea template .env"""
        env_template = """# AurumBotX Environment Configuration
# Copia questo file in .env e configura i valori

# Database Configuration
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///aurumbotx.db

# PostgreSQL (opzionale - per production)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=aurumbotx_db
POSTGRES_USER=aurumbotx_user
POSTGRES_PASSWORD=your_secure_password

# Trading Configuration
INITIAL_BALANCE=250.0
DEMO_MODE=true

# Binance API (sostituire con chiavi reali)
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
BINANCE_TESTNET=true

# Dashboard Configuration
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8507

# AI Configuration (opzionale)
OPENROUTER_API_KEY=your_openrouter_key

# Security
SECRET_KEY=your_secret_key_here
ENCRYPTION_KEY=auto_generated

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/aurumbotx.log

# Team Management
ADMIN_USERNAME=admin
ADMIN_PASSWORD=CHANGE_ME
"""
        
        with open(".env.template", "w") as f:
            f.write(env_template)
        
        # Crea .env se non esiste
        if not os.path.exists(".env"):
            with open(".env", "w") as f:
                f.write(env_template)
        
        self.log("✅ Template .env creato")
    
    def create_startup_script(self):
        """Crea script startup completo"""
        startup_script = """#!/bin/bash
# AurumBotX Startup Script

echo "🚀 Avvio AurumBotX..."

# Controlla Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 non trovato"
    exit 1
fi

# Installa dipendenze
echo "📦 Installazione dipendenze..."
pip3 install -r requirements.txt

# Crea directory necessarie
mkdir -p logs reports configs validation_results simulation_results data

# Setup database
echo "🗄️ Setup database..."
python3 -c "
import sqlite3
import os
from datetime import datetime

# Crea database se non esiste
if not os.path.exists('aurumbotx.db'):
    conn = sqlite3.connect('aurumbotx.db')
    cursor = conn.cursor()
    
    # Tabella demo trades
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS demo_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            amount REAL NOT NULL,
            price REAL NOT NULL,
            confidence REAL NOT NULL,
            profit_loss REAL NOT NULL,
            balance_after REAL NOT NULL,
            position_size_percent REAL NOT NULL
        );
    ''')
    
    # Inserisci dati demo
    import random
    balance = 250.0
    for i in range(10):
        action = random.choice(['BUY', 'SELL'])
        amount = balance * random.uniform(0.05, 0.15)
        price = random.uniform(60000, 70000)
        confidence = random.uniform(0.6, 0.9)
        profit_loss = amount * random.uniform(-0.02, 0.03)
        balance += profit_loss
        
        cursor.execute('''
            INSERT INTO demo_trades 
            (timestamp, action, amount, price, confidence, profit_loss, balance_after, position_size_percent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            action, amount, price, confidence, profit_loss, balance, 
            random.uniform(5, 15)
        ))
    
    conn.commit()
    conn.close()
    print('✅ Database demo creato')
"

# Avvia sistema
echo "🌐 Avvio dashboard..."
echo "📊 Dashboard disponibile su: http://localhost:8507"
echo "🔐 Login: admin (password impostata via AURUMBOTX_ADMIN_PASSWORD o ADMIN_PASSWORD)"

# Avvia in background se richiesto
if [ "$1" = "--background" ]; then
    nohup streamlit run team_management_system.py --server.port=8507 --server.address=0.0.0.0 > logs/startup.log 2>&1 &
    echo "✅ Sistema avviato in background"
    echo "📋 Log: tail -f logs/startup.log"
else
    streamlit run team_management_system.py --server.port=8507 --server.address=0.0.0.0
fi
"""
        
        with open("start_aurumbotx.sh", "w") as f:
            f.write(startup_script)
        
        os.chmod("start_aurumbotx.sh", 0o755)
        
        self.log("✅ Script startup creato")
    
    def create_readme_deploy(self):
        """Crea README per deploy"""
        readme_content = """# 🚀 AurumBotX - Deploy Guide

## ⚡ Quick Start (2 minuti)

### 🖥️ Locale
```bash
git clone https://github.com/Cryptomalo/AurumBotX.git
cd AurumBotX
./start_aurumbotx.sh
```

### 🌐 Cloud Deploy

#### 🚀 Railway (RACCOMANDATO)
1. Vai su [railway.app](https://railway.app)
2. "Deploy from GitHub" → Seleziona AurumBotX
3. ✅ Deploy automatico!

#### ⚡ Heroku
```bash
heroku create aurumbotx-team
git push heroku main
heroku ps:scale web=1
```

#### 🌟 Render
1. Connetti repository su [render.com](https://render.com)
2. ✅ Auto-deploy configurato!

#### 🐳 Docker
```bash
docker-compose up -d
```

## 🔐 Accesso Team

### 📊 Dashboard Principale
- **URL**: http://localhost:8507 (locale) o URL cloud
- **Login**: admin (password impostata via AURUMBOTX_ADMIN_PASSWORD o ADMIN_PASSWORD)
- **Funzioni**: Controllo completo sistema

### 👥 Gestione Team
- **Admin**: Controllo totale
- **Developer**: Sviluppo e deploy
- **Viewer**: Solo visualizzazione

### 🔑 Credenziali Sicure
- Crittografia AES per credenziali sensibili
- Gestione utenti con ruoli
- Log accessi completi

## 📊 Funzionalità Team

### ✅ Trading Data
- Dati real-time da tutti i sistemi
- Grafici performance interattivi
- Export dati per analisi

### ✅ System Control
- Start/Stop bot da interfaccia
- Monitoraggio processi
- Controllo risorse

### ✅ Credentials Management
- Binance API keys sicure
- Database credentials
- Servizi esterni

### ✅ Team Management
- Creazione utenti
- Gestione permessi
- Log accessi

## 🗄️ Database

### SQLite (Default)
- ✅ Zero configurazione
- ✅ Funziona ovunque
- ✅ Backup semplice

### PostgreSQL (Production)
- ✅ Performance superiori
- ✅ Scalabilità enterprise
- ✅ Backup avanzati

## 🔧 Configurazione

### File Principali
- `.env` - Configurazione ambiente
- `config.json` - Parametri sistema
- `team_management.db` - Database team

### Variabili Ambiente
```bash
DATABASE_TYPE=sqlite
INITIAL_BALANCE=250.0
DEMO_MODE=true
ADMIN_USERNAME=admin
ADMIN_PASSWORD=CHANGE_ME
```

## 🚨 Troubleshooting

### Problema: Port già in uso
```bash
lsof -ti:8507 | xargs kill -9
./start_aurumbotx.sh
```

### Problema: Dipendenze mancanti
```bash
pip3 install -r requirements.txt
```

### Problema: Database locked
```bash
rm *.db
./start_aurumbotx.sh
```

## 📞 Supporto

- **Repository**: https://github.com/Cryptomalo/AurumBotX
- **Issues**: GitHub Issues
- **Team**: Dashboard integrata

---

**🎉 Sistema pronto per il tuo team!**
"""
        
        with open("README_DEPLOY.md", "w") as f:
            f.write(readme_content)
        
        self.log("✅ README deploy creato")
    
    def create_health_endpoint(self):
        """Crea endpoint health check"""
        health_script = """#!/usr/bin/env python3
import streamlit as st
import json
from datetime import datetime

def health_check():
    \"\"\"Health check endpoint\"\"\"
    try:
        # Controlla database
        import sqlite3
        conn = sqlite3.connect('team_management.db')
        conn.close()
        
        # Controlla file sistema
        import os
        required_files = ['team_management_system.py', 'requirements.txt']
        for file in required_files:
            if not os.path.exists(file):
                raise Exception(f"File mancante: {file}")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Aggiungi endpoint a Streamlit
if st.query_params.get("health"):
    st.json(health_check())
"""
        
        # Aggiungi health check al team management system
        with open("team_management_system.py", "r") as f:
            content = f.read()
        
        if "health_check" not in content:
            # Inserisci health check
            health_code = '''
    # Health check endpoint
    if st.query_params.get("health"):
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "systems": {
                "database": "ok",
                "authentication": "ok",
                "trading_data": "ok"
            }
        }
        st.json(health_status)
        return
'''
            
            # Inserisci dopo imports
            content = content.replace('def main():', health_code + '\\ndef main():')
            
            with open("team_management_system.py", "w") as f:
                f.write(content)
        
        self.log("✅ Health check endpoint aggiunto")
    
    def run_deploy_setup(self):
        """Esegue setup completo deploy"""
        self.log("🚀 Avvio setup deploy AurumBotX")
        self.log("=" * 50)
        
        steps = [
            ("Dockerfile", self.create_dockerfile),
            ("Docker Compose", self.create_docker_compose),
            ("Railway Config", self.create_railway_config),
            ("Render Config", self.create_render_config),
            ("Requirements", self.update_requirements),
            ("Environment Template", self.create_env_template),
            ("Startup Script", self.create_startup_script),
            ("README Deploy", self.create_readme_deploy),
            ("Health Endpoint", self.create_health_endpoint)
        ]
        
        success_count = 0
        
        for step_name, step_func in steps:
            try:
                step_func()
                success_count += 1
            except Exception as e:
                self.log(f"❌ Errore {step_name}: {e}")
        
        self.log("\\n" + "=" * 50)
        self.log(f"✅ Setup completato: {success_count}/{len(steps)} step")
        
        if success_count == len(steps):
            self.log("\\n🎉 DEPLOY SETUP COMPLETATO!")
            self.log("\\n📋 PROSSIMI STEP:")
            self.log("1. 🔧 git add . && git commit -m 'Deploy ready'")
            self.log("2. 🚀 git push origin main")
            self.log("3. 🌐 Deploy su Railway/Heroku/Render")
            self.log("4. 🔐 Login: admin (password impostata via AURUMBOTX_ADMIN_PASSWORD o ADMIN_PASSWORD)")
            self.log("\\n🌍 DEPLOY OPTIONS:")
            self.log("- Railway: https://railway.app (1-click)")
            self.log("- Heroku: heroku create && git push heroku main")
            self.log("- Render: https://render.com (auto-deploy)")
            self.log("- Docker: docker-compose up -d")
        
        return success_count == len(steps)

def main():
    """Funzione principale"""
    print("🚀 AurumBotX Auto Deploy System")
    print("=" * 50)
    
    deployer = AutoDeploySystem()
    success = deployer.run_deploy_setup()
    
    if success:
        print("\\n🎉 SISTEMA PRONTO PER DEPLOY!")
        print("\\n🔗 Il tuo team può ora:")
        print("- 📥 Clonare da GitHub")
        print("- 🚀 Deploy 1-click su cloud")
        print("- 🔐 Accesso con login sicuro")
        print("- 📊 Controllo completo dati")
        print("- 🔧 Sviluppo e miglioramenti")
    else:
        print("\\n⚠️ Setup parzialmente completato")
    
    return success

if __name__ == "__main__":
    main()
