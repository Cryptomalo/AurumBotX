# AurumBotX Runbook (Testnet-first)

## 0) Obiettivo
Runbook operativo per:
1. Avviare i servizi locali (API + dashboard).
2. Eseguire un system test riproducibile.
3. Preparare le API necessarie (testnet) senza esporre segreti.

> **Nota sicurezza**: non inserire mai chiavi reali in file versionati. Usa `.env` locale o variabili d’ambiente.

---

## 1) Prerequisiti
- Python 3.10+
- Dipendenze: `pip install -r requirements.txt`
- Streamlit (se vuoi la dashboard): `pip install streamlit`

---

## 2) Configurazione ambiente

### 2.1 Crea `.env` locale
Copia il template e inserisci le tue chiavi **localmente**:

```bash
cp .env.example .env
```

Variabili minime consigliate (testnet):
```
BINANCE_API_KEY=your_binance_testnet_api_key
BINANCE_SECRET_KEY=your_binance_testnet_secret
BINANCE_TESTNET=true

OPENROUTER_API_KEY=your_openrouter_key
```

### 2.2 Variabili opzionali
```
HYPERLIQUID_API_KEY=your_hyperliquid_key
HYPERLIQUID_SECRET_KEY=your_hyperliquid_secret
```

Per Telegram:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_AUTHORIZED_USERS=12345678,87654321
```

---

## 3) Avvio servizi locali

### 3.1 Avvio rapido (API + Dashboard)
```bash
./start_services.sh
```

Log:
- API: `logs/api_server.log`
- Dashboard: `logs/dashboard_8501.log`

### 3.2 Avvio API server manuale
```bash
python -m src.api.api_server_usdt
```

Default: `http://localhost:5678/api/status`

---

## 4) Esecuzione test completo

### 4.1 Test con servizi locali “lightweight”
```bash
SPAWN_LOCAL_SERVICES=true DASHBOARD_URLS="Main Dashboard|http://localhost:8501" \
python test_system_complete.py
```

### 4.2 Test con servizi reali già avviati
```bash
DASHBOARD_URLS="Main Dashboard|http://localhost:8501" \
API_BASE_URL="http://localhost:5678" \
python test_system_complete.py
```

Output atteso:
- Report `SYSTEM_TEST_REPORT_*.json` (ignorado da git).

---

## 5) Paper / Testnet trading

1. Assicurati che `BINANCE_TESTNET=true`.
2. Avvia il bot:
```bash
python start_trading.py --testnet
```

---

## 6) Troubleshooting rapido

### API server non risponde (porta 5678)
- Verifica processi:
```bash
ps -ef | rg -v rg | rg "api_server_usdt"
```
- Avvia manualmente:
```bash
python -m src.api.api_server_usdt
```

### Dashboard offline (porta 8501)
- Verifica processi:
```bash
ps -ef | rg -v rg | rg "streamlit"
```
- Avvia manualmente:
```bash
streamlit run src/dashboards/modern_unified_dashboard.py \
  --server.address 0.0.0.0 --server.port 8501 --server.headless true
```

### Errori Flask non installato
`src/api/api_server_usdt.py` usa un fallback HTTP. Se vuoi Flask completo:
```bash
pip install flask
```

---

## 7) Checklist pre-produzione (sintetica)
- [ ] API keys configurate e valide.
- [ ] Test completo 9/9 OK.
- [ ] Monitoraggio attivo (dashboard + API).
- [ ] Risk management e limiti verificati.
