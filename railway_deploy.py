#!/usr/bin/env python3
"""
AurumBotX Railway Deploy Setup
Script per deploy gratuito su Railway.app
"""

import os
import json
import subprocess
from datetime import datetime

def create_railway_config():
    """Crea configurazione Railway"""
    
    # railway.json
    railway_config = {
        "build": {
            "builder": "NIXPACKS"
        },
        "deploy": {
            "startCommand": "streamlit run unified_real_dashboard.py --server.port=$PORT --server.address=0.0.0.0",
            "healthcheckPath": "/",
            "healthcheckTimeout": 100,
            "restartPolicyType": "ON_FAILURE",
            "restartPolicyMaxRetries": 10
        }
    }
    
    with open('railway.json', 'w') as f:
        json.dump(railway_config, f, indent=2)
    
    print("✅ railway.json creato")

def create_dockerfile():
    """Crea Dockerfile ottimizzato per Railway"""
    
    dockerfile_content = """# AurumBotX Railway Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data backups

# Set environment variables
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=$PORT
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:$PORT/_stcore/health || exit 1

# Start command
CMD ["streamlit", "run", "unified_real_dashboard.py", "--server.port=$PORT", "--server.address=0.0.0.0"]
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    
    print("✅ Dockerfile creato")

def create_procfile():
    """Crea Procfile per Heroku compatibility"""
    
    procfile_content = """web: streamlit run unified_real_dashboard.py --server.port=$PORT --server.address=0.0.0.0
worker: python3 mega_aggressive_trading.py
"""
    
    with open('Procfile', 'w') as f:
        f.write(procfile_content)
    
    print("✅ Procfile creato")

def create_requirements_txt():
    """Crea requirements.txt ottimizzato"""
    
    requirements = [
        "streamlit>=1.28.0",
        "pandas>=1.5.0",
        "numpy>=1.24.0",
        "plotly>=5.15.0",
        "sqlite3",  # Built-in
        "requests>=2.31.0",
        "python-binance>=1.0.19",
        "ccxt>=4.0.0",
        "scikit-learn>=1.3.0",
        "aiohttp>=3.8.0",
        "python-dotenv>=1.0.0",
        "psutil>=5.9.0"
    ]
    
    with open('requirements.txt', 'w') as f:
        for req in requirements:
            if req != "sqlite3":  # Skip built-in
                f.write(f"{req}\\n")
    
    print("✅ requirements.txt aggiornato")

def create_railway_start_script():
    """Crea script di avvio per Railway"""
    
    start_script = """#!/bin/bash

# AurumBotX Railway Start Script

echo "🚀 Starting AurumBotX on Railway..."

# Set environment variables
export PYTHONPATH=/app
export STREAMLIT_SERVER_PORT=${PORT:-8507}
export STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Create directories
mkdir -p logs data backups

# Initialize databases
python3 -c "
import sqlite3
import os
from datetime import datetime

databases = ['mega_aggressive_trading.db', 'ultra_aggressive_trading.db', 'mainnet_optimization.db']

for db_name in databases:
    if not os.path.exists(db_name):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        if 'mega' in db_name:
            table_name = 'mega_trades'
        elif 'ultra' in db_name:
            table_name = 'ultra_trades'
        else:
            table_name = 'optimized_trades'
        
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                amount REAL NOT NULL,
                price REAL NOT NULL,
                profit_loss REAL NOT NULL,
                balance_after REAL NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f'✅ {db_name} initialized')

print('🎉 Databases ready!')
"

# Start main dashboard
echo "📊 Starting Unified Dashboard..."
streamlit run unified_real_dashboard.py --server.port=$PORT --server.address=0.0.0.0
"""
    
    with open('start_railway.sh', 'w') as f:
        f.write(start_script)
    
    os.chmod('start_railway.sh', 0o755)
    print("✅ start_railway.sh creato")

def create_env_example():
    """Crea file .env.example"""
    
    env_content = """# AurumBotX Environment Variables

