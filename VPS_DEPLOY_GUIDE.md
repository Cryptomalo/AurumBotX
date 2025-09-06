# 🚀 AurumBotX VPS Deploy Guide

## ⚡ Quick Deploy (5 minuti)

### 1. 📦 Preparazione VPS
```bash
# Ubuntu 20.04+ raccomandato
sudo apt update && sudo apt upgrade -y
```

### 2. 🔧 Installazione Automatica
```bash
curl -fsSL https://raw.githubusercontent.com/Cryptomalo/AurumBotX/main/vps_install.sh | bash
```

### 3. ⚙️ Configurazione
```bash
cd AurumBotX
nano .env  # Configura credenziali Binance
```

### 4. 🚀 Avvio Sistema
```bash
docker-compose up -d
```

## 🌐 Accesso Dashboard

- **URL**: `http://YOUR_VPS_IP:8507`
- **Login**: admin / admin123
- **Mobile**: Responsive design

## 🎛️ Controlli Sistema

### Start/Stop via Dashboard
- ✅ Tutti i bot controllabili da interfaccia web
- 📊 Monitoraggio real-time
- 🔄 Auto-restart configurato

### Comandi Manuali
```bash
# Status
docker-compose ps

# Logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down
```

## 🔧 Configurazione Avanzata

### 1. 🔐 Sicurezza
```bash
# Firewall
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 8507
sudo ufw enable

# SSL (opzionale)
sudo apt install certbot
sudo certbot --nginx
```

### 2. 📊 Monitoring
```bash
# Systemd service
sudo cp aurumbotx.service /etc/systemd/system/
sudo systemctl enable aurumbotx
sudo systemctl start aurumbotx
```

### 3. 🔄 Auto-Update
```bash
# Cron job per aggiornamenti
echo "0 2 * * * cd /home/ubuntu/AurumBotX && git pull && docker-compose up -d --build" | crontab -
```

## 🌍 Provider VPS Raccomandati

### 💰 Economici
- **DigitalOcean**: $5/mese (1GB RAM)
- **Linode**: $5/mese (1GB RAM)
- **Vultr**: $3.50/mese (512MB RAM)

### 🚀 Performance
- **AWS EC2**: t3.micro (1GB RAM)
- **Google Cloud**: e2-micro (1GB RAM)
- **Azure**: B1s (1GB RAM)

## 📋 Requisiti Minimi

- **CPU**: 1 vCore
- **RAM**: 1GB (2GB raccomandato)
- **Storage**: 10GB SSD
- **Network**: 1TB transfer
- **OS**: Ubuntu 20.04+

## 🆘 Troubleshooting

### ❌ Dashboard non accessibile
```bash
# Controlla servizio
docker-compose ps
docker-compose logs aurumbotx

# Restart
docker-compose restart aurumbotx
```

### 🔑 Problemi credenziali
```bash
# Verifica .env
cat .env

# Test connessione Binance
python3 -c "from binance.client import Client; print('OK')"
```

### 📊 Performance lente
```bash
# Monitoring risorse
htop
df -h
free -h

# Ottimizzazione
docker system prune -f
```

## 🎯 Team Access

### 👥 Multi-User Setup
1. Ogni membro team clona repository
2. Configura VPS IP in dashboard
3. Accesso condiviso via URL pubblico
4. Controlli granulari per ruoli

### 🔐 Sicurezza Team
- Login centralizzato
- Audit trail completo
- Backup automatici
- Rollback rapido

## 🏆 Risultati Attesi

- **⚡ Uptime**: 99.9%
- **📊 Latency**: <100ms
- **🔄 Auto-restart**: Configurato
- **📱 Mobile**: Completamente responsive
- **👥 Team**: Accesso simultaneo

**🎉 Sistema pronto per trading 24/7 con accesso team completo!**
