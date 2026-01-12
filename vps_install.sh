#!/bin/bash
# AurumBotX VPS Installation Script

echo "🚀 AurumBotX VPS Installation Starting..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Clone repository
if [ ! -d "AurumBotX" ]; then
    echo "📥 Cloning AurumBotX..."
    git clone https://github.com/Cryptomalo/AurumBotX.git
fi

cd AurumBotX

# Setup environment
cp .env.template .env
echo "⚙️ Configure .env file with your credentials"

# Build and start
echo "🏗️ Building and starting AurumBotX..."
docker-compose up -d --build

echo "✅ AurumBotX VPS Installation Complete!"
echo "🌐 Access: http://$(curl -s ifconfig.me)"
echo "📊 Dashboard: http://$(curl -s ifconfig.me):8507"
