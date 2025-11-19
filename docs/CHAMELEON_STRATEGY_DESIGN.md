# 🦎 Strategia Chameleon - Design Document

**Data**: 11 Novembre 2025  
**Capitale Iniziale**: $50 USDT  
**Obiettivo**: Crescita esponenziale adattiva  
**Exchange**: MEXC  
**Deployment**: Demo oggi, Mainnet domani 12:00  

---

## 🎯 Concept Strategia

La **Strategia Chameleon** si adatta dinamicamente alle condizioni di mercato come un camaleonte cambia colore, modificando:
- **Aggressività** (da conservative ad ultra-aggressive)
- **Position sizing** (da 1% a 10% del capitale)
- **Timeframe** (da 5m a 4h)
- **Coppie trading** (da 3 a 15 coppie)
- **Risk/Reward ratio** (da 1:2 a 1:5)

---

## 📊 Modalità Operative (5 Livelli)

### 🐢 Livello 1: TURTLE (Protezione Capitale)
**Quando**: Mercato molto volatile, perdite recenti, capitale <$60
- Position Size: 1-2% ($0.50-1.00)
- Stop Loss: 1%
- Take Profit: 3%
- Confidence: 70%+
- Coppie: 3 (BTC, ETH, USDC)
- Timeframe: 1h-4h
- **Obiettivo**: Preservare capitale

### 🐇 Livello 2: RABBIT (Crescita Moderata)
**Quando**: Mercato stabile, win rate >65%, capitale $60-$100
- Position Size: 2-3% ($1.20-3.00)
- Stop Loss: 1.5%
- Take Profit: 4%
- Confidence: 65%+
- Coppie: 5 (BTC, ETH, SOL, ADA, XRP)
- Timeframe: 30m-2h
- **Obiettivo**: Crescita costante 20-30%/mese

### 🦅 Livello 3: EAGLE (Crescita Aggressiva)
**Quando**: Trend chiaro, win rate >70%, capitale $100-$200
- Position Size: 3-5% ($3.00-10.00)
- Stop Loss: 2%
- Take Profit: 5%
- Confidence: 60%+
- Coppie: 8 (top altcoin)
- Timeframe: 15m-1h
- **Obiettivo**: Crescita 40-60%/mese

### 🐆 Livello 4: CHEETAH (Scalping Veloce)
**Quando**: Alta volatilità positiva, win rate >75%, capitale $200-$500
- Position Size: 5-7% ($10.00-35.00)
- Stop Loss: 2.5%
- Take Profit: 6%
- Confidence: 55%+
- Coppie: 12 (include meme coins)
- Timeframe: 5m-30m
- **Obiettivo**: Crescita 80-100%/mese

### 🚀 Livello 5: ROCKET (Esponenziale)
**Quando**: Mercato bull, win rate >80%, capitale >$500
- Position Size: 7-10% ($35.00-50.00+)
- Stop Loss: 3%
- Take Profit: 8%
- Confidence: 50%+
- Coppie: 15 (tutti i mercati)
- Timeframe: 1m-15m
- **Obiettivo**: Crescita 150-200%/mese

---

## 🔄 Meccanismo di Adattamento

### Trigger Upgrade (Livello Superiore)

```python
if (
    win_rate_last_20_trades > 70% AND
    capital_growth_last_7_days > 15% AND
    consecutive_wins >= 5 AND
    market_trend == "bullish" AND
    volatility < 30%
):
    upgrade_to_next_level()
```

### Trigger Downgrade (Livello Inferiore)

```python
if (
    win_rate_last_10_trades < 55% OR
    consecutive_losses >= 3 OR
    daily_loss > 5% OR
    market_volatility > 50% OR
    capital_drawdown > 10%
):
    downgrade_to_previous_level()
```

---

## 📈 Compounding Aggressivo

### Reinvestimento Profitti

**Formula Position Size Dinamica**:
```python
position_size = current_capital * level_percentage * confidence_multiplier * trend_multiplier

Dove:
- level_percentage: 1-10% (dipende da livello)
- confidence_multiplier: 0.8-1.2 (basato su AI confidence)
- trend_multiplier: 0.9-1.3 (basato su trend strength)
```

**Esempio**:
- Capitale: $100
- Livello: EAGLE (5%)
- Confidence: 75% (1.1x)
- Trend: Strong Bull (1.2x)
- Position Size: $100 * 0.05 * 1.1 * 1.2 = **$6.60**

### Profit Withdrawal Strategy

