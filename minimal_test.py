import logging
import asyncio
from datetime import datetime
from utils.auto_trader import AutoTrader
from utils.data_loader import CryptoDataLoader
from utils.sentiment_analyzer import SentimentAnalyzer
import os

# Setup logging avanzato
log_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f'test_bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def run_test():
    """Main test function with enhanced error handling and logging"""
    try:
        logger.info("Starting test in Binance Testnet environment")
        logger.info(f"Log file location: {log_file}")

        # Initialize components with detailed logging
        test_pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
        initial_balance = 1000  # USDT

        # Component initialization with detailed logging
        logger.info("Initializing DataLoader...")
        data_loader = CryptoDataLoader(use_live_data=True)
        logger.info("DataLoader initialized successfully")

        logger.info("Initializing SentimentAnalyzer...")
        sentiment_analyzer = SentimentAnalyzer()
        logger.info("SentimentAnalyzer initialized successfully")

        logger.info("Initializing AutoTrader...")
        bot = AutoTrader(
            symbol="BTCUSDT",
            initial_balance=initial_balance,
            risk_per_trade=0.02,  # 2% risk per trade
            testnet=True
        )
        logger.info("AutoTrader initialized successfully")

        # Test main loop with enhanced error handling
        for pair in test_pairs:
            try:
                logger.info(f"\n{'='*50}\nStarting test for {pair}\n{'='*50}")

                # Market data retrieval with validation
                logger.info(f"Fetching market data for {pair}...")
                market_data = data_loader.get_historical_data(pair, period='1d', interval='1m')

                if market_data is None:
                    logger.error(f"Market data is None for {pair}")
                    continue

                if market_data.empty:
                    logger.error(f"Empty market data for {pair}")
                    continue

                logger.info(f"Market data retrieved successfully for {pair}")
                logger.info(f"Market data shape: {market_data.shape}")
                logger.info(f"Last market price: {market_data['Close'].iloc[-1]}")

                # Sentiment analysis with detailed logging
                coin = pair.split('/')[0]
                logger.info(f"Starting sentiment analysis for {coin}...")

                sentiment = await sentiment_analyzer.analyze_social_sentiment(coin)
                logger.info(f"Sentiment analysis completed for {coin}")
                logger.info(f"Sentiment results: {sentiment}")

                # Market analysis and signal generation
                logger.info(f"Starting market analysis for {pair}...")
                signal = await bot.analyze_market_async(market_data, sentiment)

                if signal:
                    logger.info(f"Signal generated for {pair}:")
                    logger.info(f"Action: {signal.get('action')}")
                    logger.info(f"Confidence: {signal.get('confidence')}")
                    logger.info(f"Target price: {signal.get('target_price')}")

                    # Execute test trade
                    logger.info(f"Executing trade for {pair}...")
                    trade_result = await bot.execute_trade_async(signal)
                    logger.info(f"Trade execution result: {trade_result}")
                else:
                    logger.info(f"No trading signal generated for {pair}")

                # API rate limiting pause
                logger.info("Pausing before next test...")
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Error in test loop for {pair}", exc_info=True)
                continue

        # Final report
        final_balance = bot.balance
        profit_loss = ((final_balance - initial_balance) / initial_balance) * 100

        logger.info("\n" + "="*50)
        logger.info("Test Summary:")
        logger.info(f"Initial balance: {initial_balance} USDT")
        logger.info(f"Final balance: {final_balance} USDT")
        logger.info(f"P/L: {profit_loss:.2f}%")
        logger.info("="*50 + "\n")

    except Exception as e:
        logger.error("Critical error in test execution", exc_info=True)
        raise

if __name__ == "__main__":
    logger.info("\n" + "="*50)
    logger.info("Starting trading bot test in testnet environment")
    logger.info("="*50 + "\n")

    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error("Fatal error in main execution", exc_info=True)