# Trading Configuration
TRADING_MODE=testnet
BINANCE_API_KEY=your_binance_testnet_api_key
BINANCE_API_SECRET=your_binance_testnet_secret

# Dashboard Configuration
DASHBOARD_PORT=8507
AUTO_REFRESH=true

# System Configuration
LOG_LEVEL=INFO
DEBUG_MODE=false

# Railway Specific
PORT=8507
"""
    
    with open('.env.example', 'w') as f:
        f.write(env_content)
    
    print("✅ .env.example creato")

def create_gitignore():
    """Crea .gitignore ottimizzato"""
    
    gitignore_content = """# AurumBotX .gitignore

# Environment variables
.env
.env.local
.env.production

# Database files
*.db
*.sqlite
*.sqlite3

# Logs
logs/
*.log

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
aurumbotx_env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Backup files
backup/
backups/
*.backup
*.bak

# Temporary files
tmp/
temp/
*.tmp

# API Keys and secrets
config/config.json
secrets.json
credentials.json

# Data files
data/
*.csv
*.json.bak

# Streamlit
.streamlit/secrets.toml
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)
    
    print("✅ .gitignore aggiornato")

def create_readme_deploy():
    """Crea README per deploy"""
    
    readme_content = """# 🚀 AurumBotX - Deploy Gratuito

## 📋 Deploy su Railway (Gratuito)

### 🎯 Setup Rapido (5 minuti)

1. **Fork questo repository** su GitHub
2. **Vai su [Railway.app](https://railway.app)**
3. **Login con GitHub**
4. **New Project → Deploy from GitHub**
5. **Seleziona AurumBotX repository**
6. **Deploy automatico!**

### 🔗 Dopo il Deploy

- **Dashboard URL**: Disponibile nel Railway dashboard
- **Auto-deploy**: Ogni push su GitHub
- **Logs**: Visibili in Railway console
- **Uptime**: 99%+ garantito

### ⚙️ Configurazione

1. **Environment Variables** in Railway:
   ```
   BINANCE_API_KEY=your_testnet_key
   BINANCE_API_SECRET=your_testnet_secret
   TRADING_MODE=testnet
   ```

2. **Custom Domain** (opzionale):
   - Aggiungi dominio in Railway
   - Configura DNS
   - SSL automatico

### 📊 Caratteristiche Deploy

- ✅ **Gratuito**: $5 credito mensile
- ✅ **Auto-scaling**: Automatico
- ✅ **SSL**: Incluso
- ✅ **Monitoring**: Integrato
- ✅ **Logs**: Real-time
- ✅ **GitHub Integration**: Auto-deploy

### 🔄 Aggiornamenti

Ogni push su GitHub aggiorna automaticamente il deploy!

### 🆘 Supporto

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **GitHub Issues**: Per problemi specifici
- **Discord**: Community Railway

## 🎉 Il tuo AurumBotX sarà online 24/7!
"""
    
    with open('README_DEPLOY.md', 'w') as f:
        f.write(readme_content)
    
    print("✅ README_DEPLOY.md creato")

def main():
    """Funzione principale"""
    print("🚀 AurumBotX Railway Deploy Setup")
    print("=" * 50)
    
    # Crea tutti i file necessari
    create_railway_config()
    create_dockerfile()
    create_procfile()
    create_requirements_txt()
    create_railway_start_script()
    create_env_example()
    create_gitignore()
    create_readme_deploy()
    
    print("\\n✅ SETUP DEPLOY COMPLETATO!")
    print("=" * 50)
    print("🎯 PROSSIMI STEP:")
    print("1. 📦 Commit e push su GitHub")
    print("2. 🌐 Vai su railway.app")
    print("3. 🔗 Deploy from GitHub")
    print("4. ⚙️ Configura environment variables")
    print("5. 🚀 Dashboard online 24/7!")
    print("\\n💡 Costo: GRATUITO ($5 credito mensile)")
    print("🔗 URL: Generato automaticamente da Railway")

if __name__ == "__main__":
    main()

