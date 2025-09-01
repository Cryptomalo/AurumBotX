#!/bin/bash
# AurumBotX Startup Script

echo "🚀 Avvio AurumBotX..."

# Controlla Python
python3 --version || {
    echo "❌ Python 3 non trovato"
    exit 1
}

# Avvia sistema principale
echo "🤖 Avvio Mega-Aggressive Trading..."
python3 mega_aggressive_trading.py &

# Attendi avvio
sleep 5

# Avvia dashboard
echo "📊 Avvio Dashboard Unificata..."
python3 -m streamlit run unified_real_dashboard.py --server.port=8507 --server.address=0.0.0.0 &

echo "✅ AurumBotX avviato!"
echo "📊 Dashboard: http://localhost:8507"
echo "🛑 Per fermare: ./stop_aurumbotx.sh"
