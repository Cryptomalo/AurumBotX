# AurumBotX v4.0 MVP - Design Semplificato

**Autore**: Manus AI  
**Data**: 12 Novembre 2025  
**Timeline**: 3-5 giorni  
**Obiettivo**: Validare ipotesi whale flows → win rate 75%+  

---

## 🎯 Obiettivo MVP

Creare una **versione minima funzionante** di v4.0 che:

1. ✅ Integra **whale flows** (componente critico)
2. ✅ Usa **GPT-4.1** per decisioni
3. ✅ Testa in **demo** per 48-72 ore
4. ✅ Valida se win rate **≥75%**
5. ✅ Decide se procedere con v4.0 completo

**Non include** (per velocità):
- Sentiment analysis (Twitter, Reddit, News)
- Technical multi-timeframe
- Macro events monitor
- Partial profit taking
- Advanced risk management

**Include solo**:
- Whale Flow Tracker (Whale Alert API)
- Market Data Collector (MEXC API)
- GPT-4.1 Decision Maker (simplified)
- Basic Execution (entry/exit semplice)

---

## 🏗️ Architettura MVP

```
┌─────────────────────────────────────────┐
│         MVP RESEARCH AGENT              │
│           (6h Analysis)                 │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐  ┌──────────────┐    │
│  │    Whale     │  │    Market    │    │
│  │    Flows     │  │     Data     │    │
│  │   Tracker    │  │  Collector   │    │
│  └──────────────┘  └──────────────┘    │
│         ↓                 ↓             │
│         └────────┬────────┘             │
│                  ↓                      │
│         ┌─────────────────┐             │
│         │  Data Buffer    │             │
│         │   (6h window)   │             │
│         └─────────────────┘             │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│       GPT-4.1 DECISION MAKER            │
│          (Simplified)                   │
├─────────────────────────────────────────┤
│  • Whale flow analysis                  │
│  • Market data synthesis                │
│  • GO/NO-GO decision                    │
│  • Entry/Exit plan                      │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│       BASIC EXECUTION ENGINE            │
├─────────────────────────────────────────┤
│  • Market order entry                   │
│  • Stop loss (fixed -2%)                │
│  • Take profit (fixed +8%)              │
│  • Max holding: 24h                     │
└─────────────────────────────────────────┘
```

---

## 📦 Componenti MVP

### 1. Whale Flow Tracker (Simplified)

**API**: Whale Alert (free tier)  
**Frequenza**: Real-time webhook + polling ogni 5 min  
**Dati raccolti**:

```json
{
  "timestamp": "2025-11-13T12:00:00Z",
  "pair": "BTC",
  "whale_activity_6h": {
    "large_transactions": [
      {
        "time": "2025-11-13T11:45:00Z",
        "from": "Unknown",
        "to": "Binance",
        "amount_usd": 134250000,
        "type": "exchange_inflow",
        "signal": "bearish"
      }
    ],
    "exchange_inflows_usd": 450000000,
    "exchange_outflows_usd": 900000000,
    "net_flow_usd": 450000000,
    "signal": "bullish",
    "confidence": 0.85
  }
}
```

**Implementazione**:

```python
# whale_flow_tracker_mvp.py
import requests
from datetime import datetime, timedelta

class WhaleFlowTrackerMVP:
    def __init__(self):
        self.api_url = "https://api.whale-alert.io/v1/transactions"
        self.api_key = "demo"  # Free tier
        self.buffer_hours = 6
    
    def fetch_whale_transactions(self, symbol="bitcoin"):
        """Fetch whale transactions from last 6 hours"""
        start_time = int((datetime.now() - timedelta(hours=self.buffer_hours)).timestamp())
        
        params = {
            "api_key": self.api_key,
            "start": start_time,
            "currency": symbol,
            "min_value": 1000000  # Min $1M
        }
        
        response = requests.get(self.api_url, params=params)
        return response.json()['transactions']
    
    def analyze_flows(self, transactions):
        """Analyze whale flows and generate signal"""
        inflows = 0
        outflows = 0
        
        for tx in transactions:
            if tx['to']['owner_type'] == 'exchange':
                inflows += tx['amount_usd']
            elif tx['from']['owner_type'] == 'exchange':
                outflows += tx['amount_usd']
        
        net_flow = outflows - inflows
        
        # Signal generation
        if net_flow > 100000000:  # >$100M net outflow
            signal = "strong_bullish"
            confidence = 0.85
        elif net_flow > 50000000:
            signal = "bullish"
            confidence = 0.75
        elif net_flow < -100000000:
            signal = "strong_bearish"
            confidence = 0.85
        elif net_flow < -50000000:
            signal = "bearish"
            confidence = 0.75
        else:
            signal = "neutral"
            confidence = 0.50
        
        return {
            "inflows_usd": inflows,
            "outflows_usd": outflows,
            "net_flow_usd": net_flow,
            "signal": signal,
            "confidence": confidence,
            "transactions_count": len(transactions)
        }
    
    def get_whale_data(self, symbol="bitcoin"):
        """Main method: get whale data and analysis"""
        transactions = self.fetch_whale_transactions(symbol)
        analysis = self.analyze_flows(transactions)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "whale_activity_6h": analysis,
            "raw_transactions": transactions[:10]  # Keep last 10 for context
        }
```

