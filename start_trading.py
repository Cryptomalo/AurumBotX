
import asyncio
import logging
import signal
from datetime import datetime
from utils.trading_bot import WebSocketHandler
from utils.database_manager import DatabaseManager
from utils.system_checkup import run_system_checkup

# Configure logging
log_filename = f'trading_bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        self.handler = None
        self.db_manager = None
        self.should_run = True
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        logger.info("Received shutdown signal, initiating graceful shutdown...")
        self.should_run = False
        if self.handler:
            asyncio.create_task(self.handler.cleanup())

    async def initialize(self):
        """Initialize bot components"""
        try:
            # Initialize database
            self.db_manager = DatabaseManager()
            await self.db_manager.initialize()
            
            # Initialize WebSocket handler
            self.handler = WebSocketHandler()
            return True
        except Exception as e:
            logger.error(f"Initialization error: {str(e)}")
            return False

    async def start(self):
        """Start the trading bot"""
        try:
            # Run system checkup
            checkup_result = await run_system_checkup()
            if not checkup_result:
                logger.error("System checkup failed")
                return

            # Initialize components
            if not await self.initialize():
                return

            # Connect WebSocket
            if await self.handler.connect_websocket():
                logger.info("Trading bot started successfully")
                while self.should_run and self.handler.check_connection():
                    await asyncio.sleep(1)
            else:
                logger.error("Failed to establish WebSocket connection")

        except Exception as e:
            logger.error(f"Error in trading bot: {str(e)}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.handler:
                await self.handler.cleanup()
            if self.db_manager:
                await self.db_manager.cleanup()
            logger.info("Trading bot shutdown completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

async def main():
    bot = TradingBot()
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down due to keyboard interrupt...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
