import os
import sys
from src.core.trading_engine_usdt_sqlalchemy import TradingEngineUSDT

# Aggiungo il percorso del progetto al path di sistema
sys.path.append("/home/ubuntu/AurumBotX")

# Carico le API key dall'ambiente
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_SECRET_KEY")

if not api_key or not api_secret:
    print("ERRORE: Le variabili d'ambiente BINANCE_API_KEY e BINANCE_SECRET_KEY non sono state trovate.")
    sys.exit(1)

# Inizializzo il trading engine con le API key reali
engine = TradingEngineUSDT(binance_api_key=api_key, binance_api_secret=api_secret)

# Avvio il trading
result = engine.start_trading()

if result["success"]:
    print("Bot avviato in modalità di testing live.")
    print(f"Capitale iniziale: {result['initial_balance_usdt']} USDT")
    print(f"Strategia: {result['strategy']}")
    print(f"Coppie di trading: {result['trading_pairs']}")
else:
    print(f"Errore durante l'avvio del bot: {result['error']}")

