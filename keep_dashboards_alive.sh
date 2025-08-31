#!/bin/bash

# Script per mantenere le dashboard sempre attive
echo "🔄 Avvio sistema keep-alive dashboard..."

# Funzione per controllare dashboard
check_dashboard() {
    local port=$1
    local name=$2
    
    if curl -s http://localhost:$port > /dev/null; then
        echo "✅ $name operativo su porta $port"
        return 0
    else
        echo "⚠️ $name non risponde su porta $port"
        return 1
    fi
}

# Loop infinito per controllo continuo
while true; do
    echo "🔍 Controllo dashboard $(date '+%Y-%m-%d %H:%M:%S')"
    
    check_dashboard 8501 "Admin Dashboard"
    check_dashboard 8502 "Premium Dashboard"
    check_dashboard 8503 "Performance Dashboard"
    check_dashboard 8504 "Config Dashboard"
    check_dashboard 8505 "Mobile Dashboard"
    
    echo "⏰ Prossimo controllo tra 5 minuti..."
    sleep 300  # 5 minuti
done

