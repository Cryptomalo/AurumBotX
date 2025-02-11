
import logging
from datetime import datetime
from utils.auto_trader import AutoTrader
from utils.data_loader import CryptoDataLoader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=f'migration_test_{datetime.now().strftime("%Y%m%d")}.log'
)

def test_system_stability():
    try:
        # Test componenti principali
        data_loader = CryptoDataLoader()
        trader = AutoTrader("BTC-USD", testnet=True)
        
        # Test connessione dati
        df = data_loader.get_historical_data("BTC-USD", period='1d')
        if df is not None and not df.empty:
            logging.info("Test dati storico: OK")
        
        # Test analisi mercato
        signal = trader.analyze_market()
        if signal is not None:
            logging.info("Test analisi mercato: OK")
            
        return True
    except Exception as e:
        logging.error(f"Test fallito: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_system_stability()
    print(f"Test completato: {'Successo' if success else 'Fallito'}")
