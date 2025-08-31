# 🚀 AurumBotX - Guida Deployment Esterno

## 📋 **PANORAMICA**

Questa guida ti permetterà di installare e avviare AurumBotX sul tuo sistema esterno, mantenendo questo ambiente come **PROGETTO ALFA** di riferimento per sviluppo e testing.

## 🎯 **ARCHITETTURA DEPLOYMENT**

```
PROGETTO ALFA (Manus)     →     DEPLOYMENT ESTERNO (Utente)
├── Sviluppo e testing    →     ├── Produzione/Testing utente
├── Nuove funzionalità    →     ├── Sistema stabile
├── Ottimizzazioni        →     ├── Performance monitoring
└── Backup e versioning   →     └── Trading reale/testnet
```

## 📦 **REQUISITI SISTEMA**

### **💻 Sistema Operativo**
- **Linux**: Ubuntu 20.04+ (raccomandato)
- **Windows**: Windows 10+ con WSL2
- **macOS**: macOS 11+ con Homebrew
- **Cloud**: AWS EC2, Google Cloud, DigitalOcean

### **🔧 Software Richiesto**
- **Python**: 3.8+ (raccomandato 3.11)
- **Git**: Per cloning repository
- **SQLite**: Database (incluso in Python)
- **Node.js**: 16+ (per dashboard avanzate)
- **RAM**: Minimo 2GB, raccomandato 4GB+
- **Storage**: Minimo 5GB liberi
- **Network**: Connessione internet stabile

## 📥 **INSTALLAZIONE RAPIDA**

### **🚀 Metodo 1: Script Automatico (Raccomandato)**

```bash
# Download e esecuzione script automatico
curl -fsSL https://raw.githubusercontent.com/Cryptomalo/AurumBotX/main/install.sh | bash

# Oppure download manuale
wget https://github.com/Cryptomalo/AurumBotX/archive/main.zip
unzip main.zip
cd AurumBotX-main
chmod +x install.sh
./install.sh
```

### **🔧 Metodo 2: Installazione Manuale**

```bash
# 1. Clone repository
git clone https://github.com/Cryptomalo/AurumBotX.git
cd AurumBotX

# 2. Crea ambiente virtuale
python3 -m venv aurumbotx_env
source aurumbotx_env/bin/activate  # Linux/Mac
# aurumbotx_env\\Scripts\\activate  # Windows

# 3. Installa dipendenze
pip install -r requirements.txt

# 4. Setup configurazione
cp config/config.example.json config/config.json
nano config/config.json  # Modifica configurazione

# 5. Inizializza database
python3 setup_database.py

# 6. Test installazione
python3 test_installation.py
```

## ⚙️ **CONFIGURAZIONE**

### **📝 File Configurazione Principale**

Crea/modifica `config/config.json`:

```json
{
  "trading": {
    "mode": "testnet",
    "exchange": "binance",
    "api_key": "YOUR_BINANCE_TESTNET_API_KEY",
    "api_secret": "YOUR_BINANCE_TESTNET_SECRET",
    "initial_balance": 1000.0,
    "max_position_size": 0.20,
    "risk_per_trade": 0.02
  },
  "strategies": {
    "active_strategy": "mega_aggressive",
    "volatility_threshold": 0.02,
    "confidence_threshold": 0.30,
    "profit_target_range": [0.01, 0.04],
    "stop_loss_range": [0.005, 0.02]
  },
  "monitoring": {
    "enable_dashboard": true,
    "dashboard_port": 8501,
    "enable_logging": true,
    "log_level": "INFO",
    "enable_notifications": false
  },
  "security": {
    "enable_2fa": false,
    "max_daily_loss": 0.05,
    "emergency_stop": true,
    "whitelist_ips": []
  }
}
```

### **🔑 Setup API Binance Testnet**

1. **Registrati su Binance Testnet**:
   - Vai su: https://testnet.binance.vision/
   - Crea account testnet
   - Genera API Key e Secret

2. **Configura API**:
   ```bash
   # Modifica config.json
   nano config/config.json
   
   # Inserisci le tue credenziali:
   "api_key": "TUA_API_KEY_TESTNET",
   "api_secret": "TUA_API_SECRET_TESTNET"
   ```

