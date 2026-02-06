#!/bin/sh

# Carica variabili d'ambiente da .env se presente
if [ -f ".env" ]; then
  set -a
  . ./.env
  set +a
fi

# Verifica configurazione essenziale
if [ -z "${BINANCE_API_KEY}" ] || [ -z "${BINANCE_SECRET_KEY}" ]; then
  echo "⚠️  BINANCE_API_KEY o BINANCE_SECRET_KEY non configurate."
  echo "   Configura le variabili ambiente o il file .env prima di avviare il bot."
fi

# Avvia l'interfaccia Streamlit (se presente)
if [ -f "team_management_system.py" ]; then
  streamlit run team_management_system.py --server.address 0.0.0.0 --server.port "${DASHBOARD_PORT:-8507}" --server.headless true &
else
  echo "⚠️  team_management_system.py non trovato, dashboard non avviata."
fi

# Avvia il Trading Bot
python3 start_trading.py &

# Avvio monitor opzionale se presente
if [ -f "monitor_24_7.py" ]; then
  python3 monitor_24_7.py &
else
  echo "⚠️  monitor_24_7.py non trovato, monitor non avviato."
fi

# Attendi che tutti i processi siano terminati
wait

