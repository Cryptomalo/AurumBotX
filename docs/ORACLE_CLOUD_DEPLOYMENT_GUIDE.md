# 🚀 AurumBotX - Guida Deployment Oracle Cloud Always Free

## Obiettivo

Deployare AurumBotX su Oracle Cloud Always Free per avere un sistema di trading 24/7 completamente gratuito con Hyperliquid Testnet.

---

## 📋 Prerequisiti

### Account e Chiavi Necessarie

1. **Account Oracle Cloud** (gratuito permanente)
2. **Wallet Hyperliquid Testnet** (MetaMask)
3. **API Key OpenAI** (per AI analysis)

### Cosa Ti Serve

- 💳 Carta di credito (solo per verifica, nessun addebito)
- 📧 Email valida
- ⏱️ 60-90 minuti di tempo

---

## 🎯 FASE 1: Registrazione Oracle Cloud (15 minuti)

### Step 1.1: Crea Account

1. Vai su: https://signup.oraclecloud.com/
2. Clicca **"Start for free"**
3. Compila il form:
   - **Email**: La tua email
   - **Country**: Italy
   - **Account Name**: Scegli un nome unico (es: `aurumbotx-trading`)

### Step 1.2: Verifica Email

1. Controlla la tua email
2. Clicca sul link di verifica
3. Completa la registrazione

### Step 1.3: Informazioni Account

1. **Account Type**: Individual
2. **Home Region**: Europe (Frankfurt) o Europe (Amsterdam)
   - ⚠️ **IMPORTANTE**: La regione NON può essere cambiata dopo!
3. Inserisci informazioni personali

### Step 1.4: Verifica Pagamento

1. Inserisci carta di credito
2. Verrà fatto un pre-addebito di €1-2 (rimborsato subito)
3. ✅ Nessun costo se usi solo Always Free resources

### Step 1.5: Attendi Approvazione

- Tempo: 5-30 minuti (di solito immediato)
- Riceverai email di conferma
- Accedi alla console: https://cloud.oracle.com/

---

## 🖥️ FASE 2: Creazione VM Always Free (20 minuti)

### Step 2.1: Accedi alla Console

1. Vai su: https://cloud.oracle.com/
2. Login con le tue credenziali
3. Verifica di essere nella **Home Region**

### Step 2.2: Crea Compute Instance

1. Nel menu hamburger (☰) → **Compute** → **Instances**
2. Clicca **"Create Instance"**

### Step 2.3: Configurazione Instance

**Nome**:
```
aurumbotx-trading-bot
```

**Placement**:
- **Availability Domain**: Scegli uno disponibile
- **Fault Domain**: Lascia default

**Image and Shape**:
1. Clicca **"Change Image"**
   - Seleziona: **Ubuntu 22.04**
   - Clicca **"Select Image"**

2. Clicca **"Change Shape"**
   - **Shape Series**: Specialty and Previous Generation
   - **Shape Name**: **VM.Standard.E2.1.Micro**
   - ✅ Verifica che mostri **"Always Free-eligible"**
   - Clicca **"Select Shape"**

**Networking**:
- **VCN**: Create new VCN (default)
- **Subnet**: Create new public subnet (default)
- ✅ **Assign a public IPv4 address**: CHECKED

**Add SSH Keys**:
- Seleziona **"Generate a key pair for me"**
- Clicca **"Save Private Key"** → Salva `ssh-key-XXXX.key`
- Clicca **"Save Public Key"** → Salva `ssh-key-XXXX.key.pub`
- ⚠️ **IMPORTANTE**: Conserva questi file al sicuro!

**Boot Volume**:
- **Boot Volume Size**: 47 GB (default)
- ✅ Always Free eligible

### Step 2.4: Crea Instance

1. Clicca **"Create"** in basso
2. Attendi 2-3 minuti (status: Provisioning → Running)
3. ✅ Quando vedi **"Running"** (verde), la VM è pronta!

### Step 2.5: Nota l'IP Pubblico

1. Nella pagina dell'instance, trova **"Public IP Address"**
2. Copia l'IP (es: `129.159.XXX.XXX`)
3. 📝 Salvalo, ti servirà per SSH

---

## 🔐 FASE 3: Connessione SSH (10 minuti)

### Step 3.1: Prepara SSH Key (Windows)

Se usi Windows:

