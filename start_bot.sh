#!/bin/sh

# Avvia l'interfaccia Streamlit
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 5000 --server.headless true &

# Avvia il Trading Bot
python3 start_trading.py &

# Avvia il System Monitor
python3 utils/system_checkup.py &

# Attendi che tutti i processi siano terminati
wait
