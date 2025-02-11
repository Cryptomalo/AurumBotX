
from utils.test_suite import AurumBotTester
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    tester = AurumBotTester()
    
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
