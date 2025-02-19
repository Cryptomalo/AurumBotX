import asyncio
import logging
import os
import signal
from datetime import datetime
from utils.trading_bot import WebSocketHandler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
        self.should_run = True
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        logger.info("Received shutdown signal...")
        self.should_run = False
        if self.handler:
            asyncio.create_task(self.handler.cleanup())

    async def start(self):
        try:
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                raise ValueError("DATABASE_URL not set")

            engine = create_engine(db_url)
            Session = sessionmaker(bind=engine)

            self.handler = WebSocketHandler(logger=logger, db=Session())

            if await self.handler.connect_websocket():
                logger.info("Trading bot started successfully")
                while self.should_run and self.handler.check_connection():
                    await asyncio.sleep(1)
            else:
                logger.error("Failed to establish WebSocket connection")

        except Exception as e:
            logger.error(f"Error: {str(e)}")
        finally:
            if self.handler:
                await self.handler.cleanup()

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