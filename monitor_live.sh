#!/bin/bash
# Monitoring script for Live Paper Trading €10,000

echo "=========================================="
echo "AurumBotX - Live Paper Trading Monitor"
echo "=========================================="
echo ""

# Check if process is running
PID=$(ps aux | grep wallet_runner_live | grep -v grep | awk '{print $2}')
if [ -z "$PID" ]; then
    echo "❌ Wallet NOT running"
else
    echo "✅ Wallet running (PID: $PID)"
fi

echo ""
echo "--- Current State ---"
STATE_FILE="/home/ubuntu/AurumBotX/live_paper_trading/live_paper_trading_eur10,000/state.json"
if [ -f "$STATE_FILE" ]; then
    python3 << PYEOF
import json
with open("$STATE_FILE") as f:
    state = json.load(f)
    
print(f"Capital: €{state['current_capital']:,.2f} (Initial: €{state['initial_capital']:,.2f})")
print(f"ROI: {state['statistics']['roi_percentage']:+.2f}%")
print(f"Total Trades: {state['statistics']['total_trades']}")
print(f"Win Rate: {state['statistics']['win_rate']:.1f}%")
print(f"Daily Trades: {state['statistics']['daily_trades']}")
print(f"Daily P&L: €{state['statistics']['daily_pnl']:+.2f}")
print(f"Current Level: {state['current_level']}")
print(f"Open Positions: {len(state['open_positions'])}")
print(f"")
print(f"Bear trades skipped: {state['statistics']['bear_market_trades_skipped']}")
print(f"Low confidence skipped: {state['statistics']['low_confidence_skipped']}")
PYEOF
else
    echo "State file not found"
fi

echo ""
echo "--- Last 15 Log Lines ---"
LOG_FILE="/home/ubuntu/AurumBotX/live_paper_trading/live_paper_trading_eur10,000/trading.log"
if [ -f "$LOG_FILE" ]; then
    tail -15 "$LOG_FILE"
else
    echo "Log file not found"
fi

echo ""
echo "=========================================="
