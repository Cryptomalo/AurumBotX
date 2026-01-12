#!/bin/sh

# Imposta le variabili d'ambiente per il database
export DATABASE_URL="postgresql://aurumbotx_user:your_secure_password@localhost:5432/aurumbotx_db"
export ASYNC_DATABASE_URL="postgresql+asyncpg://aurumbotx_user:your_secure_password@localhost:5432/aurumbotx_db"

# Imposta le variabili d'ambiente per le API di Binance Testnet
export BINANCE_API_KEY_TESTNET="ieuTfW7ZHrQp0ktZba8Fgs9b5QPygvC9w2qrhHg9ihTIfi2mRw4PCQbdNSm4GYie"
export BINANCE_SECRET_KEY_TESTNET="pcbYMZbW00goPM7x5PTNbrFaUvkZ6Ik9RZYpViFv7LgVu3X3KxEaJIwFGrDdtBP4"

# Imposta la variabile d'ambiente per OpenRouter
export OPENROUTER_API_KEY="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"

# Avvia l'interfaccia Streamlit
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 5000 --server.headless true &

# Avvia il Trading Bot
python3 start_trading.py &

# Avvia il System Monitor
python3 utils/system_checkup.py &

# Attendi che tutti i processi siano terminati
wait


