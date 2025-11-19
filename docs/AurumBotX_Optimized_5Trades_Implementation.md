# AurumBotX - Implementazione Strategia Ottimizzata 5 Trade/Giorno

## 📋 Riepilogo Implementazione

**Data**: 12 Novembre 2025  
**Versione**: 3.5 (Optimized 5 Trades/Day)  
**Status**: ✅ Implementato e Attivo

---

## 🎯 Obiettivi

L'implementazione della strategia ottimizzata 5 trade/giorno mira a risolvere il problema dell'over-trading identificato nel wallet Chameleon High-Profit Demo, che eseguiva 151 trade/giorno invece dei 3-6 previsti.

### Obiettivi Specifici

| Metrica | Valore Precedente | Target Ottimizzato | Miglioramento |
|---------|-------------------|-------------------|---------------|
| **Trade/giorno** | 151 | 5 | -97% |
| **Win Rate** | 59.1% | 70%+ | +18% |
| **Fee Impact** | 8.8% | <1% | -89% |
| **Confidence Threshold** | 65% | 75% | +15% |
| **Take Profit** | 3% | 8% | +167% |

---

## 🔧 Componenti Implementati

### 1. Configurazione Ottimizzata

**File**: `/home/ubuntu/AurumBotX/config/chameleon_optimized_5trades.json`

#### Parametri Chiave

```json
{
  "cycle_config": {
    "interval_hours": 4.5,
    "max_daily_trades": 6,
    "max_holding_hours": 24
  },
  "strategy": {
    "confidence_threshold": 0.75,
    "min_expected_profit": 0.06,
    "holding_strategy": "dynamic"
  },
  "risk_management": {
    "take_profit_percent": 0.08,
    "stop_loss_percent": 0.02
  }
}
```

#### Livelli Adattivi

Il sistema mantiene i 3 livelli Chameleon con parametri ottimizzati:

| Livello | Emoji | Position Size | Take Profit | Stop Loss | Confidence |
|---------|-------|---------------|-------------|-----------|------------|
| **TURTLE** | 🐢 | 4% | 8% | 2% | 75% |
| **RABBIT** | 🐇 | 6% | 10% | 2.5% | 70% |
| **EAGLE** | 🦅 | 10% | 12% | 3% | 65% |

### 2. Wallet Runner Ottimizzato

**File**: `/home/ubuntu/AurumBotX/wallet_runner_5trades.py`

#### Funzionalità Principali

1. **Holding Dinamico**
   - Monitoraggio posizioni ogni 1 minuto
   - Exit automatico su TP/SL/timeout
   - Max holding period: 24 ore
   - Nessun timeout forzato a 5 minuti

2. **Gestione Cicli**
   - Intervallo: 4.5 ore (5.33 cicli/giorno)
   - Analisi mercato: 30 minuti per ciclo
   - Decisione basata su confidence e expected profit

3. **Controllo Trade Giornalieri**
   - Contatore giornaliero automatico
   - Limite massimo: 6 trade/giorno
   - Reset automatico a mezzanotte

4. **Safety Limits**
   - Daily loss limit: 10%
   - Emergency stop: 30%
   - Max consecutive losses: 5
   - Circuit breaker attivo

---

## 📊 Logica di Decisione

### Condizioni per Aprire un Trade

Il sistema apre un trade solo se **tutte** le seguenti condizioni sono soddisfatte:

1. **Confidence Threshold**: `confidence >= 75%`
2. **Expected Profit**: `expected_profit >= 6%`
3. **Daily Trade Limit**: `daily_trades < 6`
4. **Daily Loss Limit**: `daily_pnl > -10%`
5. **No Circuit Breaker**: Sistema non in pausa per sicurezza

### Condizioni per Chiudere un Trade

Il sistema chiude automaticamente una posizione quando si verifica **una** delle seguenti:

1. **Take Profit**: `pnl_percent >= 8%` (TURTLE level)
2. **Stop Loss**: `pnl_percent <= -2%` (TURTLE level)
3. **Timeout**: `holding_time >= 24 hours`
4. **Trailing Stop**: Attivato al 5%, distanza 2%

---

## 🚀 Deployment

### Status Attuale

- **PID**: 18948
- **Start Time**: 2025-11-12 10:36:23
- **Initial Capital**: $50.00
- **Current Level**: TURTLE
- **Stato**: In attesa del prossimo ciclo (15:06:25)

### File di Sistema

| Tipo | Path | Descrizione |
|------|------|-------------|
| **Configurazione** | `/home/ubuntu/AurumBotX/config/chameleon_optimized_5trades.json` | Parametri strategia |
| **Codice** | `/home/ubuntu/AurumBotX/wallet_runner_5trades.py` | Wallet runner ottimizzato |
| **Stato** | `/home/ubuntu/AurumBotX/demo_trading/chameleon_optimized_5_trades_day/state.json` | Stato runtime |
| **Log Trading** | `/home/ubuntu/AurumBotX/demo_trading/chameleon_optimized_5_trades_day/trading.log` | Log dettagliato operazioni |
| **Log Sistema** | `/home/ubuntu/AurumBotX/logs/chameleon_optimized_5trades.log` | Log sistema |

