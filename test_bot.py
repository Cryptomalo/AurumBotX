
from utils.test_suite import AurumBotTester
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    tester = AurumBotTester()
    
    # Test in ambiente testnet con dati reali
    logger.info("Avvio test in testnet con dati reali...")
    bot = AutoTrader("BTC-USD", initial_balance=10000, testnet=True)
    
    # Test di trading live in testnet
    try:
        for _ in range(5):  # Test 5 cicli di trading
            signal = bot.analyze_market()
            if signal:
                success = bot.execute_trade(signal)
                logger.info(f"Esecuzione trade testnet: {'successo' if success else 'fallito'}")
            time.sleep(60)  # Attendi 1 minuto tra le operazioni
    except Exception as e:
        logger.error(f"Errore durante il test live: {str(e)}")
    
    # Test di stabilità (30 minuti)
    logger.info("Avvio test di stabilità...")
    stability_results = tester.test_stability(30)
    if stability_results:
        logger.info(f"Risultati test stabilità: {stability_results}")
    
    # Test di performance
    logger.info("Avvio test di performance...")
    performance_results = tester.test_performance()
    if performance_results:
        logger.info(f"Risultati test performance: {performance_results}")

if __name__ == "__main__":
    main()
