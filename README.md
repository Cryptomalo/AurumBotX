# AurumBotX - AI-Powered Crypto Trading Bot

**Versione**: 3.6 Live Paper Trading  
**Status**: 🟢 Operativo  
**Ultimo Aggiornamento**: 17 Novembre 2025

---

## 📋 Panoramica

AurumBotX è un sistema di trading automatizzato per criptovalute che combina intelligenza artificiale, analisi di mercato in tempo reale e strategie adattive per massimizzare i profitti proteggendo il capitale.

### Caratteristiche Principali

- **AI-Powered Analysis**: Integrazione OpenAI GPT-4 per decisioni di trading intelligenti
- **Live Market Data**: Dati di mercato in tempo reale da MEXC Exchange
- **Bear Market Protection**: Filtri automatici per mercati ribassisti
- **Chameleon Strategy**: Sistema adattivo a 3 livelli (TURTLE, RABBIT, EAGLE)
- **Dynamic Holding**: Gestione posizioni fino a 24 ore con exit automatici
- **Paper Trading**: Testing sicuro senza rischio di capitale reale

---

## 🚀 Quick Start

### Requisiti

- Python 3.11+
- Account MEXC (per dati live)
- OpenAI API Key (per AI analysis)

### Installazione

```bash
# Clone repository
git clone https://github.com/Rexon-Pambujya/AurumBotX.git
cd AurumBotX

# Installa dipendenze
pip3 install requests openai

# Configura variabili ambiente
cp .env.example .env
# Edita .env con le tue API keys
```

### Avvio Paper Trading

```bash
# Avvia wallet live paper trading €10,000
python3 wallet_runner_live.py config/live_paper_10k_eur.json

# Monitora in tempo reale
./monitor_live.sh
```

---

## 📊 Performance Attuale

### Live Paper Trading €10,000

| Metrica | Valore |
|---------|--------|
| **Capital** | €10,000.00 |
| **ROI** | 0.00% |
| **Uptime** | 88+ ore |
| **Cicli Eseguiti** | 5 |
| **Trade Eseguiti** | 0 |
| **Status** | In attesa opportunità |

**Nota**: Nessun trade ancora eseguito perché il mercato è in fase sideways. L'AI correttamente raccomanda HOLD.

### Risultati Storici (Demo)

| Wallet | Capital | Trades | Win Rate | ROI |
|--------|---------|--------|----------|-----|
| **v3.0 High-Profit** | $50 → $52.91 | 45 | 57.8% | +5.82% |
| **v3.5 Optimized** | $50 → $49.81 | 1 | 0% | -0.38% |

---

## 🎯 Strategia Chameleon

### Livelli Adattivi

Il sistema si adatta automaticamente alle performance attraverso 3 livelli:

#### 🐢 TURTLE (Conservativo)
- Position Size: 4% del capitale
- Take Profit: 8%
- Stop Loss: 2%
- Confidence Threshold: 75%
- **Livello iniziale**

#### 🐇 RABBIT (Moderato)
- Position Size: 6% del capitale
- Take Profit: 10%
- Stop Loss: 2.5%
- Confidence Threshold: 70%
- **Upgrade**: +15% capitale, 70% win rate, 15 trade

#### 🦅 EAGLE (Aggressivo)
- Position Size: 10% del capitale
- Take Profit: 12%
- Stop Loss: 3%
- Confidence Threshold: 65%
- **Upgrade**: +30% capitale, 72% win rate, 30 trade

---

## 🛡️ Protezioni e Safety

### Bear Market Filter

Il sistema rileva automaticamente mercati ribassisti e:
- Aumenta confidence threshold a 85%
- Disabilita trade BUY
- Riduce position size del 50%
- Permette solo SELL trades

### Safety Limits

- **Daily Loss Limit**: -10% (stop trading per il giorno)
- **Emergency Stop**: -30% (stop completo sistema)
- **Max Consecutive Losses**: 5 (circuit breaker)
- **Max Position Size**: 5% del capitale

### Keep-Alive Anti-Hibernation

Sistema di heartbeat ogni 5 minuti per prevenire ibernazione sandbox e garantire esecuzione cicli regolari ogni 4.5 ore.

---

## 📁 Struttura Repository

```
AurumBotX/
├── README.md                          # Questo file
├── .gitignore                         # File da escludere
├── .env.example                       # Template variabili ambiente
│
├── config/                            # Configurazioni wallet
│   ├── chameleon_high_profit_demo.json
│   ├── chameleon_optimized_5trades.json
│   └── live_paper_10k_eur.json       # Config attuale
│
├── wallet_runner_live.py             # Runner principale (v3.6)
├── wallet_runner_5trades.py          # Runner ottimizzato 5 trade/giorno
├── chameleon_strategy.py             # Logica strategia Chameleon
├── exchange_api.py                   # Interfaccia MEXC API
├── safety_validator.py               # Validatore safety limits
│
├── monitor_live.sh                   # Script monitoraggio
├── monitor_optimized.sh              # Script monitoraggio ottimizzato
│
├── mvp_v4/                           # Whale Flow Tracker v4.0 (futuro)
│   └── WHALE_ALERT_API_SETUP.md
│
└── docs/                             # Documentazione strategia
    ├── CHAMELEON_STRATEGY_DESIGN.md
    ├── CHAMELEON_HIGH_PROFIT_STRATEGY.md
    ├── CHAMELEON_V3_LEARNING_DESIGN.md
    ├── CHAMELEON_V3_OPERATION_CYCLE.md
    ├── CHAMELEON_V4_INSTITUTIONAL_DESIGN.md
    └── MEXC_SETUP_GUIDE.md
```

