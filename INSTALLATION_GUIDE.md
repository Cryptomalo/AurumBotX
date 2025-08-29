# 🚀 AURUMBOTX - GUIDA INSTALLAZIONE COMPLETA

## 📋 INDICE
1. [Requisiti di Sistema](#requisiti-di-sistema)
2. [Installazione Rapida](#installazione-rapida)
3. [Installazione Avanzata](#installazione-avanzata)
4. [Configurazione](#configurazione)
5. [Primo Avvio](#primo-avvio)
6. [Troubleshooting](#troubleshooting)
7. [Aggiornamenti](#aggiornamenti)

---

## 💻 REQUISITI DI SISTEMA

### **🖥️ Requisiti Minimi**
```bash
Sistema Operativo: Ubuntu 20.04+ / CentOS 8+ / macOS 11+ / Windows 10+
CPU: 2 core, 2.0 GHz
RAM: 4 GB
Storage: 10 GB spazio libero
Network: Connessione internet stabile
Python: 3.9+
```

### **🚀 Requisiti Raccomandati**
```bash
Sistema Operativo: Ubuntu 22.04 LTS
CPU: 4+ core, 3.0+ GHz
RAM: 8+ GB
Storage: 50+ GB SSD
Network: Connessione internet ad alta velocità
Python: 3.11+
Database: PostgreSQL 15+ (opzionale, default SQLite)
```

### **☁️ Requisiti Cloud (Produzione)**
```bash
Provider: AWS / Google Cloud / Azure / DigitalOcean
Instance Type: t3.medium+ (AWS) / e2-standard-2+ (GCP)
CPU: 2+ vCPU
RAM: 4+ GB
Storage: 20+ GB SSD
Network: 1+ Gbps
Load Balancer: Raccomandato per alta disponibilità
```

---

## ⚡ INSTALLAZIONE RAPIDA

### **🐳 Docker (Raccomandato)**
```bash
# 1. Clona il repository
git clone https://github.com/YourUsername/AurumBotX.git
cd AurumBotX

# 2. Copia file configurazione
cp .env.example .env

# 3. Configura variabili ambiente (vedi sezione Configurazione)
nano .env

# 4. Avvia con Docker Compose
docker-compose up -d

# 5. Verifica installazione
docker-compose ps
curl http://localhost:8501/health
```

### **📦 Installazione Automatica (Linux/macOS)**
```bash
# 1. Download script installazione
curl -fsSL https://raw.githubusercontent.com/YourUsername/AurumBotX/main/install.sh -o install.sh

# 2. Rendi eseguibile
chmod +x install.sh

# 3. Esegui installazione
./install.sh

# 4. Segui le istruzioni interattive
# Lo script configurerà automaticamente:
# - Dipendenze Python
# - Database
# - Variabili ambiente
# - Servizi systemd
```

### **🪟 Installazione Windows**
```powershell
# 1. Installa Python 3.11+
# Download da: https://www.python.org/downloads/

# 2. Installa Git
# Download da: https://git-scm.com/download/win

# 3. Clona repository
git clone https://github.com/YourUsername/AurumBotX.git
cd AurumBotX

# 4. Installa dipendenze
pip install -r requirements.txt

# 5. Configura ambiente
copy .env.example .env
# Modifica .env con le tue configurazioni

# 6. Avvia applicazione
python start_trading.py
```

---

## 🔧 INSTALLAZIONE AVANZATA

### **🐍 Installazione Manuale Python**
```bash
# 1. Aggiorna sistema
sudo apt update && sudo apt upgrade -y

# 2. Installa dipendenze sistema
sudo apt install -y python3.11 python3.11-pip python3.11-venv \
    postgresql postgresql-contrib redis-server \
    build-essential libpq-dev git curl

# 3. Crea utente dedicato
sudo useradd -m -s /bin/bash aurumbotx
sudo usermod -aG sudo aurumbotx

# 4. Cambia utente
sudo su - aurumbotx

# 5. Clona repository
git clone https://github.com/YourUsername/AurumBotX.git
cd AurumBotX

# 6. Crea ambiente virtuale
python3.11 -m venv venv
source venv/bin/activate

# 7. Aggiorna pip
pip install --upgrade pip setuptools wheel

# 8. Installa dipendenze
pip install -r requirements.txt

# 9. Installa dipendenze opzionali
pip install -r requirements-dev.txt  # Per sviluppo
pip install -r requirements-prod.txt # Per produzione
```

### **🗄️ Setup Database PostgreSQL**
```bash
# 1. Installa PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# 2. Avvia servizio
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 3. Crea database e utente
sudo -u postgres psql << EOF
CREATE DATABASE aurumbotx;
CREATE USER aurumbotx_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE aurumbotx TO aurumbotx_user;
ALTER USER aurumbotx_user CREATEDB;
\q
EOF

# 4. Configura connessione
echo "DATABASE_URL=postgresql://aurumbotx_user:your_secure_password@localhost:5432/aurumbotx" >> .env
```

### **🔄 Setup Redis (Cache)**
```bash
# 1. Installa Redis
sudo apt install -y redis-server

# 2. Configura Redis
sudo nano /etc/redis/redis.conf
# Modifica:
# bind 127.0.0.1
# requirepass your_redis_password

# 3. Riavvia Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server

# 4. Testa connessione
redis-cli ping
# Dovrebbe rispondere: PONG

# 5. Configura in .env
echo "REDIS_URL=redis://:your_redis_password@localhost:6379/0" >> .env
```

### **🌐 Setup Nginx (Reverse Proxy)**
```bash
# 1. Installa Nginx
sudo apt install -y nginx

# 2. Crea configurazione
sudo nano /etc/nginx/sites-available/aurumbotx

# 3. Aggiungi configurazione:
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# 4. Abilita sito
sudo ln -s /etc/nginx/sites-available/aurumbotx /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### **🔒 Setup SSL con Let's Encrypt**
```bash
# 1. Installa Certbot
sudo apt install -y certbot python3-certbot-nginx

# 2. Ottieni certificato SSL
sudo certbot --nginx -d your-domain.com

# 3. Verifica auto-renewal
sudo certbot renew --dry-run

# 4. Configura auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

---

## ⚙️ CONFIGURAZIONE

### **🔑 File .env (Configurazione Principale)**
```bash
# === CONFIGURAZIONE GENERALE ===
APP_NAME=AurumBotX
APP_VERSION=1.0.0
ENVIRONMENT=production  # development, staging, production
DEBUG=false
LOG_LEVEL=INFO

# === DATABASE ===
DATABASE_URL=postgresql://aurumbotx_user:password@localhost:5432/aurumbotx
# Alternativa SQLite: sqlite:///./aurumbotx.db

# === REDIS CACHE ===
REDIS_URL=redis://:password@localhost:6379/0

# === BINANCE API ===
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
BINANCE_TESTNET=true  # false per produzione

# === SECURITY ===
SECRET_KEY=your_super_secret_key_here_min_32_chars
JWT_SECRET_KEY=your_jwt_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here

# === TELEGRAM BOT ===
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook

# === EMAIL ===
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TLS=true

# === MONITORING ===
SENTRY_DSN=your_sentry_dsn_here
PROMETHEUS_PORT=9090

# === TRADING CONFIGURATION ===
DEFAULT_CAPITAL=1000.0
DEFAULT_RISK_PERCENTAGE=2.0
DEFAULT_STRATEGY=swing_trading
MAX_CONCURRENT_TRADES=5
MIN_CONFIDENCE_THRESHOLD=0.6

# === API RATE LIMITS ===
API_RATE_LIMIT_PER_MINUTE=60
API_RATE_LIMIT_PER_HOUR=1000

# === DASHBOARD PORTS ===
ADMIN_DASHBOARD_PORT=8501
USER_DASHBOARD_PORT=8502
PERFORMANCE_DASHBOARD_PORT=8503
CONFIG_DASHBOARD_PORT=8504
MOBILE_APP_PORT=8505
```

### **🔧 Configurazione Avanzata**
```yaml
# config/trading.yaml
trading:
  strategies:
    swing_trading:
      enabled: true
      timeframe: "6m"
      profit_target: 0.008  # 0.8%
      stop_loss: 0.005      # 0.5%
      max_position_size: 0.1  # 10% del capitale
      
    scalping:
      enabled: true
      timeframe: "1m"
      profit_target: 0.003  # 0.3%
      stop_loss: 0.002      # 0.2%
      max_position_size: 0.05  # 5% del capitale
      
  risk_management:
    max_daily_loss: 0.05    # 5% del capitale
    max_drawdown: 0.15      # 15% del capitale
    position_sizing: "kelly" # kelly, fixed, volatility
    
  exchanges:
    binance:
      enabled: true
      testnet: true
      trading_pairs:
        - "BTCUSDT"
        - "ETHUSDT"
        - "ADAUSDT"
        
# config/ai.yaml
ai:
  models:
    ensemble:
      enabled: true
      models:
        - random_forest
        - gradient_boosting
        - xgboost
      weights: [0.4, 0.4, 0.2]
      
    features:
      technical_indicators: 26
      sentiment_analysis: true
      on_chain_metrics: false  # Richiede API aggiuntive
      
  training:
    retrain_frequency: "daily"
    min_data_points: 1000
    validation_split: 0.2
    
# config/monitoring.yaml
monitoring:
  logging:
    level: INFO
    format: json
    rotation: daily
    retention_days: 30
    
  metrics:
    enabled: true
    prometheus_port: 9090
    custom_metrics:
      - trade_execution_time
      - ai_prediction_accuracy
      - portfolio_performance
      
  alerts:
    email:
      enabled: true
      recipients:
        - admin@aurumbotx.com
    telegram:
      enabled: true
      chat_id: your_telegram_chat_id
    slack:
      enabled: false
      webhook_url: your_slack_webhook
```

---

## 🚀 PRIMO AVVIO

### **✅ Checklist Pre-Avvio**
```bash
# 1. Verifica configurazione
python -c "from utils.config import Config; print('✅ Configurazione OK')"

# 2. Testa connessione database
python -c "from utils.database_manager import DatabaseManager; db = DatabaseManager(); print('✅ Database OK')"

# 3. Testa API Binance
python -c "from utils.data_loader import CryptoDataLoader; loader = CryptoDataLoader(); print('✅ Binance API OK')"

# 4. Verifica modelli AI
python -c "from utils.ai_trading import AITrading; ai = AITrading(); print('✅ AI Models OK')"

# 5. Testa dashboard
streamlit run admin_dashboard.py --server.port 8501 &
curl http://localhost:8501/health
```

### **🎯 Avvio Servizi**
```bash
# === METODO 1: Script di Avvio Automatico ===
./start_all_services.sh

# === METODO 2: Avvio Manuale ===

# 1. Avvia trading bot
nohup python start_trading.py > logs/trading.log 2>&1 &

# 2. Avvia dashboard admin
nohup streamlit run admin_dashboard.py --server.port 8501 > logs/admin_dashboard.log 2>&1 &

# 3. Avvia dashboard utenti
nohup streamlit run premium_user_dashboard.py --server.port 8502 > logs/user_dashboard.log 2>&1 &

# 4. Avvia dashboard performance
nohup streamlit run visual_performance_dashboard.py --server.port 8503 > logs/performance.log 2>&1 &

# 5. Avvia mobile app
nohup streamlit run mobile_web_app.py --server.port 8505 > logs/mobile.log 2>&1 &

# 6. Verifica servizi attivi
ps aux | grep -E "(python|streamlit)" | grep -v grep
```

### **🔍 Verifica Installazione**
```bash
# 1. Controlla processi attivi
./check_services.sh

# 2. Testa endpoint API
curl -X GET http://localhost:8000/api/v1/health
curl -X GET http://localhost:8000/api/v1/status

# 3. Testa dashboard
curl -I http://localhost:8501
curl -I http://localhost:8502
curl -I http://localhost:8503

# 4. Verifica log
tail -f logs/trading.log
tail -f logs/admin_dashboard.log

# 5. Testa trading (modalità demo)
python test_trading_demo.py
```

---

## 🛠️ TROUBLESHOOTING

### **❌ Problemi Comuni**

#### **🔌 Errori di Connessione**
```bash
# Problema: Database connection failed
# Soluzione:
sudo systemctl status postgresql
sudo systemctl restart postgresql
psql -h localhost -U aurumbotx_user -d aurumbotx -c "SELECT 1;"

# Problema: Redis connection failed
# Soluzione:
sudo systemctl status redis-server
redis-cli ping
sudo systemctl restart redis-server

# Problema: Binance API error
# Soluzione:
# Verifica API keys in .env
# Controlla se testnet è abilitato
# Verifica connessione internet
curl -s https://api.binance.com/api/v3/ping
```

#### **🐍 Errori Python**
```bash
# Problema: ModuleNotFoundError
# Soluzione:
source venv/bin/activate
pip install -r requirements.txt

# Problema: Permission denied
# Soluzione:
sudo chown -R aurumbotx:aurumbotx /path/to/AurumBotX
chmod +x start_trading.py

# Problema: Port already in use
# Soluzione:
sudo lsof -i :8501
sudo kill -9 <PID>
```

#### **📊 Errori Dashboard**
```bash
# Problema: Streamlit not starting
# Soluzione:
pip install --upgrade streamlit
streamlit --version

# Problema: Dashboard not accessible
# Soluzione:
# Verifica firewall
sudo ufw allow 8501
sudo ufw allow 8502

# Verifica Nginx
sudo nginx -t
sudo systemctl restart nginx
```

### **🔧 Script Diagnostici**
```bash
# === diagnostic.py ===
#!/usr/bin/env python3
import sys
import subprocess
import requests
from utils.database_manager import DatabaseManager
from utils.data_loader import CryptoDataLoader

def check_system():
    """Verifica sistema"""
    print("🔍 Controllo Sistema...")
    
    # Python version
    print(f"Python: {sys.version}")
    
    # Disk space
    result = subprocess.run(['df', '-h', '.'], capture_output=True, text=True)
    print(f"Disk Space:\n{result.stdout}")
    
    # Memory
    result = subprocess.run(['free', '-h'], capture_output=True, text=True)
    print(f"Memory:\n{result.stdout}")

def check_services():
    """Verifica servizi"""
    print("🔍 Controllo Servizi...")
    
    services = [
        ("Database", "postgresql"),
        ("Redis", "redis-server"),
        ("Nginx", "nginx")
    ]
    
    for name, service in services:
        result = subprocess.run(['systemctl', 'is-active', service], 
                              capture_output=True, text=True)
        status = result.stdout.strip()
        print(f"{name}: {status}")

def check_api_endpoints():
    """Verifica endpoint API"""
    print("🔍 Controllo API Endpoints...")
    
    endpoints = [
        ("Admin Dashboard", "http://localhost:8501"),
        ("User Dashboard", "http://localhost:8502"),
        ("Performance Dashboard", "http://localhost:8503"),
        ("Binance API", "https://api.binance.com/api/v3/ping")
    ]
    
    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            print(f"{name}: ✅ {response.status_code}")
        except Exception as e:
            print(f"{name}: ❌ {str(e)}")

if __name__ == "__main__":
    check_system()
    check_services()
    check_api_endpoints()
```

### **📋 Log Analysis**
```bash
# === Analisi Log Automatica ===

# Errori recenti
grep -i error logs/*.log | tail -20

# Warning recenti
grep -i warning logs/*.log | tail -20

# Performance issues
grep -i "slow\|timeout\|failed" logs/*.log | tail -20

# Trading activity
grep -i "trade\|order\|signal" logs/trading.log | tail -20

# Dashboard access
grep -i "GET\|POST" logs/*dashboard.log | tail -20
```

---

## 🔄 AGGIORNAMENTI

### **📦 Aggiornamento Automatico**
```bash
# 1. Script aggiornamento
./update.sh

# Il script esegue:
# - Backup configurazione
# - Download nuova versione
# - Aggiornamento dipendenze
# - Migrazione database
# - Riavvio servizi
# - Verifica funzionamento
```

### **🔧 Aggiornamento Manuale**
```bash
# 1. Backup
./backup.sh

# 2. Stop servizi
./stop_all_services.sh

# 3. Aggiorna codice
git pull origin main

# 4. Aggiorna dipendenze
pip install -r requirements.txt --upgrade

# 5. Migrazione database
python manage.py migrate

# 6. Riavvia servizi
./start_all_services.sh

# 7. Verifica
./check_services.sh
```

### **🗄️ Migrazione Database**
```bash
# === Backup Database ===
pg_dump aurumbotx > backup_$(date +%Y%m%d_%H%M%S).sql

# === Migrazione ===
python manage.py makemigrations
python manage.py migrate

# === Verifica ===
python manage.py check
```

### **📊 Rollback**
```bash
# 1. Stop servizi
./stop_all_services.sh

# 2. Ripristina codice
git checkout <previous_version_tag>

# 3. Ripristina database
psql aurumbotx < backup_20250101_120000.sql

# 4. Ripristina configurazione
cp .env.backup .env

# 5. Riavvia servizi
./start_all_services.sh
```

---

## 🔧 SCRIPT UTILI

### **📜 start_all_services.sh**
```bash
#!/bin/bash
set -e

echo "🚀 Avvio AurumBotX Services..."

# Attiva ambiente virtuale
source venv/bin/activate

# Verifica configurazione
python -c "from utils.config import Config; print('✅ Config OK')"

# Avvia servizi in background
echo "📊 Avvio Trading Bot..."
nohup python start_trading.py > logs/trading.log 2>&1 &
echo $! > pids/trading.pid

echo "📊 Avvio Admin Dashboard..."
nohup streamlit run admin_dashboard.py --server.port 8501 > logs/admin.log 2>&1 &
echo $! > pids/admin.pid

echo "👥 Avvio User Dashboard..."
nohup streamlit run premium_user_dashboard.py --server.port 8502 > logs/user.log 2>&1 &
echo $! > pids/user.pid

echo "📈 Avvio Performance Dashboard..."
nohup streamlit run visual_performance_dashboard.py --server.port 8503 > logs/performance.log 2>&1 &
echo $! > pids/performance.pid

echo "📱 Avvio Mobile App..."
nohup streamlit run mobile_web_app.py --server.port 8505 > logs/mobile.log 2>&1 &
echo $! > pids/mobile.pid

sleep 5
echo "✅ Tutti i servizi avviati!"
./check_services.sh
```

### **📜 stop_all_services.sh**
```bash
#!/bin/bash

echo "🛑 Stop AurumBotX Services..."

# Stop servizi usando PID files
for service in trading admin user performance mobile; do
    if [ -f "pids/${service}.pid" ]; then
        pid=$(cat "pids/${service}.pid")
        if kill -0 $pid 2>/dev/null; then
            echo "🛑 Stopping ${service} (PID: $pid)..."
            kill $pid
            rm "pids/${service}.pid"
        fi
    fi
done

# Force kill se necessario
pkill -f "start_trading.py"
pkill -f "streamlit run"

echo "✅ Tutti i servizi fermati!"
```

### **📜 backup.sh**
```bash
#!/bin/bash

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "💾 Backup AurumBotX..."

# Backup database
if [ "$DATABASE_URL" != "" ]; then
    pg_dump aurumbotx > $BACKUP_DIR/database.sql
    echo "✅ Database backup: $BACKUP_DIR/database.sql"
fi

# Backup configurazione
cp .env $BACKUP_DIR/
cp -r config/ $BACKUP_DIR/
echo "✅ Config backup: $BACKUP_DIR/"

# Backup log importanti
cp -r logs/ $BACKUP_DIR/
echo "✅ Logs backup: $BACKUP_DIR/logs/"

# Backup modelli AI
if [ -d "models/" ]; then
    cp -r models/ $BACKUP_DIR/
    echo "✅ AI Models backup: $BACKUP_DIR/models/"
fi

# Crea archivio
tar -czf $BACKUP_DIR.tar.gz -C backups $(basename $BACKUP_DIR)
rm -rf $BACKUP_DIR

echo "✅ Backup completo: $BACKUP_DIR.tar.gz"
```

---

## 📞 SUPPORTO

### **🆘 Canali di Supporto**
- **📧 Email**: support@aurumbotx.com
- **💬 Telegram**: @AurumBotXSupport
- **📖 Documentation**: https://docs.aurumbotx.com
- **🐛 Bug Reports**: https://github.com/YourUsername/AurumBotX/issues
- **💡 Feature Requests**: https://github.com/YourUsername/AurumBotX/discussions

### **📚 Risorse Aggiuntive**
- **🎥 Video Tutorial**: https://youtube.com/AurumBotX
- **📖 Wiki**: https://github.com/YourUsername/AurumBotX/wiki
- **💬 Community**: https://discord.gg/aurumbotx
- **📊 Status Page**: https://status.aurumbotx.com

---

*© 2025 AurumBotX. Installation Guide v1.0*

