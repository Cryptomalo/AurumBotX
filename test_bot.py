import logging
import asyncio
from datetime import datetime, timedelta
import os
import signal
import sys
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import text
from utils.database_manager import DatabaseManager
from utils.trading_bot import WebSocketHandler
from utils.strategies.strategy_manager import StrategyManager
from utils.sentiment_analyzer import SentimentAnalyzer
from utils.data_loader import CryptoDataLoader
from utils.auto_optimizer import AutoOptimizer
from utils.backup_manager import BackupManager
from utils.dex_trading import DexSniper
from utils.risk_management import RiskManager
from utils.learning_module import LearningModule
from utils.ai_trading import AITrading
from utils.dashboard import TradingDashboard
from utils.database_manager import DatabaseManager

def setup_test_environment():
    """Setup test environment variables if not present"""
    test_vars = {
        'DATABASE_URL': os.environ.get('DATABASE_URL', 'postgresql://user:pass@localhost:5432/testdb'),
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY', 'test_key'),
        'ALPHA_VANTAGE_KEY': os.environ.get('ALPHA_VANTAGE_KEY', 'demo'),
        'BINANCE_API_KEY': os.environ.get('BINANCE_API_KEY', 'test'),
        'BINANCE_API_SECRET': os.environ.get('BINANCE_API_SECRET', 'test'),
    }

    for key, value in test_vars.items():
        if key not in os.environ:
            os.environ[key] = value
            logging.info(f"Set test environment variable: {key}")

