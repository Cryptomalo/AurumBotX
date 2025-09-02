#!/bin/bash
# AurumBotX Startup Script

echo "🚀 Avvio AurumBotX..."

# Controlla Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 non trovato"
    exit 1
fi

# Installa dipendenze
echo "📦 Installazione dipendenze..."
pip3 install -r requirements.txt

# Crea directory necessarie
mkdir -p logs reports configs validation_results simulation_results data

# Setup database
echo "🗄️ Setup database..."
python3 -c "
import sqlite3
import os
from datetime import datetime

# Crea database se non esiste
if not os.path.exists('aurumbotx.db'):
    conn = sqlite3.connect('aurumbotx.db')
    cursor = conn.cursor()
    
    # Tabella demo trades
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS demo_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            amount REAL NOT NULL,
            price REAL NOT NULL,
            confidence REAL NOT NULL,
            profit_loss REAL NOT NULL,
            balance_after REAL NOT NULL,
            position_size_percent REAL NOT NULL
        );
    ''')
    
    # Inserisci dati demo
    import random
    balance = 250.0
    for i in range(10):
        action = random.choice(['BUY', 'SELL'])
        amount = balance * random.uniform(0.05, 0.15)
        price = random.uniform(60000, 70000)
        confidence = random.uniform(0.6, 0.9)
        profit_loss = amount * random.uniform(-0.02, 0.03)
        balance += profit_loss
        
        cursor.execute('''
            INSERT INTO demo_trades 
            (timestamp, action, amount, price, confidence, profit_loss, balance_after, position_size_percent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            action, amount, price, confidence, profit_loss, balance, 
            random.uniform(5, 15)
        ))
    
    conn.commit()
    conn.close()
    print('✅ Database demo creato')
"

# Avvia sistema
echo "🌐 Avvio dashboard..."
echo "📊 Dashboard disponibile su: http://localhost:8507"
echo "🔐 Login: admin / admin123"

# Avvia in background se richiesto
if [ "$1" = "--background" ]; then
    nohup streamlit run team_management_system.py --server.port=8507 --server.address=0.0.0.0 > logs/startup.log 2>&1 &
    echo "✅ Sistema avviato in background"
    echo "📋 Log: tail -f logs/startup.log"
else
    streamlit run team_management_system.py --server.port=8507 --server.address=0.0.0.0
fi
