# Changelog

Tutte le modifiche notevoli a questo progetto saranno documentate in questo file.

Il formato è basato su [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e questo progetto aderisce a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.6.0] - 2025-11-17

### Added
- **Keep-Alive Anti-Hibernation System**: Heartbeat ogni 5 minuti per prevenire ibernazione sandbox
- **Live Market Data**: Integrazione MEXC API per dati di mercato in tempo reale
- **AI-Powered Analysis**: Integrazione OpenAI GPT-4 per decisioni di trading intelligenti
- **Bear Market Filter**: Protezione automatica per mercati ribassisti
- **Live Paper Trading €10,000**: Wallet con capitale realistico per validazione
- **Monitoring Scripts**: `monitor_live.sh` per controllo stato in tempo reale
- **Capital Chart**: Grafico visualizzazione andamento capitale

### Changed
- Intervallo cicli da 5 minuti a 4.5 ore (5 trade/giorno target)
- Confidence threshold aumentata a 75% (da 65%)
- Take profit aumentato a 8% (da 3%)
- Holding dinamico fino a 24 ore (da 5 minuti fissi)
- Position size ridotta a 4% (da 10%)

### Fixed
- **Timing Bug**: Risolto problema cicli irregolari (12.5h invece di 4.5h)
- Sandbox hibernation: Implementato keep-alive per esecuzione regolare
- MATIC/USDT API error: Rimosso pair problematico

### Removed
- File obsoleti: `wallet_runner_chameleon.py`, `wallet_runner_optimized.py`
- Configurazioni vecchie: `chameleon_demo_50.json`, `live_mexc_50_v3.json`
- __pycache__ e file temporanei

---

## [3.5.0] - 2025-11-14

### Added
- Strategia ottimizzata 5 trade/giorno
- Filtro confidence 75%
- Holding dinamico con monitoraggio ogni 1 minuto
- Contatore trade giornaliero con reset automatico

### Changed
- Riduzione drastica frequenza trade (da 151/giorno a 5/giorno target)
- Fee impact target <1% (da 8.8%)

### Performance
- 1 trade eseguito in 7 ore
- Win rate: 0% (sample size insufficiente)
- ROI: -0.38%
- **Conclusione**: Troppo conservativo

---

## [3.0.0] - 2025-11-12

### Added
- Chameleon Strategy con 3 livelli adattivi (TURTLE, RABBIT, EAGLE)
- Sistema di upgrade automatico basato su performance
- Demo trading con capitale $50
- Profit Factor tracking
- Win/Loss streak monitoring

### Performance
- 45 trade in 3.8 ore
- Win rate: 57.8%
- ROI: +5.82%
- Profit Factor: 2.88
- **Problema**: Over-trading (12 trade/ora)

---

## [2.0.0] - 2025-11-10

### Added
- Integrazione MEXC Exchange API
- Safety limits (daily loss, emergency stop)
- Multi-pair support (BTC, ETH, SOL, XRP, ADA, DOGE)
- State persistence con JSON
- Logging completo

### Changed
- Migrazione da Bybit a MEXC
- Architettura modulare

---

## [1.0.0] - 2025-11-08

### Added
- Prima versione funzionante
- Trading simulato
- Strategia base con TP/SL fissi
- Supporto Bybit Exchange

---

## Versioni Future

### [4.0.0] - Pianificato

#### Planned
- Whale Flow Tracker integration
- Institutional-grade market analysis
- Multi-exchange support (Binance, Bybit, OKX)
- Advanced risk management
- Real money trading mode
- Telegram/Email alerts
- Web dashboard
- Backtesting framework

---

## Note

### Versioning Scheme

- **Major** (X.0.0): Cambiamenti architetturali significativi
- **Minor** (0.X.0): Nuove feature, miglioramenti strategia
- **Patch** (0.0.X): Bug fix, ottimizzazioni

### Performance Metrics

| Versione | Win Rate | ROI | Trade/Giorno | Fee Impact |
|----------|----------|-----|--------------|------------|
| v3.0 | 57.8% | +5.82% | 288 | 4.7% |
| v3.5 | 0% | -0.38% | 3 | 1.0% |
| v3.6 | TBD | TBD | 5 (target) | <2% (target) |

### Known Issues

- **v3.6**: Nessun trade ancora eseguito (mercato sideways)
- **v3.6**: MATIC/USDT API error 400 (pair rimosso)

### Migration Guide

#### v3.0 → v3.6

```bash
# Backup vecchia configurazione
cp config/chameleon_high_profit_demo.json config/backup/

# Usa nuova configurazione
python3 wallet_runner_live.py config/live_paper_10k_eur.json

# Monitora
./monitor_live.sh
```

---

**Ultimo aggiornamento**: 17 Novembre 2025  
**Versione corrente**: 3.6.0  
**Status**: 🟢 Stable
