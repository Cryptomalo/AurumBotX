#!/bin/bash
# AurumBotX Stop Script

echo "🛑 Fermata AurumBotX..."

# Ferma processi Python
pkill -f "mega_aggressive_trading.py"
pkill -f "streamlit run unified_real_dashboard.py"

echo "✅ AurumBotX fermato!"
