# 🚀 AurumBotX Mainnet Trading - Quick Start Guide

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
