#!/bin/bash

# AurumBotX Railway Start Script

echo "🚀 Starting AurumBotX on Railway..."

# Set environment variables
export PYTHONPATH=/app
export STREAMLIT_SERVER_PORT=${PORT:-8507}
export STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Create directories
mkdir -p logs data backups

# Initialize databases
python3 -c "
import sqlite3
import os
from datetime import datetime

databases = ['mega_aggressive_trading.db', 'ultra_aggressive_trading.db', 'mainnet_optimization.db']

for db_name in databases:
    if not os.path.exists(db_name):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        if 'mega' in db_name:
            table_name = 'mega_trades'
        elif 'ultra' in db_name:
            table_name = 'ultra_trades'
        else:
            table_name = 'optimized_trades'
        
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                amount REAL NOT NULL,
                price REAL NOT NULL,
                profit_loss REAL NOT NULL,
                balance_after REAL NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f'✅ {db_name} initialized')

print('🎉 Databases ready!')
"

# Start main dashboard
echo "📊 Starting Unified Dashboard..."
streamlit run unified_real_dashboard.py --server.port=$PORT --server.address=0.0.0.0