---

### 2. Market Data Collector (Simplified)

**API**: MEXC (già integrato)  
**Frequenza**: Ogni 5 min  
**Dati raccolti**:

```json
{
  "timestamp": "2025-11-13T12:00:00Z",
  "pair": "BTC/USDT",
  "price": 89500,
  "volume_24h": 45000000000,
  "change_24h_percent": 2.5,
  "high_24h": 90000,
  "low_24h": 87000,
  "rsi_14": 58,
  "trend": "uptrend"
}
```

**Implementazione**:

```python
# market_data_collector_mvp.py
import ccxt
from ta.momentum import RSIIndicator
import pandas as pd

class MarketDataCollectorMVP:
    def __init__(self, exchange='mexc'):
        self.exchange = getattr(ccxt, exchange)()
    
    def fetch_ohlcv(self, pair="BTC/USDT", timeframe="1h", limit=50):
        """Fetch OHLCV data"""
        ohlcv = self.exchange.fetch_ohlcv(pair, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
    
    def calculate_rsi(self, df, period=14):
        """Calculate RSI"""
        rsi = RSIIndicator(df['close'], window=period)
        return rsi.rsi().iloc[-1]
    
    def detect_trend(self, df):
        """Simple trend detection"""
        sma_20 = df['close'].rolling(20).mean().iloc[-1]
        sma_50 = df['close'].rolling(50).mean().iloc[-1]
        current_price = df['close'].iloc[-1]
        
        if current_price > sma_20 > sma_50:
            return "uptrend"
        elif current_price < sma_20 < sma_50:
            return "downtrend"
        else:
            return "sideways"
    
    def get_market_data(self, pair="BTC/USDT"):
        """Main method: get market data and analysis"""
        # Fetch ticker
        ticker = self.exchange.fetch_ticker(pair)
        
        # Fetch OHLCV for indicators
        df = self.fetch_ohlcv(pair)
        
        # Calculate indicators
        rsi = self.calculate_rsi(df)
        trend = self.detect_trend(df)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "pair": pair,
            "price": ticker['last'],
            "volume_24h": ticker['quoteVolume'],
            "change_24h_percent": ticker['percentage'],
            "high_24h": ticker['high'],
            "low_24h": ticker['low'],
            "rsi_14": rsi,
            "trend": trend
        }
```

---

### 3. GPT-4.1 Decision Maker (Simplified)

**Input**: Whale flows + Market data (6h)  
**Output**: GO/NO-GO + Entry/Exit plan  

**Prompt**:

```python
SYSTEM_PROMPT_MVP = """
You are a senior crypto trading analyst specializing in whale flow analysis.

You have access to:
1. Whale Flow Data (last 6 hours): Large transactions, exchange flows, net flow
2. Market Data: Price, volume, RSI, trend

Your task: Decide if there's a high-probability trading opportunity.

Rules:
- Only recommend GO if whale flows are STRONGLY supportive (net flow >$50M)
- Require confluence: whale signal + market trend aligned
- Target win rate: 75%+
- Be extremely selective

Output JSON format:
{
  "decision": "GO" or "NO-GO",
  "confidence": 0.0-1.0,
  "reasoning": "...",
  "action_plan": {
    "direction": "BUY" or "SELL",
    "entry_price": number,
    "stop_loss": number,
    "take_profit": number,
    "position_size_percent": 2-5
  }
}
"""

USER_PROMPT_TEMPLATE_MVP = """
Analyze this data and decide:

## Whale Flows (6h)
- Net Flow: ${net_flow:,.0f} USD
- Signal: {whale_signal}
- Confidence: {whale_confidence:.0%}
- Inflows: ${inflows:,.0f}
- Outflows: ${outflows:,.0f}
- Transactions: {tx_count}

## Market Data
- Pair: {pair}
- Price: ${price:,.2f}
- 24h Change: {change_24h:+.2f}%
- RSI(14): {rsi:.1f}
- Trend: {trend}

Should we trade? Provide your decision in JSON format.
"""
```

