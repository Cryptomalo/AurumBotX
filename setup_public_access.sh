#!/bin/bash
# AurumBotX Ngrok Setup per accesso esterno

echo "🌐 Setup accesso esterno AurumBotX..."

# Controlla se ngrok è installato
if ! command -v ngrok &> /dev/null; then
    echo "📦 Installazione ngrok..."
    
    # Download ngrok
    wget -q https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
    tar xzf ngrok-v3-stable-linux-amd64.tgz
    sudo mv ngrok /usr/local/bin/
    rm ngrok-v3-stable-linux-amd64.tgz
    
    echo "✅ Ngrok installato"
fi

# Avvia server in background
echo "🚀 Avvio server AurumBotX..."
python3 standalone_server.py 8080 &
SERVER_PID=$!

# Aspetta che il server si avvii
sleep 3

# Avvia ngrok
echo "🌐 Creazione tunnel pubblico..."
ngrok http 8080 --log=stdout > ngrok.log 2>&1 &
NGROK_PID=$!

# Aspetta che ngrok si avvii
sleep 5

# Estrae URL pubblico
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['tunnels'][0]['public_url'])
except:
    print('Errore estrazione URL')
")

echo ""
echo "🎉 AurumBotX accessibile pubblicamente!"
echo "🔗 URL Pubblico: $PUBLIC_URL"
echo "🔐 Login: admin / admin123"
echo ""
echo "📋 Condividi questo URL con il tuo team:"
echo "$PUBLIC_URL"
echo ""
echo "🛑 Premi Ctrl+C per fermare"

# Salva URL in file
echo "$PUBLIC_URL" > public_url.txt
echo "💾 URL salvato in public_url.txt"

# Mantieni attivo
trap "kill $SERVER_PID $NGROK_PID 2>/dev/null" EXIT
wait
