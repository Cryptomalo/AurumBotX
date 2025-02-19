import asyncio
import logging
import json
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
import random
from binance.client import Client
from binance.streams import ThreadedWebsocketManager
from binance.exceptions import BinanceAPIException

logger = logging.getLogger(__name__)

class WebSocketHandler:
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.connected = False
        self.handlers = {}
        self.twm = None
        self.last_reconnect = datetime.now()
        self.reconnect_delay = 1
        self.max_reconnect_delay = 60
        self.keep_running = True
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.initialized = False

    async def initialize(self) -> bool:
        """Initialize the WebSocket handler asynchronously"""
        try:
            if self.initialized:
                return True

            self.client = Client(self.api_key, self.api_secret, testnet=self.testnet)
            await self._init_websocket_manager()
            self.initialized = True
            logger.info("WebSocket handler initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket handler: {e}")
            return False

    async def _init_websocket_manager(self) -> None:
        """Initialize WebSocket manager asynchronously"""
        try:
            self.twm = ThreadedWebsocketManager(
                api_key=self.api_key,
                api_secret=self.api_secret,
                testnet=self.testnet
            )
            logger.info("WebSocket manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket manager: {e}")
            raise

    async def test_connection(self) -> bool:
        """Test the WebSocket connection"""
        try:
            if not self.initialized:
                await self.initialize()

            if not self.is_connected():
                success = await self.start()
                if not success:
                    return False

            # Test the connection by sending a ping
            test_message = {"method": "ping"}
            success = await self.send_message(test_message)

            if success:
                logger.info("WebSocket connection test successful")
                return True

            logger.error("WebSocket connection test failed")
            return False

        except Exception as e:
            logger.error(f"WebSocket connection test failed: {e}")
            return False

    async def start(self) -> bool:
        """Start the WebSocket connection"""
        try:
            if not self.initialized:
                await self.initialize()

            if self.twm is None:
                await self._init_websocket_manager()

            self.twm.start()
            self.connected = True
            logger.info("WebSocket connection started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start WebSocket connection: {e}")
            return False

    async def stop(self) -> None:
        """Stop the WebSocket connection"""
        try:
            if self.twm:
                self.twm.stop()
                self.connected = False
                logger.info("WebSocket connection stopped")
        except Exception as e:
            logger.error(f"Error stopping WebSocket connection: {e}")

    async def cleanup(self) -> None:
        """Cleanup WebSocket resources"""
        try:
            self.keep_running = False
            await self.stop()
            self.initialized = False
            logger.info("WebSocket handler cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during WebSocket cleanup: {e}")

    def register_handler(self, stream: str, handler: Callable):
        if not callable(handler):
            raise ValueError("Handler must be callable")
        self.handlers[stream] = handler
        logger.info(f"Handler registered for stream: {stream}")

    def _message_handler(self, msg: Dict):
        try:
            if msg.get('e') == 'error':
                logger.error(f"WebSocket error: {msg.get('m')}")
                self._handle_error(msg)
                return

            stream = msg.get('stream', '')
            if stream in self.handlers:
                self.handlers[stream](msg.get('data', {}))

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def _handle_error(self, error_msg: Any):
        try:
            if isinstance(error_msg, dict):
                error_code = error_msg.get('code', 0)
                error_msg = error_msg.get('msg', str(error_msg))
            else:
                error_code = 0
                logger.error(f"Non-dict error message received: {error_msg}")

            logger.error(f"WebSocket error {error_code}: {error_msg}")

            if error_code in [1002, 1006, 1012]:  # Connection errors
                logger.warning(f"Connection error {error_code}, attempting reconnect...")
                asyncio.create_task(self.reconnect()) #Use asyncio.create_task for asynchronous reconnect
            elif error_code == 451:  # Authentication error
                logger.critical("Authentication failed. Please check API credentials.")
                self.keep_running = False
                asyncio.create_task(self.stop()) #Use asyncio.create_task for asynchronous stop
            else:
                logger.warning(f"Unhandled error code: {error_code}")

        except Exception as e:
            logger.error(f"Error handling error: {str(e)}")

    async def reconnect(self):
        if not self.keep_running:
            logger.info("Reconnection stopped - service is shutting down")
            return False

        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.critical(f"Maximum reconnection attempts ({self.max_reconnect_attempts}) reached")
            self.keep_running = False
            return False

        now = datetime.now()
        if now - self.last_reconnect < timedelta(seconds=self.reconnect_delay):
            logger.debug(f"Waiting {self.reconnect_delay}s before next reconnection attempt")
            return False

        try:
            logger.info(f"Attempting to reconnect... (attempt {self.reconnect_attempts + 1}/{self.max_reconnect_attempts})")

            # Stop existing connection
            if hasattr(self, 'twm') and self.twm:
                try:
                    self.twm.stop()
                except Exception as e:
                    logger.warning(f"Error stopping existing connection: {e}")

            # Create new connection
            await self._init_websocket_manager()

            # Reset connection state before attempting reconnection
            self.connected = False

            # Attempt reconnection
            success = await self.start()

            if success:
                logger.info("Reconnection successful")
                self.last_reconnect = now
                self.reconnect_delay = 1  # Reset delay on success
                self.reconnect_attempts = 0 # Reset attempts on success
                return True

            # Update state on failure
            self.last_reconnect = now
            # Exponential backoff with jitter
            jitter = random.uniform(0, 0.1) * self.reconnect_delay
            self.reconnect_delay = min(self.reconnect_delay * 2 + jitter, self.max_reconnect_delay)
            logger.warning(f"Reconnection failed. Next attempt in {self.reconnect_delay:.1f}s")
            self.reconnect_attempts += 1
            return False

        except Exception as e:
            logger.error(f"Reconnection attempt failed: {str(e)}")
            self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
            self.last_reconnect = now
            return False

    def is_connected(self) -> bool:
        return self.connected and hasattr(self, 'twm') and self.twm and self.twm.is_alive()

    async def send_message(self, message: Dict[str, Any]) -> bool:
        if not self.is_connected():
            logger.warning("Not connected, attempting to reconnect...")
            if not await self.reconnect(): #Await the async reconnect function
                return False

        try:
            msg_str = json.dumps(message)
            logger.debug(f"Sending message: {msg_str[:100]}...")

            if self.twm and self.twm.is_alive():
                self.twm._send_message(msg_str)
                return True
            else:
                logger.error("ThreadedWebsocketManager is not alive")
                self.connected = False
                return False

        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            self.connected = False
            return False