---

## 🔧 Configurazione

### Variabili Ambiente

Crea file `.env` nella root:

```bash
# OpenAI API (per AI analysis)
OPENAI_API_KEY=sk-your-key-here

# MEXC API (opzionale, solo per trading reale)
MEXC_API_KEY=your-mexc-api-key
MEXC_SECRET_KEY=your-mexc-secret-key
```

### Configurazione Wallet

Edita `config/live_paper_10k_eur.json` per personalizzare:

```json
{
  "wallet_name": "Live Paper Trading €10,000",
  "initial_capital": 10000.0,
  "mode": "live_paper_trading",
  
  "cycle_config": {
    "interval_hours": 4.5,
    "max_daily_trades": 6,
    "max_holding_hours": 24
  },
  
  "strategy": {
    "confidence_threshold": 0.75,
    "bear_market_filter": true,
    "ai_analysis": true
  }
}
```

---

## 📈 Monitoraggio

### Script di Monitoraggio

```bash
# Status completo
./monitor_live.sh

# Log in tempo reale
tail -f live_paper_trading/live_paper_trading_eur10,000/trading.log

# Stato JSON
cat live_paper_trading/live_paper_trading_eur10,000/state.json | python3 -m json.tool
```

### Metriche Chiave

- **Capital**: Capitale corrente
- **ROI**: Return on Investment percentuale
- **Win Rate**: Percentuale trade vincenti
- **Profit Factor**: Rapporto profitti/perdite
- **Daily Trades**: Trade eseguiti oggi
- **Open Positions**: Posizioni aperte

---

## 🔄 Ciclo Operativo

1. **Market Analysis** (ogni 4.5 ore)
   - Scarica dati live da MEXC
   - Rileva trend di mercato
   - Analizza con AI (OpenAI GPT-4)

2. **Decision Making**
   - Verifica confidence threshold (75%)
   - Applica bear market filter
   - Controlla safety limits
   - Decide: BUY / SELL / HOLD

3. **Trade Execution** (se condizioni soddisfatte)
   - Calcola position size (4% in TURTLE)
   - Esegue entry (simulato in paper trading)
   - Imposta TP/SL

4. **Position Monitoring**
   - Check ogni 1 minuto
   - Exit automatico su TP/SL/timeout
   - Aggiorna statistiche

5. **Keep-Alive Heartbeat**
   - Heartbeat ogni 5 minuti
   - Previene ibernazione sandbox
   - Garantisce cicli regolari

---

## 🎓 Lezioni Apprese

### v3.0 → v3.6 Evolution

**v3.0 High-Profit**:
- ✅ ROI positivo (+5.82%)
- ❌ Over-trading (12 trade/ora)
- ❌ Fee impact alto (4.7%)

**v3.5 Optimized**:
- ✅ Fee impact basso (1%)
- ❌ Troppo conservativo (1 trade in 7 ore)
- ❌ Sample size insufficiente

**v3.6 Live Paper** (attuale):
- ✅ Dati live MEXC
- ✅ AI-powered decisions
- ✅ Bear market protection
- ✅ Timing corretto (4.5h)
- ✅ Capital adeguato (€10k)

---

## 🚧 Roadmap

### v3.6 (Attuale)
- [x] Live paper trading €10,000
- [x] AI analysis con OpenAI
- [x] Bear market filter
- [x] Keep-alive anti-hibernation
- [ ] Primo trade con dati live
- [ ] Validazione 7 giorni

### v4.0 (Prossimo)
- [ ] Whale Flow Tracker integration
- [ ] Institutional-grade analysis
- [ ] Multi-exchange support
- [ ] Advanced risk management
- [ ] Real money trading (dopo validazione)

---

## ⚠️ Disclaimer

**Questo software è fornito "as is" senza garanzie di alcun tipo.**

- Il trading di criptovalute comporta rischi significativi
- Le performance passate non garantiscono risultati futuri
- Usa solo capitale che puoi permetterti di perdere
- Il paper trading non replica perfettamente condizioni reali
- Non è un consiglio finanziario

---

## 📝 Licenza

MIT License - Vedi file LICENSE per dettagli

---

## 🤝 Contributi

I contributi sono benvenuti! Per favore:

1. Fork il repository
2. Crea un branch per la tua feature (`git checkout -b feature/AmazingFeature`)
3. Commit le modifiche (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

---

## 📧 Contatti

**Repository**: [github.com/Rexon-Pambujya/AurumBotX](https://github.com/Rexon-Pambujya/AurumBotX)

**Creato da**: Manus AI  
**Versione**: 3.6  
**Data**: Novembre 2025

---

**⭐ Se trovi utile questo progetto, lascia una stella su GitHub!**