1. Apri PowerShell
2. Converti la chiave:
```powershell
# Sposta la chiave nella cartella .ssh
mkdir $HOME\.ssh -Force
move Downloads\ssh-key-*.key $HOME\.ssh\oracle_key.key

# Imposta permessi (solo tu puoi leggere)
icacls $HOME\.ssh\oracle_key.key /inheritance:r
icacls $HOME\.ssh\oracle_key.key /grant:r "$($env:USERNAME):(R)"
```

### Step 3.1: Prepara SSH Key (Mac/Linux)

```bash
# Sposta la chiave nella cartella .ssh
mkdir -p ~/.ssh
mv ~/Downloads/ssh-key-*.key ~/.ssh/oracle_key.key

# Imposta permessi corretti
chmod 600 ~/.ssh/oracle_key.key
```

### Step 3.2: Connettiti via SSH

```bash
ssh -i ~/.ssh/oracle_key.key ubuntu@YOUR_VM_IP
```

Sostituisci `YOUR_VM_IP` con l'IP pubblico copiato prima.

**Esempio**:
```bash
ssh -i ~/.ssh/oracle_key.key ubuntu@129.159.123.45
```

### Step 3.3: Prima Connessione

1. Ti chiederà: `Are you sure you want to continue connecting?`
2. Digita: `yes` e premi Enter
3. ✅ Sei dentro! Dovresti vedere:

```
Welcome to Ubuntu 22.04.3 LTS
ubuntu@aurumbotx-trading-bot:~$
```

---

## 📦 FASE 4: Setup Ambiente (20 minuti)

### Step 4.1: Download Script Setup

Sulla VM Oracle, esegui:

```bash
# Download repository
git clone https://github.com/Rexon-Pambujya/AurumBotX.git
cd AurumBotX

# Rendi eseguibile lo script
chmod +x scripts/setup_oracle_cloud.sh

# Esegui setup
./scripts/setup_oracle_cloud.sh
```

Lo script installerà:
- Python 3.11
- Hyperliquid SDK
- OpenAI SDK
- Systemd service e timer
- Tutte le dipendenze

⏱️ Tempo: ~10-15 minuti

### Step 4.2: Configura Chiavi API

Dopo il setup, edita il file `.env`:

```bash
cd /home/ubuntu/AurumBotX
nano .env
```

Inserisci le tue chiavi:

```env
# Hyperliquid Configuration
HYPERLIQUID_TESTNET=true
HYPERLIQUID_ACCOUNT_ADDRESS=0xYOUR_WALLET_ADDRESS
HYPERLIQUID_SECRET_KEY=0xYOUR_PRIVATE_KEY

# OpenAI Configuration
OPENAI_API_KEY=sk-YOUR_OPENAI_KEY

# Logging
LOG_LEVEL=INFO
```

**Come ottenere le chiavi**:

1. **Hyperliquid Wallet**:
   - Vai su: https://app.hyperliquid-testnet.xyz/trade
   - Connect MetaMask
   - Settings → API → Generate Keys
   - Copia Address e Private Key

2. **OpenAI API Key**:
   - Vai su: https://platform.openai.com/api-keys
   - Create new secret key
   - Copia la chiave

Salva il file:
- Premi `Ctrl+X`
- Premi `Y`
- Premi `Enter`

---

## 🧪 FASE 5: Test Manuale (10 minuti)

### Step 5.1: Test Connessione Hyperliquid

```bash
cd /home/ubuntu/AurumBotX
source venv/bin/activate
python3 << 'EOF'
from hyperliquid.info import Info
from hyperliquid.utils import constants

info = Info(constants.TESTNET_API_URL, skip_ws=True)
prices = info.all_mids()
print("✅ Hyperliquid connected!")
print(f"BTC: ${float(prices['BTC']):,.2f}")
EOF
```

✅ Dovresti vedere il prezzo BTC

### Step 5.2: Test Bot Completo

```bash
python3 wallet_runner_hyperliquid.py config/hyperliquid_testnet_10k.json
```

✅ Dovresti vedere:
- Connessione a Hyperliquid
- Analisi di 6 pair
- AI recommendations
- Stato salvato

⏱️ Tempo: ~10 secondi

---

## ⚙️ FASE 6: Attivazione Sistema 24/7 (5 minuti)

### Step 6.1: Avvia Timer Systemd

