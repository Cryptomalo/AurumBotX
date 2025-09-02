# 🚀 AurumBotX - Deploy Guide

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
- **Login**: admin / admin123
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
ADMIN_PASSWORD=admin123
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
