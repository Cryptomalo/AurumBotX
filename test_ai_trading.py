import os

# Imposta le variabili d'ambiente per il test
os.environ["BINANCE_API_KEY_TESTNET"] = "ieuTfW7ZHrQp0ktZba8Fgs9b5QPygvC9w2qrhHg9ihTIfi2mRw4PCQbdNSm4GYie"
os.environ["BINANCE_SECRET_KEY_TESTNET"] = "pcbYMZbW00goPM7x5PTNbrFaUvkZ6Ik9RZYpViFv7LgVu3X3KxEaJIwFGrDdtBP4"
os.environ["OPENROUTER_API_KEY"] = "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"
os.environ["DATABASE_URL"] = "postgresql://aurumbotx_user:your_secure_password@localhost:5432/aurumbotx_db"

import asyncio
import logging
from utils.ai_trading import AITrading
from utils.data_loader import CryptoDataLoader
from utils.sentiment_analyzer import SentimentAnalyzer
from utils.prediction_model import PredictionModel

logging.basicConfig(level=logging.INFO)

async def test_ai_trading():
    data_loader = CryptoDataLoader(use_live_data=True)
    sentiment_analyzer = SentimentAnalyzer()
    prediction_model = PredictionModel()

    # Inizializza i moduli asincroni
    from utils.database import init_db
    await init_db()
    await data_loader.initialize()
    await sentiment_analyzer.initialize()

    ai_trading = AITrading()

    # Recupera dati di mercato per l'analisi
    symbol = "BTCUSDT"
    market_data = await data_loader.get_historical_data(symbol, interval="1d", start_date="2024-01-01")

    if market_data.empty:
        logging.warning("Nessun dato di mercato recuperato. Impossibile procedere con l'analisi.")
        return

    # Simula dati social (per ora vuoti, ci concentriamo sul market analysis)
    social_data = {}

    logging.info("Avvio analisi di mercato...")
    analysis_result = await ai_trading.analyze_market(symbol)
    if analysis_result:
        logging.info("Generazione segnali di trading...")
        signals = await ai_trading.generate_trading_signals(symbol)
        if signals:
            logging.info(f"Segnali di trading generati: {signals}")
        else:
            logging.info("Nessun segnale di trading generato.")
    else:
        logging.error("Analisi di mercato fallita.")

if __name__ == "__main__":
    asyncio.run(test_ai_trading())