# Setup logging
log_filename = f'test_bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.DEBUG,
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
        self.db_manager = DatabaseManager()
        self.websocket_handler = None
        self.strategy_manager = None
        self.sentiment_analyzer = None
        self.data_loader = None
        self.auto_optimizer = None
        self.backup_manager = None
        self.dex_sniper = None
        self.risk_manager = None
        self.learning_module = None
        self.ai_trading = None
        self.dashboard = None
        self.should_run = True
        self.test_duration = timedelta(minutes=10)
        self.start_time = datetime.now()
        self.trade_results = []
        setup_test_environment()
        self.setup_signal_handlers()
        logger.info("TestBot initialized successfully")

    def setup_signal_handlers(self):
        """Setup handlers for graceful shutdown"""
        def handle_signal(signum, frame):
            logger.info(f"Received signal {signum}")
            self.should_run = False

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

    async def initialize_database(self) -> bool:
        """Initialize database connection with proper async support"""
        try:
            logger.info("Initializing database connection...")
            db_url = os.environ.get('DATABASE_URL')
            if not db_url:
                logger.error("DATABASE_URL not set")
                return False

            return await self.db_manager.initialize(db_url)

        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            return False

    async def db_health_check(self) -> bool:
        """Verify database health"""
        try:
            return await self.db_manager.verify_connection()
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False

    async def initialize_components(self) -> bool:
        """Initialize all components with proper error handling"""
        try:
            logger.info("Initializing components...")

            # Initialize database first
            if not await self.initialize_database():
                logger.error("Database initialization failed")
                return False

            # Initialize other components
            try:
                self.data_loader = CryptoDataLoader(use_live_data=False)
                await self.data_loader.preload_data()

                self.websocket_handler = WebSocketHandler(logger, self.db_manager.engine) #Modified this line
                self.strategy_manager = StrategyManager()
                await self.strategy_manager.configure_for_live_testing()

                self.sentiment_analyzer = SentimentAnalyzer()
                self.backup_manager = BackupManager()
                self.auto_optimizer = AutoOptimizer(self.db_manager.engine, self.strategy_manager) #Modified this line
                self.dex_sniper = DexSniper(testnet=True)
                self.risk_manager = RiskManager()
                self.learning_module = LearningModule()

                self.ai_trading = AITrading({
                    'min_confidence': 0.7,
                    'use_sentiment': True,
                    'risk_threshold': 0.8
                })

                self.dashboard = TradingDashboard()
                logger.info("All components initialized successfully")
                return True

            except Exception as e:
                logger.error(f"Component initialization error: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"Component initialization error: {str(e)}")
            return False

    async def execute_ai_trade(self, signal: Dict) -> Dict:
        """Execute AI-driven trade with proper error handling"""
        try:
            if not signal or not isinstance(signal, dict):
                raise ValueError("Invalid signal format")

            return {
                'success': True,
                'action': signal.get('action'),
                'price': signal.get('price', 0),
                'size': signal.get('size', 0),
                'ai_confidence': signal.get('confidence', 0),
                'take_profit': signal.get('take_profit', 0),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"AI Trade execution error: {e}")
            return {'success': False, 'error': str(e)}

    async def run_ai_testnet_simulation(self) -> bool:
        """Run the AI testnet simulation with improved error handling"""
        try:
            logger.info("Starting AI-based testnet simulation...")
            if not await self.initialize_components():
                logger.error("Component initialization failed")
                return False

            test_pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
            logger.info(f"Testing with pairs: {test_pairs}")

            while self.should_run and (datetime.now() - self.start_time) < self.test_duration:
                try:
                    for symbol in test_pairs:
                        logger.debug(f"Processing symbol: {symbol}")
                        if self.ai_trading:  # Check if AI trading component is initialized
                            predictions = await self.ai_trading.analyze_and_predict(symbol)
                            logger.debug(f"Predictions for {symbol}: {predictions}")

                            if predictions and isinstance(predictions, dict):
                                trade_result = await self.execute_ai_trade(predictions)
                                self.trade_results.append(trade_result)
                                logger.info(f"Trade result for {symbol}: {trade_result}")

                                if self.dashboard:  # Check if dashboard is initialized
                                    await self.dashboard.update_trade_data(trade_result)
                        else:
                            logger.warning("AI trading component not initialized")

                    await asyncio.sleep(1)

                except Exception as e:
                    logger.error(f"Error in AI testnet simulation loop: {str(e)}")
                    await asyncio.sleep(2)

            await self.generate_test_report()
            logger.info("AI testnet simulation completed")
            return True

        except Exception as e:
            logger.error(f"Error during AI testnet simulation: {e}")
            return False

    async def generate_test_report(self):
        """Generate comprehensive test report with error handling"""
        try:
            logger.info("Generating AI testnet simulation report...")
            total_trades = len(self.trade_results)
            successful_trades = sum(1 for trade in self.trade_results if trade.get('success'))
            avg_confidence = sum(trade.get('ai_confidence', 0) for trade in self.trade_results) / max(total_trades, 1)
            avg_profit = sum(trade.get('take_profit', 0) - trade.get('price', 0) for trade in self.trade_results) / max(total_trades, 1)

            report = {
                "total_trades": total_trades,
                "successful_trades": successful_trades,
                "success_rate": f"{(successful_trades / max(total_trades, 1)) * 100:.2f}%",
                "average_confidence": f"{avg_confidence:.2f}",
                "average_profit_per_trade": f"${avg_profit:.2f}"
            }

            if self.dashboard:  # Check if dashboard is initialized
                await self.dashboard.update_report(report)
            logger.info(f"AI Trading Test Report: {report}")

        except Exception as e:
            logger.error(f"Error generating test report: {e}")

    async def cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Starting cleanup process...")

            if self.db_manager:
                await self.db_manager.cleanup()

            if self.websocket_handler:
                await self.websocket_handler.cleanup()

            if self.strategy_manager:
                await self.strategy_manager.cleanup()

            logger.info("Cleanup completed successfully")

        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting AI testnet simulation...")
    bot = TestBot()
    try:
        asyncio.run(bot.run_ai_testnet_simulation())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        asyncio.run(bot.cleanup())
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        asyncio.run(bot.cleanup())
    sys.exit(0)