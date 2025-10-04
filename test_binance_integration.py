import os
from src.exchanges.binance_adapter import BinanceAdapter

# Carica le API key dall'ambiente
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_SECRET_KEY")

# Inizializza l'adapter
adapter = BinanceAdapter(api_key, api_secret)

# Prova a ottenere il saldo
balance = adapter.get_balance()
print("Saldo:", balance)

# Prova a ottenere il ticker di BTCUSDT
ticker = adapter.get_ticker("BTCUSDT")
print("Ticker BTCUSDT:", ticker)

