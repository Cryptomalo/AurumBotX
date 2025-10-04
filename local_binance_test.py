import os
from binance.client import Client

# Istruzioni per l'utente
print("Questo script testa la connessione a Binance con le tue API key.")
print("Assicurati di aver impostato le variabili d'ambiente BINANCE_API_KEY e BINANCE_SECRET_KEY.")

# Carica le API key dall'ambiente
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_SECRET_KEY")

if not api_key or not api_secret:
    print("\nERRORE: Le variabili d'ambiente BINANCE_API_KEY e BINANCE_SECRET_KEY non sono state trovate.")
    print("Per favore, impostale e riesegui lo script.")
else:
    try:
        # Inizializza il client di Binance
        client = Client(api_key, api_secret)

        # Prova a ottenere le informazioni dell'account
        account_info = client.get_account()

        print("\nConnessione a Binance riuscita!")
        print(f"Account Type: {account_info['accountType']}")

        # Cerca il saldo in USDT
        usdt_balance = 0
        for balance in account_info['balances']:
            if balance['asset'] == 'USDT':
                usdt_balance = float(balance['free'])
                break
        
        print(f"Saldo USDT disponibile: {usdt_balance}")

    except Exception as e:
        print(f"\nERRORE di connessione a Binance: {e}")

