import asyncio
import logging
import json
import time
import websockets
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from utils.database_manager import DatabaseManager
from utils.models import TradingData

logger = logging.getLogger(__name__)

class WebSocketHandler:
    def __init__(self):
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connected: bool = False
        self.max_retries: int = 5
        self.retry_delay: int = 1
        self.last_heartbeat: float = time.time()
        self.heartbeat_interval: int = 30
        self.reconnect_lock: threading.Lock = threading.Lock()
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.should_run: bool = True
        self.db_manager = DatabaseManager()
        self._initialize_db()

    async def _initialize_db(self) -> None:
        """Initialize database connection"""
        try:
            await self.db_manager.initialize()
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise

    async def connect_websocket(self) -> bool:
        """Connect to WebSocket with error handling"""
        try:
            if self.ws:
                await self.ws.close()

            self.ws = await websockets.connect(
                "wss://stream.binance.com:9443/ws/!ticker@arr",
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            self.connected = True
            self.last_heartbeat = time.time()

            # Start message processing
            asyncio.create_task(self._process_messages())
            logger.info("WebSocket connection established successfully")
            return True

        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            return False

    async def _process_messages(self) -> None:
        """Process incoming WebSocket messages"""
        while self.connected and self.ws:
            try:
                message = await self.ws.recv()
                await self._on_message(message)
            except websockets.exceptions.ConnectionClosed:
                self.logger.error("WebSocket connection closed unexpectedly")
                self.connected = False
                await self.handle_websocket_error()
                break
            except Exception as e:
                logger.error(f"Message processing error: {str(e)}")
                continue

    async def _on_message(self, message: str) -> None:
        """Process and store messages"""
        try:
            data = json.loads(message)
            self.last_heartbeat = time.time()

            # Process only ticker data
            if isinstance(data, list):
                for ticker in data:
                    if all(k in ticker for k in ['s', 'c', 'v']):
                        trading_data = TradingData(
                            symbol=ticker['s'],
                            price=float(ticker['c']),
                            volume=float(ticker['v'])
                        )
                        async with self.db_manager.get_session() as session:
                            session.add(trading_data)
                            await session.commit()

        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding error: {str(e)}")
        except Exception as e:
            logger.error(f"Message handling error: {str(e)}")

    async def handle_websocket_error(self) -> bool:
        """Handle WebSocket errors with retry"""
        retry_count = 0
        current_delay = self.retry_delay

        while retry_count < self.max_retries and self.should_run:
            try:
                logger.info(f"Attempting reconnection {retry_count + 1}/{self.max_retries}")
                if await self.connect_websocket():
                    logger.info("Reconnection successful")
                    return True

                current_delay = min(current_delay * 2, 30)
                logger.info(f"Reconnection failed, waiting {current_delay}s before next attempt")
                await asyncio.sleep(current_delay)
                retry_count += 1

            except Exception as e:
                logger.error(f"Reconnection error: {str(e)}")
                retry_count += 1

        logger.critical("Failed to establish WebSocket connection after all retries")
        return False

    def check_connection(self) -> bool:
        """Verify connection status"""
        try:
            return bool(self.ws and self.connected)
        except:
            return False

    async def cleanup(self) -> None:
        """Cleanup resources"""
        self.should_run = False
        if self.ws:
            await self.ws.close()
        self.connected = False
        logger.info("WebSocket handler cleaned up")

async def main():
    handler = WebSocketHandler()
    try:
        if await handler.connect_websocket():
            logger.info("Trading bot started successfully")
            while handler.check_connection():
                await asyncio.sleep(1)
        else:
            logger.error("Failed to establish WebSocket connection")
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await handler.cleanup()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())