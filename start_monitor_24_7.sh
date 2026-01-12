#!/bin/bash

# AurumBotX 24/7 Monitor Startup Script
# Avvia il sistema di monitoraggio continuo con gestione automatica dei restart

echo "🚀 AVVIO AURUMBOTX 24/7 MONITOR"
echo "================================"

# Verifica dipendenze
echo "🔍 Verifica dipendenze..."
python3 -c "import asyncio, logging, psycopg2, ccxt" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Dipendenze mancanti, installazione..."
    pip3 install -r requirements.txt
fi

# Crea directory logs se non esiste
mkdir -p logs

# Funzione per avvio con restart automatico
start_monitor() {
    local restart_count=0
    local max_restarts=10
    
    while [ $restart_count -lt $max_restarts ]; do
        echo "📊 Avvio monitoraggio (tentativo $((restart_count + 1))/$max_restarts)..."
        echo "⏰ $(date '+%Y-%m-%d %H:%M:%S')"
        
        # Avvia il monitor
        python3 monitor_24_7.py
        
        # Controlla exit code
        exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            echo "✅ Monitoraggio terminato normalmente"
            break
        else
            echo "❌ Monitoraggio terminato con errore (exit code: $exit_code)"
            restart_count=$((restart_count + 1))
            
            if [ $restart_count -lt $max_restarts ]; then
                echo "🔄 Restart automatico in 30 secondi..."
                sleep 30
            else
                echo "💥 Raggiunto limite massimo di restart ($max_restarts)"
                echo "📧 Inviare notifica di errore critico"
                break
            fi
        fi
    done
}

# Funzione per monitoraggio in background
start_background() {
    echo "🌙 Avvio in background..."
    nohup bash -c "$(declare -f start_monitor); start_monitor" > logs/monitor_startup.log 2>&1 &
    echo $! > logs/monitor.pid
    echo "✅ Monitor avviato in background (PID: $(cat logs/monitor.pid))"
    echo "📄 Log: tail -f logs/monitor_startup.log"
}

# Funzione per stop del monitor
stop_monitor() {
    if [ -f logs/monitor.pid ]; then
        local pid=$(cat logs/monitor.pid)
        echo "🛑 Arresto monitor (PID: $pid)..."
        kill -TERM $pid 2>/dev/null
        sleep 5
        kill -KILL $pid 2>/dev/null
        rm -f logs/monitor.pid
        echo "✅ Monitor arrestato"
    else
        echo "⚠️ Nessun monitor in esecuzione"
    fi
}

# Funzione per status del monitor
status_monitor() {
    if [ -f logs/monitor.pid ]; then
        local pid=$(cat logs/monitor.pid)
        if ps -p $pid > /dev/null 2>&1; then
            echo "✅ Monitor in esecuzione (PID: $pid)"
            echo "📊 Uptime: $(ps -o etime= -p $pid | tr -d ' ')"
            echo "💾 Memoria: $(ps -o rss= -p $pid | tr -d ' ') KB"
        else
            echo "❌ Monitor non in esecuzione (PID file obsoleto)"
            rm -f logs/monitor.pid
        fi
    else
        echo "⚠️ Monitor non avviato"
    fi
}

# Funzione per visualizzare logs
show_logs() {
    echo "📄 Log files disponibili:"
    ls -la logs/*.log 2>/dev/null | tail -10
    echo ""
    echo "📊 Ultimi log monitor:"
    tail -20 logs/monitor_24_7_$(date +%Y%m%d).log 2>/dev/null || echo "Nessun log disponibile"
}

# Menu principale
case "${1:-menu}" in
    "start")
        start_monitor
        ;;
    "background"|"bg")
        start_background
        ;;
    "stop")
        stop_monitor
        ;;
    "restart")
        stop_monitor
        sleep 2
        start_background
        ;;
    "status")
        status_monitor
        ;;
    "logs")
        show_logs
        ;;
    "menu"|*)
        echo ""
        echo "🎛️  MENU AURUMBOTX 24/7 MONITOR"
        echo "================================"
        echo "1. start      - Avvia monitor in foreground"
        echo "2. background - Avvia monitor in background"
        echo "3. stop       - Arresta monitor"
        echo "4. restart    - Riavvia monitor"
        echo "5. status     - Mostra status monitor"
        echo "6. logs       - Mostra logs recenti"
        echo ""
        echo "Uso: $0 [start|background|stop|restart|status|logs]"
        echo ""
        echo "📊 Status attuale:"
        status_monitor
        ;;
esac