```bash
# Abilita e avvia il timer
sudo systemctl enable aurumbotx-hyperliquid.timer
sudo systemctl start aurumbotx-hyperliquid.timer

# Verifica status
sudo systemctl status aurumbotx-hyperliquid.timer
```

✅ Dovresti vedere: **"Active: active (waiting)"**

### Step 6.2: Verifica Prossima Esecuzione

```bash
sudo systemctl list-timers aurumbotx-hyperliquid.timer
```

Dovresti vedere quando partirà il prossimo ciclo (tra ~1 ora).

### Step 6.3: Trigger Esecuzione Immediata (Opzionale)

Per testare subito:

```bash
sudo systemctl start aurumbotx-hyperliquid.service
```

### Step 6.4: Monitora Log in Real-Time

```bash
# Log systemd
sudo journalctl -u aurumbotx-hyperliquid.service -f

# Oppure log file
tail -f /home/ubuntu/AurumBotX/logs/hyperliquid_trading_*.log
```

Premi `Ctrl+C` per uscire.

---

## 📊 FASE 7: Monitoring e Manutenzione

### Comandi Utili

**Stato Sistema**:
```bash
# Status timer
sudo systemctl status aurumbotx-hyperliquid.timer

# Prossime esecuzioni
sudo systemctl list-timers

# Ultimi log
sudo journalctl -u aurumbotx-hyperliquid.service -n 50
```

**Gestione Timer**:
```bash
# Stop timer
sudo systemctl stop aurumbotx-hyperliquid.timer

# Restart timer
sudo systemctl restart aurumbotx-hyperliquid.timer

# Disable timer
sudo systemctl disable aurumbotx-hyperliquid.timer
```

**Controllo Stato Trading**:
```bash
# Visualizza stato wallet
cat /home/ubuntu/AurumBotX/hyperliquid_trading/hyperliquid_testnet_10k_state.json | python3 -m json.tool

# Conta trade eseguiti
cat /home/ubuntu/AurumBotX/hyperliquid_trading/hyperliquid_testnet_10k_state.json | grep -o '"total_trades": [0-9]*'
```

**Log Analysis**:
```bash
# Conta cicli eseguiti oggi
grep "CYCLE START" /home/ubuntu/AurumBotX/logs/hyperliquid_trading_$(date +%Y%m%d).log | wc -l

# Trova trade eseguiti
grep "TRADE SIGNAL" /home/ubuntu/AurumBotX/logs/hyperliquid_trading_*.log

# Errori recenti
grep "ERROR" /home/ubuntu/AurumBotX/logs/hyperliquid_trading_*.log | tail -20
```

### Script di Monitoring Rapido

Crea uno script per check veloce:

```bash
cat > /home/ubuntu/check_bot.sh << 'EOF'
#!/bin/bash
echo "🤖 AurumBotX Status Check"
echo "========================="
echo ""
echo "⏰ Timer Status:"
systemctl is-active aurumbotx-hyperliquid.timer
echo ""
echo "📊 Last Execution:"
sudo journalctl -u aurumbotx-hyperliquid.service -n 5 --no-pager
echo ""
echo "📈 Trading Stats:"
cat /home/ubuntu/AurumBotX/hyperliquid_trading/hyperliquid_testnet_10k_state.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f\"  Capital: €{data['current_capital']:.2f}\")
print(f\"  Total Trades: {data['total_trades']}\")
print(f\"  Win Rate: {data['winning_trades']}/{data['total_trades']} ({data['winning_trades']/max(data['total_trades'],1)*100:.1f}%)\")
print(f\"  Daily Trades: {data['daily_trades']}\")
"
EOF

chmod +x /home/ubuntu/check_bot.sh
```

Usa con:
```bash
/home/ubuntu/check_bot.sh
```

---

## 🎯 Risultati Attesi

### Prime 24 Ore

- ✅ 24 cicli eseguiti (1 ogni ora)
- ✅ 4-8 trade simulati
- ✅ 144 analisi AI complete
- ✅ 0 downtime
- ✅ €0 costi

### Prima Settimana

- ✅ 168 cicli eseguiti
- ✅ 30-60 trade simulati
- ✅ 1,008 analisi AI
- ✅ Dati sufficienti per ottimizzazione
- ✅ €0 costi

### Primo Mese