- **0-$100**: Reinvesti 100% profitti
- **$100-$500**: Reinvesti 90%, preleva 10%
- **$500-$1000**: Reinvesti 80%, preleva 20%
- **>$1000**: Reinvesti 70%, preleva 30%

---

## 🎨 Market Condition Detection

### 1. Trend Detection
```python
trend = analyze_trend(timeframes=['5m', '15m', '1h', '4h'])

if all_timeframes_aligned:
    trend_strength = "STRONG"
    trend_multiplier = 1.3
elif majority_aligned:
    trend_strength = "MODERATE"
    trend_multiplier = 1.1
else:
    trend_strength = "WEAK"
    trend_multiplier = 0.9
```

### 2. Volatility Analysis
```python
volatility = calculate_atr(period=14) / current_price * 100

if volatility < 2%:
    market_state = "LOW_VOLATILITY"  # TURTLE mode
elif volatility < 5%:
    market_state = "NORMAL"  # RABBIT/EAGLE mode
elif volatility < 10%:
    market_state = "HIGH"  # CHEETAH mode
else:
    market_state = "EXTREME"  # TURTLE mode (protezione)
```

### 3. Volume Analysis
```python
volume_ratio = current_volume / avg_volume_24h

if volume_ratio > 2.0:
    volume_signal = "STRONG_INTEREST"  # Opportunità
elif volume_ratio > 1.5:
    volume_signal = "MODERATE"
else:
    volume_signal = "LOW"  # Evita trade
```

---

## 🛡️ Risk Management Avanzato

### Dynamic Stop Loss

```python
# Stop loss si adatta a volatilità
base_stop_loss = level_config['stop_loss']
volatility_adjustment = min(volatility * 0.5, 2.0)
dynamic_stop_loss = base_stop_loss + volatility_adjustment

# Max 4%, min 0.5%
final_stop_loss = max(0.5, min(4.0, dynamic_stop_loss))
```

### Trailing Stop

```python
# Attiva trailing stop quando profit > 50% del target
if current_profit > take_profit_target * 0.5:
    enable_trailing_stop(
        activation_price=entry_price * (1 + take_profit_target * 0.5),
        trailing_distance=take_profit_target * 0.3
    )
```

### Position Sizing Limits

```python
# Mai più del 10% capitale in singolo trade
max_position = min(
    calculated_position,
    current_capital * 0.10
)

# Mai più del 30% capitale totale in trade aperti
if total_open_positions_value > current_capital * 0.30:
    skip_trade()
```

### Circuit Breaker

```python
# Stop trading automatico se:
if (
    daily_loss > capital * 0.08 OR  # -8% giornaliero
    consecutive_losses >= 5 OR
    capital < initial_capital * 0.70  # -30% totale
):
    emergency_stop()
    downgrade_to_TURTLE_mode()
    notify_user()
```

---

## 🤖 AI Integration Avanzata

### Multi-Model Ensemble

```python
# Usa 3 modelli AI per consensus
models = ['gpt-4-turbo', 'claude-3-opus', 'gemini-pro']

predictions = []
for model in models:
    pred = model.predict(market_data)
    predictions.append(pred)

# Trade solo se almeno 2/3 modelli concordano
if consensus(predictions) >= 0.66:
    confidence = average_confidence(predictions)
    execute_trade(confidence)
```

### Sentiment Analysis

```python
# Analizza sentiment da:
- Twitter trending topics
- Reddit r/cryptocurrency
- News headlines
- Fear & Greed Index

if sentiment_score > 70:
    sentiment_multiplier = 1.2  # Bullish
elif sentiment_score < 30:
    sentiment_multiplier = 0.8  # Bearish
else:
    sentiment_multiplier = 1.0  # Neutral
```

---

## 📊 Performance Targets

### Crescita Capitale Proiettata

| Timeframe | Target Conservativo | Target Medio | Target Aggressivo |
|-----------|---------------------|--------------|-------------------|
| **1 settimana** | $55 (+10%) | $60 (+20%) | $70 (+40%) |
| **2 settimane** | $65 (+30%) | $80 (+60%) | $100 (+100%) |
| **1 mese** | $85 (+70%) | $125 (+150%) | $200 (+300%) |
| **2 mesi** | $145 (+190%) | $250 (+400%) | $500 (+900%) |
| **3 mesi** | $250 (+400%) | $500 (+900%) | $1,000 (+1,900%) |

### Win Rate Targets per Livello