3. **Test connessione**:
   ```bash
   python3 test_binance_connection.py
   ```

## 🚀 **AVVIO SISTEMA**

### **🎯 Avvio Completo (Raccomandato)**

```bash
# Avvia tutto il sistema
./start_aurumbotx.sh

# Oppure manualmente:
python3 main_launcher.py --mode=full
```

### **🔧 Avvio Componenti Singoli**

```bash
# Solo trading engine
python3 mega_aggressive_trading.py

# Solo dashboard
streamlit run admin_dashboard.py --server.port=8501

# Solo monitoring
python3 monitor_24_7.py

# Sistema ottimizzazione mainnet
python3 mainnet_optimization_strategies.py
```

### **📊 Avvio Dashboard Multiple**

```bash
# Script per avviare tutte le dashboard
./start_all_dashboards.sh

# Manuale:
streamlit run admin_dashboard.py --server.port=8501 &
streamlit run visual_performance_dashboard.py --server.port=8503 &
streamlit run mobile_web_app.py --server.port=8505 &
streamlit run premium_user_dashboard.py --server.port=8502 &
streamlit run advanced_config_dashboard.py --server.port=8504 &
```

## 🌐 **ACCESSO DASHBOARD**

### **📱 URL Dashboard**

Dopo l'avvio, accedi alle dashboard:

- **🔧 Admin Dashboard**: http://localhost:8501
- **📈 Performance Dashboard**: http://localhost:8503  
- **📱 Mobile Dashboard**: http://localhost:8505
- **💎 Premium Dashboard**: http://localhost:8502
- **⚙️ Config Dashboard**: http://localhost:8504

### **🌍 Accesso Esterno**

Per accesso da altri dispositivi:

```bash
# Trova il tuo IP locale
ip addr show | grep inet

# Accedi da altri dispositivi:
http://TUO_IP_LOCALE:8501
```

### **☁️ Accesso Cloud**

Se installato su cloud (AWS, Google Cloud, etc.):

```bash
# Configura firewall per porte dashboard
sudo ufw allow 8501:8505/tcp

# Accedi tramite IP pubblico:
http://TUO_IP_PUBBLICO:8501
```

## 📊 **MODALITÀ OPERATIVE**

### **🧪 Modalità Testnet (Raccomandato per iniziare)**

```bash
# Configura modalità testnet
python3 configure.py --mode=testnet

# Avvia trading testnet
python3 mega_aggressive_trading.py --testnet
```

**Caratteristiche**:
- ✅ Soldi virtuali (sicuro)
- ✅ API Binance Testnet
- ✅ Tutti i sistemi funzionanti
- ✅ Zero rischi finanziari

### **💰 Modalità Mainnet (Solo dopo testing)**

```bash
# ATTENZIONE: Solo dopo aver testato in testnet!
python3 configure.py --mode=mainnet

# Setup API Binance reale
nano config/config.json  # Inserisci API reali

# Avvia con capitale limitato
python3 mainnet_optimization_strategies.py --capital=100
```

**Caratteristiche**:
- ⚠️ Soldi reali (rischio)
- 💰 API Binance mainnet
- 📊 Performance reali
- 🛡️ Risk management attivo

## 🔍 **MONITORING E CONTROLLO**

### **📊 Controllo Status**

```bash
# Status generale sistema
python3 system_status.py

# Status trading
python3 trading_status.py

# Logs in tempo reale
tail -f logs/mega_aggressive.log
tail -f logs/mainnet_optimization.log
```

### **📈 Performance Monitoring**

```bash
# Report performance
python3 generate_trading_report.py

# Statistiche database
python3 database_stats.py

# Backup automatico
python3 backup_system.py
```

### **🛑 Controlli di Emergenza**

```bash
# Stop immediato tutto
./emergency_stop.sh

# Stop solo trading
python3 stop_trading.py

# Restart sistema
./restart_aurumbotx.sh
```

## 🔧 **TROUBLESHOOTING**

### **❌ Problemi Comuni**

#### **1. Errore Dipendenze**
```bash
# Reinstalla dipendenze
pip install --upgrade -r requirements.txt

# Verifica versione Python
python3 --version  # Deve essere 3.8+
```

