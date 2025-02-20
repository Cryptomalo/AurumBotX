import asyncio
import logging
import nest_asyncio
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
import random
from binance.client import Client
from binance.streams import ThreadedWebsocketManager
from binance.exceptions import BinanceAPIException

# Apply nest_asyncio to handle nested event loops
nest_asyncio.apply()

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
        self.active_streams = set()
        self._loop = asyncio.new_event_loop()
        self._ws_task = None

    async def initialize(self) -> bool:
        """Initialize the WebSocket handler asynchronously"""
        try:
            if self.initialized:
                return True

            logger.info("Initializing WebSocket handler...")
            self.client = Client(self.api_key, self.api_secret, testnet=self.testnet)

            # Initialize WebSocket manager with the new event loop
            asyncio.set_event_loop(self._loop)
            self.twm = ThreadedWebsocketManager(
                api_key=self.api_key,
                api_secret=self.api_secret,
                testnet=self.testnet
            )

            # Start WebSocket manager in a separate task
            self._ws_task = self._loop.create_task(self._start_websocket())
            await asyncio.sleep(1)  # Give it time to establish connection

            self.initialized = True
            self.connected = True
            logger.info("WebSocket handler initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize WebSocket handler: {e}")
            return False

    async def _start_websocket(self):
        """Start WebSocket manager in a separate task"""
        try:
            self.twm.start()
            while self.keep_running:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"WebSocket manager error: {e}")
            self.connected = False
        finally:
            if self.twm and self.twm.is_alive():
                self.twm.stop()

    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self.connected and self.twm and self.twm.is_alive()

    async def test_connection(self) -> bool:
        """Test the WebSocket connection"""
        try:
            if not self.initialized:
                if not await self.initialize():
                    return False

            if not self.is_connected():
                logger.warning("WebSocket not connected, attempting reconnect...")
                if not await self.initialize():
                    return False

            logger.info("WebSocket connection test successful")
            return True

        except Exception as e:
            logger.error(f"WebSocket connection test failed: {e}")
            return False

    async def start(self) -> bool:
        """Start the WebSocket connection"""
        try:
            if not self.initialized:
                await self.initialize()

            if not self.twm or not self.twm.is_alive():
                self.twm = ThreadedWebsocketManager(
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                    testnet=self.testnet
                )
                self._ws_task = self._loop.create_task(self._start_websocket())
                await asyncio.sleep(1)  # Give it time to establish connection

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
                # Unsubscribe from all active streams
                for stream in self.active_streams:
                    try:
                        self.twm.stop_socket(stream)
                    except Exception as e:
                        logger.warning(f"Error unsubscribing from stream {stream}: {e}")

                self.connected = False
                logger.info("WebSocket connection stopped")
                self.active_streams.clear()
        except Exception as e:
            logger.error(f"Error stopping WebSocket connection: {e}")

    async def cleanup(self) -> None:
        """Cleanup WebSocket resources"""
        try:
            self.keep_running = False
            if self._ws_task:
                self._ws_task.cancel()
                try:
                    await self._ws_task
                except asyncio.CancelledError:
                    pass
            if self.twm:
                self.twm.stop()
            self.initialized = False
            self.connected = False
            logger.info("WebSocket handler cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during WebSocket cleanup: {e}")

    def register_handler(self, stream: str, handler: Callable):
        """Register a message handler for a specific stream"""
        if not callable(handler):
            raise ValueError("Handler must be callable")
        self.handlers[stream] = handler
        logger.info(f"Handler registered for stream: {stream}")

    def _message_handler(self, msg: Dict):
        """Handle incoming WebSocket messages"""
        try:
            if msg is None:
                return

            if isinstance(msg, dict) and msg.get('e') == 'error':
                logger.error(f"WebSocket error: {msg.get('m')}")
                self._handle_error(msg)
                return

            # Extract stream name from message if available
            stream = msg.get('stream', '') if isinstance(msg, dict) else ''

            # Pass message to registered handler if exists
            if stream in self.handlers:
                self.handlers[stream](msg)
            else:
                logger.debug(f"No handler registered for stream: {stream}")

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def send_message(self, message: Dict[str, Any]) -> bool:
        """Send a message through WebSocket"""
        if not self.is_connected():
            logger.warning("Not connected, attempting to reconnect...")
            if not await self.reconnect():
                return False

        try:
            # Handle different message types
            msg_type = message.get('type', '')
            symbol = message.get('symbol', '').upper()

            if msg_type == 'subscribe':
                # Subscribe to market data streams
                stream_name = f"{symbol.lower()}@trade"
                self.twm.start_symbol_ticker_socket(
                    symbol=symbol,
                    callback=self._message_handler
                )
                self.active_streams.add(stream_name)
                logger.info(f"Subscribed to stream: {stream_name}")
                return True
            else:
                logger.error(f"Unsupported message type: {msg_type}")
                return False

        except BinanceAPIException as e:
            logger.error(f"Binance API error: {str(e)}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            self.connected = False
            return False

    async def reconnect(self) -> bool:
        """Attempt to reconnect the WebSocket"""
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
            await self.stop()

            # Create new connection
            success = await self.start()

            if success:
                logger.info("Reconnection successful")
                self.last_reconnect = now
                self.reconnect_delay = 1  # Reset delay on success
                self.reconnect_attempts = 0  # Reset attempts on success

                # Resubscribe to active streams
                for stream in self.active_streams.copy():
                    symbol = stream.split('@')[0].upper()
                    self.twm.start_symbol_ticker_socket(
                        symbol=symbol,
                        callback=self._message_handler
                    )

                return True

            # Update state on failure
            self.last_reconnect = now
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

    def _handle_error(self, error_msg: Any):
        """Handle WebSocket error messages"""
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
                asyncio.create_task(self.reconnect())
            elif error_code == 451:  # Authentication error
                logger.critical("Authentication failed. Please check API credentials.")
                self.keep_running = False
                asyncio.create_task(self.stop())
            else:
                logger.warning(f"Unhandled error code: {error_code}")

        except Exception as e:
            logger.error(f"Error handling error message: {str(e)}")