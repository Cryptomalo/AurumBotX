# 🚀 AurumBotX Hyperliquid - Quick Start

## Setup Rapido (5 minuti)

### 1. Ottieni Fondi Testnet

1. Vai su: https://app.hyperliquid-testnet.xyz/trade
2. Connect MetaMask
3. Clicca **"Faucet"** → Get testnet USDC
4. Riceverai ~10,000 USDC testnet

### 2. Genera API Keys

1. Settings (⚙️) → **API**
2. Clicca **"Generate New Key"**
3. Copia:
   - **Account Address**: `0x...`
   - **Private Key**: `0x...`
4. ⚠️ Salva in modo sicuro!

### 3. Configura Bot

```bash
# Clone repository
git clone https://github.com/Rexon-Pambujya/AurumBotX.git
cd AurumBotX

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install hyperliquid-python-sdk openai eth-account

# Configure environment
cp .env.example .env
nano .env
```

Inserisci nel `.env`:
```env
HYPERLIQUID_TESTNET=true
HYPERLIQUID_ACCOUNT_ADDRESS=0xYOUR_ADDRESS
HYPERLIQUID_SECRET_KEY=0xYOUR_PRIVATE_KEY
OPENAI_API_KEY=sk-YOUR_OPENAI_KEY
```

### 4. Test Bot

```bash
python3 wallet_runner_hyperliquid.py config/hyperliquid_testnet_10k.json
```

✅ Dovresti vedere analisi di 6 pair crypto!

---

## Deploy su Oracle Cloud (60 minuti)

Segui la guida completa: [ORACLE_CLOUD_DEPLOYMENT_GUIDE.md](./ORACLE_CLOUD_DEPLOYMENT_GUIDE.md)

**TL;DR**:
1. Crea account Oracle Cloud (gratis permanente)
2. Crea VM Always Free (Ubuntu 22.04)
3. SSH nella VM
4. Esegui: `./scripts/setup_oracle_cloud.sh`
5. Configura `.env`
6. Avvia timer: `sudo systemctl start aurumbotx-hyperliquid.timer`

**Risultato**: Bot operativo 24/7, €0/mese!

---

## Comandi Utili

### Locale (Testing)

```bash
# Attiva venv
source venv/bin/activate

# Test singolo ciclo
python3 wallet_runner_hyperliquid.py config/hyperliquid_testnet_10k.json

# Check stato
cat hyperliquid_trading/hyperliquid_testnet_10k_state.json | python3 -m json.tool

# View logs
tail -f logs/hyperliquid_trading_*.log
```

### Oracle Cloud (Production)

```bash
# Status sistema
sudo systemctl status aurumbotx-hyperliquid.timer

# View logs real-time
sudo journalctl -u aurumbotx-hyperliquid.service -f

# Trigger manuale
sudo systemctl start aurumbotx-hyperliquid.service

# Check rapido
/home/ubuntu/check_bot.sh
```

---

## FAQ

**Q: È gratis?**  
A: Sì! Oracle Cloud Always Free è permanente. Solo OpenAI API costa ~€2-5/mese.

**Q: Serve KYC?**  
A: No per Hyperliquid Testnet. Sì per Oracle Cloud (verifica carta).

**Q: Posso usare mainnet?**  
A: Sì, ma SOLO dopo aver validato su testnet per almeno 1 mese.

**Q: Quanto guadagno?**  
A: È testnet = paper trading. Nessun guadagno reale, solo dati per validazione.

**Q: Quanti trade al giorno?**  
A: Target 4-8 trade/giorno (max 12). Dipende da volatilità mercato.

**Q: Posso modificare i parametri?**  
A: Sì! Edita `config/hyperliquid_testnet_10k.json`

---

## Supporto

- 📖 Guida completa: [ORACLE_CLOUD_DEPLOYMENT_GUIDE.md](./ORACLE_CLOUD_DEPLOYMENT_GUIDE.md)
- 🐛 Issues: https://github.com/Rexon-Pambujya/AurumBotX/issues
- 📚 Docs Hyperliquid: https://hyperliquid.gitbook.io/

---

**Made with 💡 by Manus AI**
