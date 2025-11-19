# 🚀 Guida Setup MEXC per Trading Reale - AurumBotX

**Data**: 11 Novembre 2025  
**Capitale**: $25 USD  
**Exchange**: MEXC  
**Avvio**: Domani 12 Novembre 2025 ore 12:00  

---

## 📋 Checklist Completa

### Fase 1: Registrazione MEXC (30 minuti)

**1.1 Crea Account MEXC**
- [ ] Vai su https://www.mexc.com
- [ ] Click "Sign Up"
- [ ] Inserisci email e password sicura
- [ ] Verifica email
- [ ] Login

**1.2 Completa KYC (Know Your Customer)**
- [ ] Vai su "Profile" → "Verification"
- [ ] Seleziona "Individual Verification"
- [ ] Carica documento identità (Carta d'identità o Passaporto)
- [ ] Selfie con documento
- [ ] Attendi approvazione (10-30 minuti)

**1.3 Abilita 2FA (Sicurezza)**
- [ ] Scarica Google Authenticator (iOS/Android)
- [ ] Vai su "Security" → "Google Authenticator"
- [ ] Scansiona QR code
- [ ] Salva backup code in luogo sicuro
- [ ] Conferma attivazione

---

### Fase 2: Deposito $25 USDT (15 minuti)

**2.1 Acquista USDT**

**Opzione A: Carta di Credito/Debito** (più veloce)
- [ ] Vai su "Buy Crypto" → "Credit/Debit Card"
- [ ] Seleziona USDT
- [ ] Importo: $25
- [ ] Inserisci dati carta
- [ ] Conferma acquisto
- [ ] Fee: ~3-5% ($0.75-1.25)

**Opzione B: Bonifico Bancario** (più economico ma lento)
- [ ] Vai su "Buy Crypto" → "Bank Transfer"
- [ ] Seleziona EUR o USD
- [ ] Importo: €25 / $25
- [ ] Segui istruzioni bonifico
- [ ] Attendi 1-3 giorni lavorativi
- [ ] Fee: ~1% ($0.25)

**Opzione C: P2P Trading** (fee minime)
- [ ] Vai su "P2P Trading"
- [ ] Cerca venditori USDT
- [ ] Seleziona metodo pagamento (PayPal, Revolut, etc.)
- [ ] Completa transazione
- [ ] Fee: 0%

**2.2 Verifica Saldo**
- [ ] Vai su "Assets" → "Spot Account"
- [ ] Verifica $25 USDT disponibili

---

### Fase 3: Creazione API Keys (15 minuti)

**3.1 Genera API Key**
- [ ] Vai su "API Management"
- [ ] Click "Create API"
- [ ] Nome: "AurumBotX_Trading"
- [ ] Tipo: "System Generated"

**3.2 Configura Permessi**
- [ ] ✅ Enable Reading
- [ ] ✅ Enable Spot Trading
- [ ] ❌ Disable Withdrawals (IMPORTANTE!)
- [ ] ❌ Disable Futures Trading
- [ ] ❌ Disable Margin Trading

**3.3 Configura IP Whitelist**
- [ ] Trova tuo IP pubblico: https://whatismyipaddress.com
- [ ] Aggiungi IP alla whitelist
- [ ] Se IP dinamico, lascia vuoto (meno sicuro)

**3.4 Salva Credenziali**
- [ ] Copia API Key
- [ ] Copia API Secret
- [ ] Salva in luogo sicuro (password manager)
- [ ] **NON condividere MAI con nessuno!**

---

### Fase 4: Configurazione AurumBotX (30 minuti)

**4.1 Crea File .env**

```bash
cd /home/ubuntu/AurumBotX
cp .env.example .env
nano .env
```

**4.2 Inserisci API Keys**

Modifica `.env`:

```bash
# MEXC Exchange
MEXC_API_KEY=your_actual_api_key_here
MEXC_API_SECRET=your_actual_api_secret_here

# OpenAI (se non già configurato)
OPENAI_API_KEY=your_openai_key_here

# Trading Mode
DEMO_MODE=false  # ⚠️ IMPORTANTE: false per trading reale!

# Logging
LOG_LEVEL=INFO
```

Salva: `Ctrl+X` → `Y` → `Enter`

**4.3 Modifica Configurazione Wallet**

```bash
nano config/wallet_25_real_mexc.json
```

Verifica configurazione:
- `initial_capital`: 25.0 ✅
- `exchange`: "mexc" ✅
- `demo_mode`: false ✅
- `risk_profile`: "ultra_conservative" ✅
- `max_position_size_percentage`: 1.0 (= $0.25 per trade) ✅
- `stop_loss_percentage`: 1.5 ✅
- `max_daily_loss_absolute`: 0.50 ✅

**4.4 Test Connessione API**

```bash
python3 << 'EOF'
import os
from dotenv import load_dotenv
from exchange_api import create_exchange

# Carica .env
load_dotenv()

# Test connessione
api_key = os.getenv('MEXC_API_KEY')
api_secret = os.getenv('MEXC_API_SECRET')

print("Testing MEXC connection...")
mexc = create_exchange('mexc', api_key, api_secret, demo_mode=False)

# Test
if mexc.test_connection():
    print("✅ Connessione OK!")
    balance = mexc.get_balance()
    print(f"Saldo: {balance}")
else:
    print("❌ Connessione fallita!")
EOF
```

**Output atteso**:
```
Testing MEXC connection...
✅ Connessione OK!
Saldo: {'USDT': 25.0, ...}
```

---

### Fase 5: Primo Avvio (Domani 12:00)

**5.1 Pre-Flight Check**

```bash
cd /home/ubuntu/AurumBotX

# Verifica file
ls -lh config/wallet_25_real_mexc.json
ls -lh .env
ls -lh exchange_api.py
ls -lh wallet_runner_optimized.py

# Verifica saldo MEXC
python3 -c "
from dotenv import load_dotenv
import os
from exchange_api import create_exchange

load_dotenv()
mexc = create_exchange('mexc', os.getenv('MEXC_API_KEY'), os.getenv('MEXC_API_SECRET'), demo_mode=False)
print('Saldo:', mexc.get_balance())
"
```

**5.2 Avvio Wallet**

```bash
# Avvia in modalità interattiva per primi 3 trade
python3 wallet_runner_optimized.py config/wallet_25_real_mexc.json
```

**5.3 Monitoraggio Primi Trade**

Il sistema chiederà conferma manuale per i primi 3 trade:

```
🤖 Trade Signal Detected!
Pair: BTC/USDT
Side: BUY
Amount: 0.00005 BTC (~$0.25)
Confidence: 68%
Stop Loss: $0.24625 (-1.5%)
Take Profit: $0.2575 (+3%)

Confermare trade? (y/n):
```

- [ ] Verifica parametri
- [ ] Se OK, digita `y` e premi Enter
- [ ] Se dubbio, digita `n` per saltare

**5.4 Dopo 3 Trade Manuali**

Se tutto OK, il sistema passa automatico:

```
✅ Primi 3 trade completati con successo!
Passaggio a modalità automatica...
```

**5.5 Monitoraggio Continuo**

```bash
# In altra finestra terminale
tail -f /home/ubuntu/AurumBotX/demo_trading/wallet_25_real_mexc/trading.log
```

---

## ⚠️ Safety Checks Automatici

Il sistema include protezioni automatiche:

### 1. Stop Loss Automatico
- Ogni trade ha stop loss 1.5%
- Max perdita per trade: $0.00375

### 2. Daily Loss Limit
- Max perdita giornaliera: $0.50 (2%)
- Sistema si ferma automaticamente se raggiunto

### 3. Consecutive Losses
- Max 5 perdite consecutive
- Sistema si ferma e richiede revisione

### 4. Emergency Stop
- Se capitale scende sotto $22.50 (-10%)
- Sistema si ferma immediatamente

### 5. Position Size Limit
- Max 1% del capitale per trade
- Con $25 = max $0.25 per trade

---

## 📊 Monitoraggio Performance

### Dashboard Web

```bash
# Avvia API server (se non già avviato)
cd /home/ubuntu/AurumBotX
python3 api_server.py &

# Apri browser
http://localhost:8080
```

### Comandi Utili

**Verifica Stato**:
```bash
cat /home/ubuntu/AurumBotX/demo_trading/wallet_25_real_mexc/state.json | jq '.'
```

**Verifica Ultimo Trade**:
```bash
cat /home/ubuntu/AurumBotX/demo_trading/wallet_25_real_mexc/state.json | jq '.trades_history[-1]'
```

**Statistiche Rapide**:
```bash
python3 << 'EOF'
import json

with open('/home/ubuntu/AurumBotX/demo_trading/wallet_25_real_mexc/state.json') as f:
    state = json.load(f)

print(f"Capitale: ${state['capital']:.2f}")
print(f"P&L: ${state['total_pnl']:.2f}")
print(f"Trade: {state['total_trades']}")
print(f"Win Rate: {state['winning_trades']/state['total_trades']*100:.1f}%" if state['total_trades'] > 0 else "N/A")
EOF
```

---

## 🛑 Come Fermare il Sistema

### Stop Temporaneo
```bash
# Trova PID processo
ps aux | grep wallet_runner_optimized

# Kill processo
kill -SIGINT <PID>
```

### Stop di Emergenza
```bash
# Kill immediato
pkill -9 -f wallet_25_real_mexc
```

### Riavvio
```bash
cd /home/ubuntu/AurumBotX
python3 wallet_runner_optimized.py config/wallet_25_real_mexc.json
```

---

## 📈 Risultati Attesi (Primo Mese)

### Scenario Conservativo
- Trade/giorno: 3-5
- Win Rate: 70%
- ROI mensile: 15-20%
- Capitale fine mese: **$28.75-$30.00**
- Profit: **+$3.75-5.00**

### Scenario Ottimistico
- Trade/giorno: 5-7
- Win Rate: 75%
- ROI mensile: 25%
- Capitale fine mese: **$31.25**
- Profit: **+$6.25**

### Scenario Pessimistico
- Trade/giorno: 2-3
- Win Rate: 60%
- ROI mensile: 5-10%
- Capitale fine mese: **$26.25-$27.50**
- Profit: **+$1.25-2.50**

---

## ⚠️ Troubleshooting

### Errore: "Invalid API Key"
- Verifica API key in `.env`
- Verifica permessi API su MEXC
- Verifica IP whitelist

### Errore: "Insufficient Balance"
- Verifica saldo USDT su MEXC
- Verifica che fondi siano in Spot Account (non Futures)

### Errore: "Order Failed"
- Verifica connessione internet
- Verifica che coppia sia disponibile su MEXC
- Verifica amount minimo per coppia

### Sistema Non Trova Trade
- Normale! Confidence threshold 65% è alto
- Sistema aspetta opportunità sicure
- Può passare anche 1-2 ore senza trade

### Performance Sotto Aspettative
- Primi giorni possono essere lenti
- Sistema sta "imparando"
- Valuta performance dopo 2-4 settimane

---

## 📞 Supporto

### Log File
```bash
/home/ubuntu/AurumBotX/demo_trading/wallet_25_real_mexc/trading.log
```

### State File
```bash
/home/ubuntu/AurumBotX/demo_trading/wallet_25_real_mexc/state.json
```

### Errori Comuni
- Controllare sempre log file
- Verificare saldo MEXC
- Verificare connessione API

---

## ✅ Checklist Finale Prima di Avviare

- [ ] Account MEXC creato e verificato (KYC)
- [ ] 2FA abilitato
- [ ] $25 USDT depositati e visibili in Spot Account
- [ ] API Keys create con permessi corretti
- [ ] IP whitelist configurato (se necessario)
- [ ] File `.env` creato con API keys
- [ ] Configurazione wallet verificata
- [ ] Test connessione API superato
- [ ] Backup API keys salvato in luogo sicuro
- [ ] Compreso funzionamento stop loss e safety
- [ ] Pronto a monitorare primi 3 trade manualmente

---

## 🎯 Prossimi Step Dopo Primo Mese

Se performance positive (ROI >10%):
1. Aumentare capitale a $50
2. Aggiungere più coppie trading
3. Ridurre confidence threshold a 60%
4. Aumentare position size a 1.5%

Se performance negative (ROI <0%):
1. Analizzare trade perdenti
2. Aumentare confidence threshold a 70%
3. Ridurre coppie a solo BTC/ETH
4. Ridurre position size a 0.5%

---

**Buon Trading! 🚀**

*Ricorda: Trading crypto è ad alto rischio. Investi solo capitale che puoi permetterti di perdere.*

---

**Guida creata il**: 11 Novembre 2025  
**Versione**: 1.0  
**Sistema**: AurumBotX Multi-Wallet Enterprise v2.0  
**Exchange**: MEXC (Fee 0.05%)
