#!/bin/bash
# Script avvio trading automatico AurumBotX

cd /home/ubuntu/AurumBotX

echo "🚀 Avvio Trading Automatico AurumBotX..."
echo "⏰ $(date)"
echo "📊 Strategia: Scalping 6M Conservativo"
echo "💰 Testnet: Binance"
echo ""

# Crea directory logs se non esiste
mkdir -p logs

# Avvia trading automatico
python3 automatic_trading_loop.py
