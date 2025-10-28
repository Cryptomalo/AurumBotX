#!/bin/bash

# Script di Deployment per AurumBotX su VPS
# Questo script automatizza l'installazione di Docker e Docker Compose
# e il deployment dell'applicazione AurumBotX.

REPO_URL="https://github.com/Cryptomalo/AurumBotX.git"
PROJECT_DIR="AurumBotX"

echo "--- Avvio del Deployment di AurumBotX ---"

# 1. Aggiornamento del sistema
echo "1. Aggiornamento dei pacchetti di sistema..."
sudo apt update -y
sudo apt upgrade -y

# 2. Installazione di Docker (se non già installato)
if ! command -v docker &> /dev/null
then
    echo "2. Docker non trovato. Installazione di Docker..."
    sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update -y
    sudo apt install -y docker-ce docker-ce-cli containerd.io
    
    # Aggiungi l'utente corrente al gruppo docker per eseguire comandi senza sudo
    echo "Aggiunta dell'utente al gruppo docker. Potrebbe essere necessario un logout/login."
    sudo usermod -aG docker ${USER}
else
    echo "2. Docker è già installato."
fi

# 3. Installazione di Docker Compose (se non già installato)
if ! command -v docker-compose &> /dev/null
then
    echo "3. Docker Compose non trovato. Installazione di Docker Compose..."
    # Usa il metodo raccomandato per l'installazione di Docker Compose (plugin)
    sudo apt install -y docker-compose-plugin
    # Crea un alias per docker compose
    sudo ln -s /usr/libexec/docker/cli-plugins/docker-compose /usr/bin/docker-compose
else
    echo "3. Docker Compose è già installato."
fi

# 4. Clonazione del repository GitHub
if [ -d "$PROJECT_DIR" ]; then
    echo "4. Directory $PROJECT_DIR esistente. Pulling degli ultimi cambiamenti..."
    cd $PROJECT_DIR
    git pull
    cd ..
else
    echo "4. Clonazione del repository AurumBotX..."
    git clone $REPO_URL
fi

# 5. Configurazione delle variabili d'ambiente
echo "5. Creazione del file .env per le variabili d'ambiente..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cat << EOF > "$PROJECT_DIR/.env"
# Variabili d'ambiente per AurumBotX
# SOSTITUIRE I VALORI PLACEHOLDER CON LE CHIAVI API REALI DI BINANCE E TELEGRAM

BINANCE_API_KEY="YOUR_BINANCE_API_KEY"
BINANCE_SECRET_KEY="YOUR_BINANCE_SECRET_KEY"
TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID="YOUR_TELEGRAM_CHAT_ID"
POSTGRES_PASSWORD="YOUR_POSTGRES_PASSWORD" # Se si usa Postgres

# Esempi di altre variabili di configurazione
# DATABASE_URL=sqlite:///data/trading_engine.db
# AURUM_ENV=production
EOF
    echo "File .env creato in $PROJECT_DIR. MODIFICARE QUESTO FILE con le credenziali reali PRIMA di avviare il container."
else
    echo "File .env esistente in $PROJECT_DIR. Assicurarsi che contenga le credenziali corrette."
fi

# 6. Avvio del container Docker
echo "6. Avvio del container AurumBotX con Docker Compose..."
cd $PROJECT_DIR
# Costruisce l'immagine e avvia i servizi in background
docker-compose up --build -d

echo "--- Deployment Completato ---"
echo "AurumBotX è in esecuzione in background."
echo "Controlla lo stato con: docker-compose ps"
echo "Controlla i log con: docker-compose logs -f"
echo "Le interfacce web sono disponibili su:"
echo " - Dashboard Streamlit (Moderno): http://<IP_VPS>:8502"
echo " - Web PWA Interface: http://<IP_VPS>:8080"
echo "NOTA: Se Docker è stato appena installato, potresti dover eseguire 'newgrp docker' o riavviare la sessione SSH per eseguire docker-compose senza 'sudo'."
