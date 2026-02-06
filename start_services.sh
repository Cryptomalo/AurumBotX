#!/bin/sh

set -e

mkdir -p logs

echo "🚀 Avvio servizi AurumBotX (API + Dashboard)..."

# Avvia API server
python -m src.api.api_server_usdt > logs/api_server.log 2>&1 &
API_PID=$!
echo "✅ API server avviato (PID ${API_PID})"

# Avvia dashboard Streamlit se disponibile, altrimenti fallback HTTP statico
if command -v streamlit >/dev/null 2>&1; then
  streamlit run src/dashboards/modern_unified_dashboard.py \
    --server.address 0.0.0.0 \
    --server.port 8501 \
    --server.headless true > logs/dashboard_8501.log 2>&1 &
  DASH_PID=$!
  echo "✅ Dashboard avviata (PID ${DASH_PID})"
else
  python -m http.server 8501 > logs/dashboard_8501.log 2>&1 &
  DASH_PID=$!
  echo "⚠️  Streamlit non disponibile, avviato fallback HTTP (PID ${DASH_PID})."
fi

echo "📋 Log API: logs/api_server.log"
echo "📋 Log Dashboard: logs/dashboard_8501.log"