- ✅ 720 cicli eseguiti
- ✅ 120-240 trade simulati
- ✅ 4,320 analisi AI
- ✅ Dataset completo per ML
- ✅ €0 costi

---

## ⚠️ Troubleshooting

### Problema: "Out of host capacity"

**Causa**: Nessuna VM Always Free disponibile nella tua availability domain.

**Soluzione**:
1. Prova un'altra availability domain
2. Aspetta qualche ora e riprova
3. Prova in un'altra regione (se non hai ancora creato risorse)

### Problema: SSH non si connette

**Causa**: Firewall o chiave errata.

**Soluzione**:
```bash
# Verifica permessi chiave
chmod 600 ~/.ssh/oracle_key.key

# Prova con verbose
ssh -v -i ~/.ssh/oracle_key.key ubuntu@YOUR_IP

# Verifica security list in Oracle Console
# Compute → Instances → Instance Details → Primary VNIC → Subnet → Security List
# Deve avere regola: Ingress, Source 0.0.0.0/0, TCP, Port 22
```

### Problema: Timer non parte

**Causa**: Service non configurato correttamente.

**Soluzione**:
```bash
# Ricarica systemd
sudo systemctl daemon-reload

# Abilita e avvia
sudo systemctl enable aurumbotx-hyperliquid.timer
sudo systemctl start aurumbotx-hyperliquid.timer

# Check errori
sudo systemctl status aurumbotx-hyperliquid.service
sudo journalctl -u aurumbotx-hyperliquid.service -n 50
```

### Problema: "Permission denied" su log

**Causa**: Directory non accessibile.

**Soluzione**:
```bash
# Crea directory con permessi corretti
mkdir -p /home/ubuntu/AurumBotX/logs
mkdir -p /home/ubuntu/AurumBotX/hyperliquid_trading
chmod 755 /home/ubuntu/AurumBotX/logs
chmod 755 /home/ubuntu/AurumBotX/hyperliquid_trading
```

### Problema: Hyperliquid API error

**Causa**: Chiavi non configurate o invalide.

**Soluzione**:
```bash
# Verifica .env
cat /home/ubuntu/AurumBotX/.env

# Test connessione
cd /home/ubuntu/AurumBotX
source venv/bin/activate
python3 -c "from hyperliquid.info import Info; from hyperliquid.utils import constants; info = Info(constants.TESTNET_API_URL, skip_ws=True); print(info.all_mids()['BTC'])"
```

---

## 💰 Costi

### Oracle Cloud Always Free

| Risorsa | Limite | Costo |
|---------|--------|-------|
| **VM** | 2x Micro (1 GB RAM) | €0 |
| **Storage** | 200 GB | €0 |
| **Bandwidth** | 10 TB/mese | €0 |
| **Public IP** | 2 | €0 |

**TOTALE**: **€0/mese PERMANENTE** ✅

### Altri Costi

| Servizio | Utilizzo | Costo/Mese |
|----------|----------|------------|
| **Hyperliquid Testnet** | Illimitato | €0 |
| **OpenAI API** | ~4,320 calls | ~€2-5 |

**TOTALE REALE**: **€2-5/mese** (solo OpenAI)

---

## 🎉 Congratulazioni!

Hai deployato con successo AurumBotX su Oracle Cloud!

Il tuo bot è ora:
- ✅ Operativo 24/7
- ✅ Completamente automatico
- ✅ Praticamente gratuito (€2-5/mese)
- ✅ Con dati di mercato reali
- ✅ Zero rischio (testnet)

### Prossimi Step

1. **Monitora per 7 giorni**: Raccogli dati e verifica stabilità
2. **Analizza performance**: Win rate, ROI, pattern
3. **Ottimizza parametri**: Confidence threshold, position sizing
4. **Considera mainnet**: Solo dopo validazione completa

---

## 📞 Supporto

**Problemi?**
- Controlla la sezione Troubleshooting
- Verifica log: `sudo journalctl -u aurumbotx-hyperliquid.service -f`
- Check stato: `/home/ubuntu/check_bot.sh`

**Documentazione**:
- Oracle Cloud: https://docs.oracle.com/iaas/
- Hyperliquid: https://hyperliquid.gitbook.io/
- AurumBotX: https://github.com/Rexon-Pambujya/AurumBotX

---

**Made with 💡 by Manus AI**  
**Data: 26 Novembre 2025**
