import logging
from datetime import datetime
from utils.auto_trader import AutoTrader
from utils.data_loader import CryptoDataLoader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=f'test_bot_{datetime.now().strftime("%Y%m%d")}.log'
)
logger = logging.getLogger(__name__)

def run_test():
    try:
        logger.info("Starting minimal test")

        # Initialize bot with BTC-USD pair
        bot = AutoTrader(
            symbol="BTC-USD",
            initial_balance=1000,
            risk_per_trade=0.02
        )

        # Get and analyze market data
        signal = bot.analyze_market()
        if signal:
            logger.info(f"Signal received: {signal}")
            # Execute trade based on signal
            bot.execute_trade(signal)
        else:
            logger.info("No trading signal generated")

        logger.info(f"Test completed. Final balance: {bot.balance}")

    except Exception as e:
        logger.error(f"Test error: {str(e)}")

if __name__ == "__main__":
    run_test()