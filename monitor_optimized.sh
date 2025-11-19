#!/bin/bash
# Quick monitoring script for Optimized 5 Trades/Day wallet

echo "=========================================="
echo "AurumBotX - Optimized 5 Trades Monitor"
echo "=========================================="
echo ""

# Check if process is running
PID=$(ps aux | grep wallet_runner_5trades | grep -v grep | awk '{print $2}')
if [ -z "$PID" ]; then
    echo "❌ Wallet NOT running"
else
    echo "✅ Wallet running (PID: $PID)"
fi

echo ""
echo "--- Current State ---"
STATE_FILE="/home/ubuntu/AurumBotX/demo_trading/chameleon_optimized_5_trades_day/state.json"
if [ -f "$STATE_FILE" ]; then
    python3 << PYEOF
import json
with open("$STATE_FILE") as f:
    state = json.load(f)
    
print(f"Capital: \${state['current_capital']:.2f} (Initial: \${state['initial_capital']:.2f})")
print(f"ROI: {state['statistics']['roi_percentage']:+.2f}%")
print(f"Total Trades: {state['statistics']['total_trades']}")
print(f"Win Rate: {state['statistics']['win_rate']:.1f}%")
print(f"Daily Trades: {state['statistics']['daily_trades']}")
print(f"Daily P&L: \${state['statistics']['daily_pnl']:+.4f}")
print(f"Current Level: {state['current_level']}")
print(f"Open Positions: {len(state['open_positions'])}")
PYEOF
else
    echo "State file not found"
fi

echo ""
echo "--- Last 10 Log Lines ---"
LOG_FILE="/home/ubuntu/AurumBotX/demo_trading/chameleon_optimized_5_trades_day/trading.log"
if [ -f "$LOG_FILE" ]; then
    tail -10 "$LOG_FILE"
else
    echo "Log file not found"
fi

echo ""
echo "=========================================="