| Livello | Win Rate Target | Profit Factor | Max Drawdown |
|---------|-----------------|---------------|--------------|
| TURTLE | 75%+ | 5.0+ | 5% |
| RABBIT | 70%+ | 4.0+ | 8% |
| EAGLE | 68%+ | 3.5+ | 12% |
| CHEETAH | 65%+ | 3.0+ | 15% |
| ROCKET | 60%+ | 2.5+ | 20% |

---

## 🔧 Implementazione Tecnica

### File Struttura

```
AurumBotX/
├── chameleon_strategy.py      # Strategia principale
├── market_analyzer.py          # Analisi mercato
├── level_manager.py            # Gestione livelli
├── position_sizer.py           # Calcolo position size
├── risk_manager.py             # Risk management
└── config/
    ├── chameleon_demo_50.json  # Config demo
    └── chameleon_mainnet_50.json  # Config mainnet
```

### Parametri Configurabili

```json
{
  "strategy": "chameleon",
  "initial_level": "TURTLE",
  "auto_level_adjustment": true,
  "compounding_enabled": true,
  "max_level": "ROCKET",
  "conservative_mode": false,
  "ai_ensemble": true,
  "sentiment_analysis": true,
  "trailing_stop": true
}
```

---

## ⚡ Vantaggi Strategia Chameleon

1. **Adattabilità**: Si adatta automaticamente a qualsiasi condizione di mercato
2. **Protezione**: Downgrade automatico in caso di perdite
3. **Crescita**: Upgrade automatico quando performance positive
4. **Compounding**: Reinvestimento profitti per crescita esponenziale
5. **Risk Management**: Stop loss dinamici e circuit breaker
6. **AI Avanzata**: Multi-model ensemble per decisioni migliori
7. **Scalabilità**: Funziona da $50 a $10,000+

---

## ⚠️ Rischi e Mitigazioni

### Rischio 1: Over-Trading (Livelli alti)
**Mitigazione**: Limite max 30% capitale in posizioni aperte

### Rischio 2: Slippage (Scalping veloce)
**Mitigazione**: Usa solo coppie ad alta liquidità (volume >$10M)

### Rischio 3: Drawdown Eccessivo
**Mitigazione**: Circuit breaker -8% giornaliero, -30% totale

### Rischio 4: Falsi Segnali AI
**Mitigazione**: Multi-model ensemble, richiede consensus 66%

### Rischio 5: Flash Crash
**Mitigazione**: Stop loss sempre attivi, max position 10%

---

## 🎯 Piano Test Demo (Oggi)

### Fase 1: Test Livello TURTLE (2 ore)
- Capitale simulato: $50
- Verifica protezione capitale
- Win rate target: >75%

### Fase 2: Test Upgrade RABBIT (2 ore)
- Simula 5 win consecutive
- Verifica upgrade automatico
- Test position sizing

### Fase 3: Test Downgrade (1 ora)
- Simula 3 loss consecutive
- Verifica downgrade automatico
- Test circuit breaker

### Fase 4: Test Compounding (2 ore)
- Simula crescita 20%
- Verifica reinvestimento
- Test position size dinamico

### Fase 5: Stress Test (1 ora)
- Simula alta volatilità
- Simula flash crash
- Verifica tutti safety

**Totale**: 8 ore test → Deploy mainnet domani 12:00

---

## 📈 KPI Monitoraggio

### Metriche Primarie
- **ROI giornaliero**: Target >5%
- **Win Rate**: Target >65%
- **Profit Factor**: Target >3.0
- **Max Drawdown**: Limite <15%
- **Sharpe Ratio**: Target >2.0

### Metriche Secondarie
- **Livello attivo**: TURTLE → ROCKET
- **Trade/giorno**: 5-20 (dipende da livello)
- **Avg profit per trade**: $0.50-$5.00
- **Tempo medio trade**: 5min-4h
- **Fee impact**: <2% dei profitti

---

## ✅ Checklist Deployment Mainnet

- [ ] Test demo completato (8 ore)
- [ ] Win rate >65% in demo
- [ ] Tutti safety verificati
- [ ] Circuit breaker testato
- [ ] API MEXC configurate
- [ ] $50 USDT depositati
- [ ] Monitoring dashboard attivo
- [ ] Alert configurati
- [ ] Backup configurazione
- [ ] Emergency stop procedure documentata

---

**Strategia progettata il**: 11 Novembre 2025  
**Versione**: 1.0  
**Autore**: Manus AI  
**Sistema**: AurumBotX Chameleon Strategy  
**Target ROI**: 300-1,900% in 3 mesi 🚀
