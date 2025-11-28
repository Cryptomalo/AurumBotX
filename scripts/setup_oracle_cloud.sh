#!/bin/bash
#
# AurumBotX Oracle Cloud Setup Script
# This script sets up the complete environment on Oracle Cloud Always Free VM
#

set -e

echo "========================================"
echo "AurumBotX Oracle Cloud Setup"
echo "========================================"
echo ""

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
echo "🐍 Installing Python 3.11..."
sudo apt install -y python3.11 python3.11-venv python3-pip git curl

# Install system dependencies
echo "📚 Installing system dependencies..."
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev

# Create project directory
echo "📁 Creating project directory..."
cd /home/ubuntu
if [ ! -d "AurumBotX" ]; then
    git clone https://github.com/Rexon-Pambujya/AurumBotX.git
fi
cd AurumBotX

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install hyperliquid-python-sdk==0.21.0
pip install openai==1.12.0
pip install eth-account==0.10.0
pip install python-dotenv==1.0.0

# Create directories
echo "📂 Creating directories..."
mkdir -p hyperliquid_trading
mkdir -p logs
mkdir -p config

# Create .env file
echo "🔐 Creating .env file..."
cat > .env << 'EOF'
# Hyperliquid Configuration
HYPERLIQUID_TESTNET=true
HYPERLIQUID_ACCOUNT_ADDRESS=your_wallet_address_here
HYPERLIQUID_SECRET_KEY=your_private_key_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_key_here

# Logging
LOG_LEVEL=INFO
EOF

echo "⚠️  IMPORTANT: Edit .env file with your actual keys!"
echo "   nano /home/ubuntu/AurumBotX/.env"

# Create systemd service
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/aurumbotx-hyperliquid.service > /dev/null << 'EOF'
[Unit]
Description=AurumBotX Hyperliquid Testnet Trading Bot
After=network.target

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/home/ubuntu/AurumBotX
Environment="PATH=/home/ubuntu/AurumBotX/venv/bin"
ExecStart=/home/ubuntu/AurumBotX/venv/bin/python3 wallet_runner_hyperliquid.py config/hyperliquid_testnet_10k.json
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aurumbotx

[Install]
WantedBy=multi-user.target
EOF

# Create systemd timer
echo "⏰ Creating systemd timer..."
sudo tee /etc/systemd/system/aurumbotx-hyperliquid.timer > /dev/null << 'EOF'
[Unit]
Description=AurumBotX Hyperliquid Trading Bot Timer
Requires=aurumbotx-hyperliquid.service

[Timer]
OnBootSec=2min
OnUnitActiveSec=1h
AccuracySec=1min

[Install]
WantedBy=timers.target
EOF

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable timer
echo "✅ Enabling timer..."
sudo systemctl enable aurumbotx-hyperliquid.timer

echo ""
echo "========================================"
echo "✅ Setup Complete!"
echo "========================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Edit .env file with your keys:"
echo "   nano /home/ubuntu/AurumBotX/.env"
echo ""
echo "2. Test the bot manually:"
echo "   cd /home/ubuntu/AurumBotX"
echo "   source venv/bin/activate"
echo "   python3 wallet_runner_hyperliquid.py config/hyperliquid_testnet_10k.json"
echo ""
echo "3. Start the timer:"
echo "   sudo systemctl start aurumbotx-hyperliquid.timer"
echo ""
echo "4. Check status:"
echo "   sudo systemctl status aurumbotx-hyperliquid.timer"
echo "   sudo journalctl -u aurumbotx-hyperliquid.service -f"
echo ""
echo "5. Monitor logs:"
echo "   tail -f /home/ubuntu/AurumBotX/logs/hyperliquid_trading_*.log"
echo ""
