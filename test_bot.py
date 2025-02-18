import logging
import asyncio
from datetime import datetime, timedelta
import os
import signal
import sys
from typing import Optional, Dict, Any
import uvicorn
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
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

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('test_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AurumBot Trading API",
    description="Trading Bot Control Interface",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TestBot:
    def __init__(self):
        self.db_manager = None
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
        self.test_duration = timedelta(minutes=30)
        self.start_time = datetime.now()
        self.trade_results = []
        logger.info("TestBot instance created")

    async def initialize_components(self) -> bool:
        """Initialize all components with error handling"""
        try:
            # Initialize database
            db_url = os.environ.get('DATABASE_URL')
            if not db_url:
                logger.error("DATABASE_URL not set")
                return False

            self.db_manager = DatabaseManager()
            if not await self.db_manager.initialize(db_url):
                logger.error("Database initialization failed")
                return False

            logger.info("Database initialized")

            # Initialize core components
            self.data_loader = CryptoDataLoader(use_live_data=False)
            self.strategy_manager = StrategyManager()
            self.sentiment_analyzer = SentimentAnalyzer()

            logger.info("Core components initialized")

            # Initialize trading components
            self.ai_trading = AITrading({
                'min_confidence': 0.7,
                'use_sentiment': True,
                'risk_threshold': 0.8
            })

            logger.info("AI trading initialized")

            self.dashboard = TradingDashboard()
            logger.info("Dashboard initialized")

            return True

        except Exception as e:
            logger.error(f"Component initialization error: {str(e)}", exc_info=True)
            return False

    async def execute_test_trade(self) -> Dict:
        """Execute a test trade to verify system functionality"""
        try:
            logger.info("Executing test trade")
            test_data = {
                'symbol': 'BTC/USDT',
                'action': 'buy',
                'price': 50000,
                'amount': 0.1,
                'confidence': 0.85
            }

            if self.ai_trading:
                result = await self.ai_trading.analyze_and_predict('BTC/USDT')
                if result:
                    test_data.update(result)

            return {
                'success': True,
                'test_data': test_data,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Test trade error: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.db_manager:
                await self.db_manager.cleanup()
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}", exc_info=True)

# Global bot instance
bot = None

async def get_or_create_bot() -> TestBot:
    """Get existing bot instance or create new one"""
    global bot
    if not bot:
        bot = TestBot()
        if not await bot.initialize_components():
            logger.error("Bot initialization failed")
            return None
    return bot

# API Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AurumBot Trading API",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/status")
async def get_status():
    """Get bot status"""
    try:
        current_bot = await get_or_create_bot()
        if not current_bot:
            return {"status": "error", "message": "Bot not initialized"}

        return {
            "status": "running",
            "uptime": str(datetime.now() - current_bot.start_time),
            "trades": len(current_bot.trade_results)
        }
    except Exception as e:
        logger.error(f"Status check error: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

@app.post("/test")
async def test_trading():
    """Execute test trade"""
    try:
        current_bot = await get_or_create_bot()
        if not current_bot:
            return {"status": "error", "message": "Bot not initialized"}

        result = await current_bot.execute_test_trade()
        return result
    except Exception as e:
        logger.error(f"Test trade error: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

@app.get("/metrics")
async def get_metrics():
    """Get trading metrics"""
    try:
        current_bot = await get_or_create_bot()
        if not current_bot:
            return {"status": "error", "message": "Bot not initialized"}

        return {
            "total_trades": len(current_bot.trade_results),
            "active_pairs": ["BTC/USDT", "ETH/USDT"],
            "last_update": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Metrics error: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

@app.on_event("startup")
async def startup_event():
    """Initialize bot on startup"""
    try:
        await get_or_create_bot()
    except Exception as e:
        logger.error(f"Startup error: {str(e)}", exc_info=True)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        if bot:
            await bot.cleanup()
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}", exc_info=True)

def run_server():
    """Run the FastAPI server"""
    try:
        logger.info("Starting FastAPI server...")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=3001,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_server()