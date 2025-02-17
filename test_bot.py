import logging
import asyncio
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
from utils.dex_trading import DexSniper
from utils.risk_management import RiskManager
from utils.learning_module import LearningModule
from utils.ai_trading import AITrading
from utils.dashboard import TradingDashboard

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

# Setup logging with more verbose output
log_filename = f'test_bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
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
        self.dex_sniper: Optional[DexSniper] = None
        self.risk_manager: Optional[RiskManager] = None
        self.learning_module: Optional[LearningModule] = None
        self.ai_trading: Optional[AITrading] = None
        self.dashboard: Optional[TradingDashboard] = None
        self.should_run: bool = True
        self.test_duration: timedelta = timedelta(minutes=10)  # Reduced for testing
        self.start_time: datetime = datetime.now()
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

    async def initialize_components(self) -> bool:
        """Initialize all components with proper error handling"""
        try:
            logger.info("Initializing components...")

            # Initialize database first
            db_url = os.environ.get('DATABASE_URL')
            if not db_url:
                logger.error("DATABASE_URL not set")
                return False

            try:
                self.db = Database(db_url)
                if not await self.db_health_check():
                    return False
                logger.info("Database initialized successfully")
            except Exception as e:
                logger.error(f"Database connection error: {str(e)}")
                return False

            # Initialize data loader with retry mechanism
            try:
                self.data_loader = CryptoDataLoader(use_live_data=False)
                await self.data_loader.preload_data()
                logger.info("Data loader initialized successfully")
            except Exception as e:
                logger.error(f"Data loading error: {str(e)}")
                return False

            # Initialize other components with proper error handling
            try:
                self.websocket_handler = WebSocketHandler(logger, self.db)
                self.strategy_manager = StrategyManager()
                await self.strategy_manager.configure_for_live_testing()
                self.sentiment_analyzer = SentimentAnalyzer()
                self.backup_manager = BackupManager()
                self.auto_optimizer = AutoOptimizer(self.db, self.strategy_manager)
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
        try:
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

    async def run_ai_testnet_simulation(self):
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
                    # Process each test pair
                    for symbol in test_pairs:
                        logger.debug(f"Processing symbol: {symbol}")
                        predictions = await self.ai_trading.analyze_and_predict(symbol)
                        logger.debug(f"Predictions for {symbol}: {predictions}")

                        if predictions and isinstance(predictions, dict):
                            trade_result = await self.execute_ai_trade(predictions)
                            self.trade_results.append(trade_result)
                            logger.info(f"Trade result for {symbol}: {trade_result}")

                            try:
                                await self.dashboard.update_trade_data(trade_result)
                            except Exception as e:
                                logger.error(f"Dashboard update error: {str(e)}")

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

            await self.dashboard.update_report(report)
            logger.info(f"AI Trading Test Report: {report}")

        except Exception as e:
            logger.error(f"Error generating test report: {e}")

if __name__ == "__main__":
    logger.info("Starting AI testnet simulation...")
    bot = TestBot()
    success = asyncio.run(bot.run_ai_testnet_simulation())
    sys.exit(0 if success else 1)