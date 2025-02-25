import os

def main():
    # Configura l'ambiente per la testnet
    os.environ['TRADING_MODE'] = 'test'
    os.environ['API_KEY'] = 'your_testnet_api_key'
    os.environ['API_SECRET'] = 'your_testnet_api_secret'
    os.environ['BASE_URL'] = 'https://testnet.example.com'

    # Avvia il bot di trading
    from trading_bot import TradingBot
    bot = TradingBot()
    bot.start()

if __name__ == "__main__":
    main()
