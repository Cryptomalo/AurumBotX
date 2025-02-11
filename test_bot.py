
import logging
from datetime import datetime
import time
from utils.auto_trader import AutoTrader
from utils.data_loader import CryptoDataLoader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=f'test_bot_{datetime.now().strftime("%Y%m%d")}.log'
)
logger = logging.getLogger(__name__)

def test_testnet():
    try:
        logger.info("Avvio test in modalità testnet")
        
        # Test connessione dati
        logger.info("Test connessione dati...")
        data_loader = CryptoDataLoader()
        df = data_loader.get_historical_data("BTC-USD", period='1d')
        if df is None or df.empty:
            raise Exception("Impossibile ottenere dati storici")
            
        # Test trading bot
        logger.info("Test trading bot...")
        bot = AutoTrader("BTC-USD", initial_balance=10000, testnet=True)
        
        # Test analisi mercato
        logger.info("Test analisi mercato...")
        signal = bot.analyze_market()
        if signal:
            logger.info(f"Segnale ricevuto: {signal}")
            
            # Test esecuzione trade
            logger.info("Test esecuzione trade...")
            success = bot.execute_trade(signal)
            if not success:
                raise Exception("Errore nell'esecuzione del trade")
            
        return True
    except Exception as e:
        logger.error(f"Test fallito: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_testnet()
    print(f"Test completato: {'Successo' if success else 'Fallito'}")