**Implementazione**:

```python
# gpt_decision_maker_mvp.py
import os
from openai import OpenAI
import json

class GPTDecisionMakerMVP:
    def __init__(self):
        self.client = OpenAI()  # API key from env
        self.model = "gpt-4.1-mini"
    
    def make_decision(self, whale_data, market_data):
        """Get trading decision from GPT-4.1"""
        
        # Format prompt
        user_prompt = USER_PROMPT_TEMPLATE_MVP.format(
            net_flow=whale_data['whale_activity_6h']['net_flow_usd'],
            whale_signal=whale_data['whale_activity_6h']['signal'],
            whale_confidence=whale_data['whale_activity_6h']['confidence'],
            inflows=whale_data['whale_activity_6h']['inflows_usd'],
            outflows=whale_data['whale_activity_6h']['outflows_usd'],
            tx_count=whale_data['whale_activity_6h']['transactions_count'],
            pair=market_data['pair'],
            price=market_data['price'],
            change_24h=market_data['change_24h_percent'],
            rsi=market_data['rsi_14'],
            trend=market_data['trend']
        )
        
        # Call GPT-4.1
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_MVP},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3  # Low temperature for consistency
        )
        
        # Parse response
        decision = json.loads(response.choices[0].message.content)
        
        return decision
```

---

### 4. Basic Execution Engine

**Funzionalità**:
- Market order entry
- Fixed stop loss (-2%)
- Fixed take profit (+8%)
- Max holding: 24h

```python
# execution_engine_mvp.py
from exchange_api import ExchangeAPI
from datetime import datetime, timedelta

class ExecutionEngineMVP:
    def __init__(self, exchange_api):
        self.api = exchange_api
        self.active_positions = []
    
    def execute_trade(self, decision, capital):
        """Execute trade based on GPT decision"""
        if decision['decision'] != 'GO':
            return None
        
        action_plan = decision['action_plan']
        
        # Calculate position size
        position_size_usd = capital * (action_plan['position_size_percent'] / 100)
        
        # Execute market order
        if action_plan['direction'] == 'BUY':
            order = self.api.create_market_buy_order(
                pair=action_plan['pair'],
                amount_usd=position_size_usd
            )
        else:
            order = self.api.create_market_sell_order(
                pair=action_plan['pair'],
                amount_usd=position_size_usd
            )
        
        # Track position
        position = {
            "id": order['id'],
            "pair": action_plan['pair'],
            "direction": action_plan['direction'],
            "entry_price": order['price'],
            "entry_time": datetime.now(),
            "position_size_usd": position_size_usd,
            "stop_loss": action_plan['stop_loss'],
            "take_profit": action_plan['take_profit'],
            "status": "open"
        }
        
        self.active_positions.append(position)
        return position
    
    def monitor_positions(self):
        """Monitor and close positions if needed"""
        for position in self.active_positions:
            if position['status'] != 'open':
                continue
            
            # Get current price
            current_price = self.api.fetch_price(position['pair'])
            
            # Check stop loss
            if current_price <= position['stop_loss']:
                self.close_position(position, current_price, "stop_loss")
            
            # Check take profit
            elif current_price >= position['take_profit']:
                self.close_position(position, current_price, "take_profit")
            
            # Check max holding time (24h)
            elif datetime.now() - position['entry_time'] > timedelta(hours=24):
                self.close_position(position, current_price, "timeout")
    
    def close_position(self, position, exit_price, reason):
        """Close position"""
        # Execute close order
        if position['direction'] == 'BUY':
            order = self.api.create_market_sell_order(
                pair=position['pair'],
                amount_usd=position['position_size_usd']
            )
        else:
            order = self.api.create_market_buy_order(
                pair=position['pair'],
                amount_usd=position['position_size_usd']
            )
        
        # Calculate P&L
        if position['direction'] == 'BUY':
            pnl = (exit_price - position['entry_price']) / position['entry_price']
        else:
            pnl = (position['entry_price'] - exit_price) / position['entry_price']
        
        pnl_usd = position['position_size_usd'] * pnl
        
        # Update position
        position['exit_price'] = exit_price
        position['exit_time'] = datetime.now()
        position['pnl_usd'] = pnl_usd
        position['pnl_percent'] = pnl * 100
        position['close_reason'] = reason
        position['status'] = 'closed'
        
        return position
```