### Comandi Utili

```bash
# Verifica processo attivo
ps aux | grep wallet_runner_5trades

# Monitora log trading
tail -f /home/ubuntu/AurumBotX/demo_trading/chameleon_optimized_5_trades_day/trading.log

# Controlla stato
cat /home/ubuntu/AurumBotX/demo_trading/chameleon_optimized_5_trades_day/state.json | python3 -m json.tool

# Stop wallet
kill -SIGINT <PID>
```

---

## 📈 Metriche di Successo

### Target Prime 24 Ore

| Metrica | Target | Come Misurare |
|---------|--------|---------------|
| **Trade Eseguiti** | 5 ± 1 | `state.statistics.total_trades` |
| **Win Rate** | ≥ 70% | `state.statistics.win_rate` |
| **ROI** | ≥ +2% | `state.statistics.roi_percentage` |
| **Fee Impact** | < 1% | `total_fees / total_volume` |
| **Avg Holding Time** | 4-12 ore | Analisi `trades_history` |

### Criteri di Validazione

✅ **Successo** se dopo 24 ore:
- Trade eseguiti: 4-6
- Win rate: ≥ 65%
- ROI: positivo
- Fee impact: < 2%

⚠️ **Review necessaria** se:
- Trade eseguiti: < 3 o > 7
- Win rate: < 60%
- ROI: negativo
- Fee impact: > 2%

❌ **Rollback** se:
- Trade eseguiti: > 10 o < 2
- Win rate: < 50%
- ROI: < -5%

---

## 🔄 Prossimi Step

### Fase 1: Monitoraggio (24-48 ore)

1. **Ore 0-6**: Verifica primo ciclo completo
2. **Ore 6-24**: Monitoraggio continuo metriche
3. **Ore 24-48**: Validazione stabilità

### Fase 2: Ottimizzazione Fine-Tuning (se necessario)

Se i risultati non soddisfano i target:

- **Troppi trade** (>7/giorno): Aumentare confidence threshold a 80%
- **Troppo pochi trade** (<3/giorno): Ridurre confidence a 70% o min_expected_profit a 5%
- **Win rate basso** (<65%): Aumentare confidence e ridurre max_daily_trades
- **Fee impact alto** (>1.5%): Aumentare intervallo cicli a 6 ore

### Fase 3: Integrazione v4.0 (opzionale)

Se la strategia 5 trade/giorno funziona bene, integrare:

1. **Whale Flow Tracker** (già implementato in `mvp_v4/modules/whale_flow_tracker.py`)
2. **Sentiment Analysis** con GPT-4.1
3. **Multi-timeframe Analysis**
4. **Advanced Risk Management**

Target v4.0: **75-85% win rate**

---

## 📝 Note Tecniche

### Differenze vs v3.0 (Precedente)

| Aspetto | v3.0 | v3.5 Optimized |
|---------|------|----------------|
| **Ciclo** | 5 minuti | 4.5 ore |
| **Holding** | Fisso 5 min | Dinamico fino a 24h |
| **Confidence** | 65% | 75% |
| **TP** | 3% | 8% |
| **Trade/giorno** | ~151 | ~5 |
| **Fee impact** | 8.8% | <1% target |

### Vantaggi Chiave

1. **Qualità > Quantità**: Solo trade ad alta probabilità
2. **Holding Ottimale**: Massimizza profitti lasciando correre i vincitori
3. **Fee Minimizzate**: 97% in meno di trade = 97% in meno di fee
4. **Scalabilità**: Meno risorse CPU per wallet
5. **Sostenibilità**: Strategia più robusta nel lungo periodo

---

## 🎓 Lessons Learned

### Dal Problema dell'Over-Trading

Il wallet Chameleon High-Profit Demo eseguiva 151 trade/giorno perché:

1. **Cicli troppo frequenti** (5 minuti)
2. **Confidence threshold troppo bassa** (65%)
3. **Exit forzato** a 5 minuti impediva ai trade di svilupparsi
4. **Nessun limite giornaliero** di trade

### Soluzioni Implementate

1. **Cicli ogni 4.5 ore** → Tempo adeguato per analisi e decisioni ponderate
2. **Confidence 75%** → Solo opportunità di alta qualità
3. **Holding dinamico** → Lascia correre i vincitori, taglia le perdite
4. **Limite 6 trade/giorno** → Safety net contro anomalie

---

## 📞 Supporto

Per problemi o domande:

1. Controllare i log: `trading.log` per dettagli operativi
2. Verificare lo stato: `state.json` per metriche real-time
3. Consultare documentazione v4.0: `/home/ubuntu/AurumBotX_V4_Technical_Specification.md`

---

**Documento creato**: 2025-11-12  
**Ultima modifica**: 2025-11-12  
**Versione**: 1.0
