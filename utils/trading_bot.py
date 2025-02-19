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
        self.should_run: bool = True
        self.db_manager = DatabaseManager()
        self.connection_urls = [
            "wss://stream.binance.com:9443/ws/!ticker@arr",
            "wss://fstream.binance.com/ws/!ticker@arr",
            "wss://dstream.binance.com/ws/!ticker@arr"
        ]
        self.current_url_index = 0

    async def initialize(self) -> None:
        """Initialize the handler with database connection"""
        try:
            await self.db_manager.initialize()
            logger.info("WebSocket handler initialized successfully")
        except Exception as e:
            logger.error(f"Initialization error: {str(e)}")
            raise

    async def connect_websocket(self) -> bool:
        """Connect to WebSocket with improved error handling and fallback URLs"""
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass

        while self.current_url_index < len(self.connection_urls):
            try:
                url = self.connection_urls[self.current_url_index]
                logger.info(f"Attempting connection to {url}")

                self.ws = await websockets.connect(
                    url,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=10,
                    max_size=2**23,  # 8MB max message size
                    compression=None,
                    extra_headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )
                self.connected = True
                self.last_heartbeat = time.time()

                # Subscribe to ticker stream
                await self.ws.send(json.dumps({
                    "method": "SUBSCRIBE",
                    "params": ["!ticker@arr"],
                    "id": int(time.time() * 1000)
                }))

                # Start message processing
                asyncio.create_task(self._process_messages())
                logger.info(f"WebSocket connection established successfully to {url}")
                return True

            except websockets.exceptions.InvalidStatusCode as e:
                logger.error(f"Invalid status code from {url}: {e}")
                self.current_url_index += 1
                continue

            except Exception as e:
                logger.error(f"WebSocket connection error to {url}: {str(e)}")
                self.current_url_index += 1
                continue

        self.current_url_index = 0  # Reset for next retry cycle
        logger.error("All WebSocket endpoints failed")
        return False

    async def _process_messages(self) -> None:
        """Process incoming WebSocket messages with improved error handling"""
        while self.connected and self.ws:
            try:
                message = await self.ws.recv()
                await self._on_message(message)

                # Update heartbeat
                self.last_heartbeat = time.time()

            except websockets.exceptions.ConnectionClosed as e:
                logger.error(f"WebSocket connection closed: {str(e)}")
                self.connected = False
                await self.handle_websocket_error()
                break

            except Exception as e:
                logger.error(f"Message processing error: {str(e)}")
                if str(e).startswith(("Invalid control frame", "Connection reset", "Server rejected")):
                    self.connected = False
                    await self.handle_websocket_error()
                    break
                continue

    async def _on_message(self, message: str) -> None:
        """Process and store messages with validation"""
        try:
            data = json.loads(message)

            # Handle subscription confirmation
            if isinstance(data, dict) and 'result' in data:
                logger.info(f"Subscription response: {data}")
                return

            # Process ticker data
            if isinstance(data, list):
                valid_tickers = 0
                for ticker in data:
                    if all(k in ticker for k in ['s', 'c', 'v']):
                        try:
                            trading_data = TradingData(
                                symbol=ticker['s'],
                                price=float(ticker['c']),
                                volume=float(ticker['v']),
                                timestamp=datetime.now()
                            )
                            await self.db_manager.save_trading_data(trading_data)
                            valid_tickers += 1
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Invalid ticker data format: {e}")
                            continue

                if valid_tickers > 0:
                    logger.debug(f"Processed {valid_tickers} valid tickers")

        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding error: {str(e)}")
        except Exception as e:
            logger.error(f"Message handling error: {str(e)}")

    async def handle_websocket_error(self) -> bool:
        """Handle WebSocket errors with improved retry logic"""
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
        """Verify connection status and heartbeat"""
        try:
            if not (self.ws and self.connected):
                return False

            # Check heartbeat
            if time.time() - self.last_heartbeat > self.heartbeat_interval * 2:
                logger.warning("Connection appears stale based on heartbeat")
                return False

            return True
        except Exception:
            return False

    async def cleanup(self) -> None:
        """Cleanup resources"""
        self.should_run = False
        if self.ws:
            try:
                await self.ws.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
        self.connected = False
        await self.db_manager.cleanup()
        logger.info("WebSocket handler cleaned up")

async def main():
    handler = WebSocketHandler()
    try:
        await handler.initialize()
        if await handler.connect_websocket():
            logger.info("Trading bot started successfully")
            while handler.check_connection():
                await asyncio.sleep(1)
        else:
            logger.error("Failed to establish WebSocket connection")
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        await handler.cleanup()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())