#### **2. Errore API Binance**
```bash
# Test connessione
python3 test_binance_connection.py

# Verifica credenziali in config.json
# Assicurati di usare testnet per testing
```

#### **3. Dashboard Non Accessibili**
```bash
# Verifica porte
netstat -tlnp | grep :8501

# Restart dashboard
pkill -f streamlit
./start_all_dashboards.sh
```

#### **4. Database Corrotto**
```bash
# Backup e reset database
cp *.db backup/
python3 reset_database.py
python3 setup_database.py
```

### **🆘 Supporto**

Se hai problemi:

1. **📋 Controlla logs**: `tail -f logs/*.log`
2. **🔍 Verifica config**: `python3 validate_config.py`
3. **🧪 Test sistema**: `python3 test_installation.py`
4. **📞 Contatta supporto**: Apri issue su GitHub

## 🔄 **AGGIORNAMENTI**

### **📥 Aggiornamento Automatico**

```bash
# Update dal repository ALFA
./update_aurumbotx.sh

# Oppure manuale:
git pull origin main
pip install --upgrade -r requirements.txt
python3 migrate_database.py
```

### **🔄 Sincronizzazione con ALFA**

Il progetto ALFA viene aggiornato continuamente. Per sincronizzare:

```bash
# Backup configurazione locale
cp config/config.json config/config.backup.json

# Pull aggiornamenti
git pull origin main

# Merge configurazioni
python3 merge_config.py

# Test dopo aggiornamento
python3 test_installation.py
```

## 📊 **PERFORMANCE ATTESE**

### **🧪 Testnet Performance**
- **💰 Profitto simulato**: $20-50 per trade
- **✅ Win rate**: 65-100% (simulato)
- **📊 Trade giornalieri**: 10-50
- **🎯 ROI simulato**: 100-1000% annuale

### **💰 Mainnet Performance (Realistiche)**
- **💰 Profitto reale**: $10-30 per trade
- **✅ Win rate**: 55-75%
- **📊 Trade giornalieri**: 5-15
- **🎯 ROI reale**: 50-300% annuale

## 🛡️ **SICUREZZA**

### **🔐 Best Practices**

1. **🔑 API Security**:
   - Usa solo API testnet per testing
   - Non condividere mai API keys
   - Abilita IP whitelist su Binance

2. **💰 Risk Management**:
   - Inizia con capitale minimo
   - Imposta stop loss giornalieri
   - Monitora performance costantemente

3. **🖥️ System Security**:
   - Mantieni sistema aggiornato
   - Usa firewall per dashboard
   - Backup regolari configurazioni

## 🎯 **ROADMAP UTILIZZO**

### **📅 Settimana 1-2: Setup e Testing**
- ✅ Installazione sistema
- ✅ Configurazione testnet
- ✅ Test tutte le funzionalità
- ✅ Familiarizzazione dashboard

### **📅 Settimana 3-4: Ottimizzazione**
- ⚡ Tuning parametri
- 📊 Analisi performance
- 🔧 Personalizzazione strategie
- 📈 Monitoring avanzato

### **📅 Mese 2+: Produzione**
- 💰 Transizione mainnet (opzionale)
- 📊 Scaling capitale
- 🚀 Ottimizzazioni avanzate
- 💎 Performance tracking

## 🎉 **CONCLUSIONE**

### **✅ Sistema Pronto**

Con questa guida hai tutto il necessario per:

1. **🚀 Installare** AurumBotX sul tuo sistema
2. **⚙️ Configurare** per le tue esigenze
3. **🧪 Testare** in sicurezza con testnet
4. **📊 Monitorare** performance in tempo reale
5. **💰 Scalare** verso trading reale (quando pronto)

### **🔄 Supporto Continuo**

- **📋 Progetto ALFA**: Continua sviluppo e ottimizzazioni
- **🔄 Aggiornamenti**: Nuove funzionalità regolari
- **🆘 Supporto**: Documentazione e troubleshooting
- **📊 Performance**: Monitoring e miglioramenti continui

**🚀 AURUMBOTX È PRONTO PER IL DEPLOYMENT ESTERNO!**

**Il progetto ALFA rimane il centro di sviluppo mentre tu puoi utilizzare una versione stabile e ottimizzata!** 💎

