import asyncio
import logging
from datetime import datetime, timedelta
import os
import signal
import sys
from typing import Optional, Dict, Any
from sqlalchemy import text
from utils.trading_bot import WebSocketHandler
from utils.strategies.strategy_manager import StrategyManager
from utils.sentiment_analyzer import SentimentAnalyzer
from utils.database import Database
from utils.data_loader import CryptoDataLoader
from utils.auto_optimizer import AutoOptimizer
from utils.backup_manager import BackupManager

# Setup logging
log_filename = f'test_bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TestBot:
    def __init__(self):
        logger.info("Initializing TestBot...")
        self.db: Optional[Database] = None
        self.websocket_handler: Optional[WebSocketHandler] = None
        self.strategy_manager: Optional[StrategyManager] = None
        self.sentiment_analyzer: Optional[SentimentAnalyzer] = None
        self.data_loader: Optional[CryptoDataLoader] = None
        self.auto_optimizer: Optional[AutoOptimizer] = None
        self.backup_manager: Optional[BackupManager] = None
        self.should_run: bool = True
        self.test_duration: timedelta = timedelta(hours=4)
        self.start_time: datetime = datetime.now()
        self.setup_signal_handlers()
        logger.info("TestBot initialized successfully")

    def setup_signal_handlers(self) -> None:
        """Configure signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        logger.info("Signal handlers configured")

    def handle_shutdown(self, signum: int, frame: Any) -> None:
        """Handle graceful shutdown"""
        logger.info("Received shutdown signal...")
        self.should_run = False

    async def initialize_components(self) -> bool:
        """Initialize components with retry"""
        try:
            logger.info("Initializing components...")

            # Initialize database with proper error handling
            db_url = os.environ.get('DATABASE_URL')
            if not db_url:
                logger.error("DATABASE_URL not set")
                raise ValueError("DATABASE_URL not set")

            logger.info("Initializing database connection...")
            try:
                self.db = Database(db_url)
                logger.info("Database instance created successfully")
            except Exception as e:
                logger.error(f"Failed to create database instance: {e}")
                return False

            if not await self.db_health_check():
                logger.error("Database health check failed")
                return False

            logger.info("Database connection verified, proceeding with other components...")

            # Initialize components
            self.data_loader = CryptoDataLoader(use_live_data=True)
            self.websocket_handler = WebSocketHandler(logger, self.db)
            self.strategy_manager = StrategyManager()
            await self.strategy_manager.configure_for_live_testing()
            self.sentiment_analyzer = SentimentAnalyzer()

            # Initialize auto-optimization components
            self.backup_manager = BackupManager()
            self.auto_optimizer = AutoOptimizer(self.db, self.strategy_manager)

            logger.info("All components initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Component initialization error: {str(e)}")
            return False

    async def db_health_check(self) -> bool:
        """Verify database health with proper session handling"""
        if not self.db:
            logger.error("Database not initialized during health check")
            raise ValueError("Database not initialized")

        max_attempts = 3
        retry_delay = 5

        for attempt in range(max_attempts):
            try:
                logger.info(f"Database health check attempt {attempt + 1}")
                # Get a new session using the improved session handling
                session = self.db.get_session()
                try:
                    logger.debug("Executing test query...")
                    session.execute(text("SELECT 1"))
                    session.commit()
                    logger.info("Database health check passed")
                    return True
                except Exception as e:
                    logger.error(f"Test query failed: {str(e)}")
                    session.rollback()
                    raise
                finally:
                    session.close()

            except Exception as e:
                logger.error(f"Database health check attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_attempts - 1:
                    logger.info(f"Waiting {retry_delay}s before next attempt...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2

        logger.error("Database health check failed after all attempts")
        return False

    async def run_extended_test(self) -> bool:
        """Run extended test with real market data and testnet trading"""
        try:
            logger.info("Starting extended test with real market data...")

            if not await self.initialize_components():
                logger.error("Component initialization failed")
                return False

            test_pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
            optimization_interval = timedelta(hours=1)
            last_optimization = datetime.now()

            while self.should_run and datetime.now() - self.start_time < self.test_duration:
                try:
                    # Regular trading logic
                    for pair in test_pairs:
                        try:
                            market_data = await self.data_loader.get_historical_data_async(pair)
                            if market_data is None or market_data.empty:
                                logger.warning(f"No market data available for {pair}")
                                continue

                            sentiment = await self.sentiment_analyzer.analyze_social_sentiment(
                                pair.split('/')[0]
                            )

                            signals = []
                            if self.strategy_manager:
                                signals = await self.strategy_manager.analyze_all_strategies(
                                    market_data,
                                    sentiment,
                                    {'available_balance': 10000}
                                )

                            # Execute valid signals on testnet
                            for signal in signals:
                                if signal and signal.get('action') != 'hold':
                                    result = await self.execute_test_trade(signal)
                                    logger.info(f"Trade execution result: {result}")

                        except Exception as e:
                            logger.error(f"Error processing {pair}: {str(e)}")
                            continue

                    # Run auto-optimization periodically
                    current_time = datetime.now()
                    if current_time - last_optimization >= optimization_interval:
                        logger.info("Running strategy auto-optimization...")
                        await self.auto_optimizer.optimize_strategies()
                        last_optimization = current_time

                    # Wait before next iteration
                    await asyncio.sleep(60)

                except Exception as e:
                    logger.error(f"Error in main loop: {str(e)}")
                    await asyncio.sleep(60)  # Wait before retry

            logger.info("Extended test completed successfully")
            return True

        except Exception as e:
            logger.error(f"Error during extended test: {str(e)}")
            return False
        finally:
            await self.cleanup()

    async def execute_test_trade(self, signal: Dict) -> Dict:
        """Execute trade on testnet"""
        try:
            # Implement testnet trade execution
            return {
                'success': True,
                'action': signal['action'],
                'price': signal.get('price', 0),
                'size': signal.get('size', 0),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return {'success': False, 'error': str(e)}

    async def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            logger.info("Starting cleanup procedure...")
            if self.websocket_handler:
                await self.websocket_handler.cleanup()
            if self.strategy_manager:
                await self.strategy_manager.cleanup()
            logger.info("Resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    logger.info("Starting main program...")
    bot = TestBot()
    success = asyncio.run(bot.run_extended_test())
    sys.exit(0 if success else 1)