---

## 🔄 MVP Operation Cycle

```
CYCLE START (Every 6 hours)
├─ Hour 0-6: Data Collection
│  ├─ Whale Flow Tracker: Monitor transactions
│  └─ Market Data Collector: Fetch price/indicators
│
├─ Hour 6: Decision Making
│  ├─ Aggregate 6h data
│  ├─ GPT-4.1 analysis
│  └─ GO/NO-GO decision
│
├─ If GO: Execute Trade
│  ├─ Market order entry
│  ├─ Set stop loss / take profit
│  └─ Start monitoring
│
└─ Continuous: Position Monitoring
   ├─ Check stop loss (every 1 min)
   ├─ Check take profit (every 1 min)
   └─ Check timeout (24h max)

CYCLE END → REPEAT
```

---

## 📅 Implementation Timeline

### Day 1: Setup & Whale Flows
- [ ] Setup project structure
- [ ] Whale Alert API integration
- [ ] Whale Flow Tracker implementation
- [ ] Test whale data collection
- [ ] Verify signal generation

### Day 2: Market Data & Integration
- [ ] Market Data Collector implementation
- [ ] MEXC API integration (reuse existing)
- [ ] Data aggregation logic
- [ ] Test 6h data buffer
- [ ] Integration whale + market data

### Day 3: GPT-4.1 Decision Maker
- [ ] OpenAI API setup
- [ ] Prompt engineering
- [ ] Decision maker implementation
- [ ] Test decision generation
- [ ] Validate JSON output

### Day 4: Execution Engine
- [ ] Basic execution engine
- [ ] Position tracking
- [ ] Stop loss / take profit logic
- [ ] Integration with exchange API
- [ ] End-to-end test

### Day 5: Demo Testing
- [ ] Deploy MVP demo
- [ ] Run 48h test
- [ ] Collect performance data
- [ ] Analyze win rate
- [ ] Decision: proceed with full v4.0?

---

## 🎯 Success Criteria

### MVP Test (48-72 hours)

**Minimum Acceptable**:
- Win Rate: ≥70%
- Trade Count: ≥3
- No crashes
- Whale data quality: Good

**Target**:
- **Win Rate: ≥75%** ✅
- Trade Count: 4-6
- Uptime: 100%
- Whale signal accuracy: ≥75%

**If Success** → Proceed with full v4.0 implementation

**If Partial** (65-74% win rate) → Optimize and retest

**If Failure** (<65%) → Revisit hypothesis

---

## 💡 Key Differences MVP vs Full v4.0

| Feature | MVP | Full v4.0 |
|---------|-----|-----------|
| **Analysis Window** | 6h | 24h |
| **Data Sources** | 2 (whale + market) | 5 (all) |
| **Decision Cycle** | Every 6h | Every 24h |
| **Trade Frequency** | 4/day | 1-2/day |
| **Risk Management** | Basic (fixed SL/TP) | Advanced (partial, trailing) |
| **Sentiment** | ❌ No | ✅ Yes |
| **Technical Multi-TF** | ❌ No | ✅ Yes |
| **Macro Events** | ❌ No | ✅ Yes |
| **Implementation Time** | 3-5 days | 23 days |

---

## 📊 Expected Results

### Hypothesis

**Whale flows alone** (without sentiment/technical/macro) should improve win rate from **54.8%** (v3.0 current) to **70-75%**.

### Rationale

1. **Whale flows = leading indicator**
   - Precede price movements
   - Alpha Arena data: 78% accuracy

2. **Simplified = less noise**
   - Focus on strongest signal
   - Avoid over-optimization

3. **GPT-4.1 synthesis**
   - Better than rule-based
   - Pattern recognition

### If Hypothesis Confirmed

→ Full v4.0 with all 5 data sources should reach **75-85%** win rate

### If Hypothesis Rejected

→ Whale flows alone not sufficient, need full multi-dimensional approach

---

## ✅ Next Steps

**Immediate** (Today):
1. Create project structure
2. Setup Whale Alert API
3. Start Day 1 implementation

**Tomorrow**:
1. Complete whale flow tracker
2. Test data collection
3. Start market data integration

**Day 3-5**:
1. GPT-4.1 integration
2. Execution engine
3. Demo testing
4. Results analysis

---

**MVP Design completato!** Ready for implementation? 🚀

---

**Autore**: Manus AI  
**Data**: 12 Novembre 2025  
**Versione**: 4.0.0-mvp
