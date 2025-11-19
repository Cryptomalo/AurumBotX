# Whale Alert API Setup Guide

## 🐋 Ottenere API Key Gratuita

### Step 1: Registrazione

1. Vai su https://whale-alert.io
2. Click "API" nel menu
3. Click "Get API Key"
4. Compila form registrazione:
   - Email
   - Nome progetto: "AurumBotX MVP"
   - Uso: "Personal trading bot development"

### Step 2: Verifica Email

1. Controlla email di conferma
2. Click link verifica
3. Login al dashboard

### Step 3: Ottieni API Key

1. Dashboard → "API Keys"
2. Copia la tua API key
3. **Salva in luogo sicuro!**

---

## 📋 Piano Gratuito vs Paid

### Free Tier (Sufficiente per MVP!)

- ✅ 100 requests/mese
- ✅ Dati real-time
- ✅ Tutte le blockchain
- ✅ Webhook support
- ⚠️ Rate limit: 1 req/min

**Per MVP**: Sufficiente!
- 1 request ogni 6h = 4 req/giorno
- 120 req/mese < 100 limit ❌

**Soluzione**: Request ogni 12h invece di 6h
- 2 req/giorno = 60 req/mese ✅

### Pro Plan ($49/mese)

- 10,000 requests/mese
- No rate limit
- Historical data
- Priority support

**Per Production**: Consigliato dopo MVP validato

---

## 🔧 Configurazione in AurumBotX

### Opzione 1: Environment Variable

```bash
# Aggiungi a .env
echo "WHALE_ALERT_API_KEY=tua_api_key_qui" >> /home/ubuntu/AurumBotX/.env
```

### Opzione 2: Config File

```bash
# Crea config
cat > /home/ubuntu/AurumBotX/mvp_v4/whale_config.json << 'EOF'
{
  "whale_alert_api_key": "tua_api_key_qui",
  "min_value_usd": 1000000,
  "buffer_hours": 12
}
EOF
```

### Opzione 3: Direct in Code

```python
from whale_flow_tracker import WhaleFlowTracker

tracker = WhaleFlowTracker(api_key="tua_api_key_qui")
```

---

## ✅ Test Connessione

```bash
cd /home/ubuntu/AurumBotX/mvp_v4/modules

# Test con tua API key
python3 << 'EOF'
from whale_flow_tracker import WhaleFlowTracker

tracker = WhaleFlowTracker(api_key="TUA_API_KEY_QUI")
data = tracker.get_whale_data("bitcoin")

if data['whale_activity']['transactions_count'] > 0:
    print("✅ API Key funzionante!")
else:
    print("⚠️  Nessuna transazione trovata (normale se mercato calmo)")
EOF
```

---

## 🔄 Modalità Sviluppo (Senza API Key)

Per sviluppare senza API key reale, usa il **simulatore**:

```python
from whale_data_simulator import WhaleFlowTrackerWithSimulator

# Usa dati simulati
tracker = WhaleFlowTrackerWithSimulator(
    use_simulator=True,
    scenario="bullish"  # o "bearish", "neutral", etc.
)

data = tracker.get_whale_data("bitcoin")
```

**Scenari disponibili**:
- `strong_bullish`: Net flow +$600M+
- `bullish`: Net flow +$400-600M
- `neutral`: Net flow ±$100M
- `bearish`: Net flow -$400-600M
- `strong_bearish`: Net flow -$600M+

---

## 📊 Rate Limiting Best Practices

### Free Tier (1 req/min)

```python
import time

tracker = WhaleFlowTracker(api_key="your_key")

# Request ogni 12h per stare sotto 100/mese
while True:
    data = tracker.get_whale_data("bitcoin")
    # ... process data ...
    
    time.sleep(12 * 3600)  # Wait 12 hours
```

### Pro Plan (No limit)

```python
# Request ogni 6h come progettato
while True:
    data = tracker.get_whale_data("bitcoin")
    # ... process data ...
    
    time.sleep(6 * 3600)  # Wait 6 hours
```

---

## 🎯 Prossimi Passi

1. ✅ Ottieni API key gratuita
2. ✅ Configura in .env
3. ✅ Testa connessione
4. ✅ Se funziona → Procedi con MVP
5. ✅ Se non funziona → Usa simulatore per ora

---

## ❓ Troubleshooting

### Error 401 Unauthorized

- ✅ Verifica API key corretta
- ✅ Verifica no spazi extra
- ✅ Verifica email confermata

### Error 429 Too Many Requests

- ✅ Hai superato rate limit (1/min)
- ✅ Aspetta 1 minuto e riprova
- ✅ Riduci frequenza requests

### No Transactions Found

- ✅ Normale se mercato calmo
- ✅ Prova con timeframe più lungo (12-24h)
- ✅ Prova con min_value più basso ($500k)

---

**Guida completata!** 🐋✅
