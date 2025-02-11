import asyncio
import logging
import json
import random
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.exceptions import BinanceAPIException
import websocket

logger = logging.getLogger(__name__)

class WebSocketHandler:
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = True):
        """Initialize WebSocket handler with improved retry mechanism"""
        self.api_key = api_key or ""
        self.api_secret = api_secret or ""
        self.testnet = testnet
        self.ws: Optional[websocket.WebSocketApp] = None
        self.connected = False
        self.last_reconnect = datetime.now()
        self.reconnect_delay = 1  # Start with 1 second delay
        self.max_reconnect_delay = 60  # Maximum 60 seconds between retries
        self.handlers: Dict[str, Callable] = {}
        self.keep_running = True
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10

        # Setup Binance client
        self.client = Client(self.api_key, self.api_secret, testnet=self.testnet)
        self.bm = BinanceSocketManager(self.client)
        self.conn_key = None

    def setup_socket(self):
        """Setup WebSocket with proper error handling and authentication"""
        try:
            logger.info("Setting up WebSocket connection...")
            # Close existing connection if any
            if self.conn_key:
                self.bm.stop_socket(self.conn_key)
                logger.debug("Closed existing WebSocket connection")

            if not self.api_key or not self.api_secret:
                logger.warning("No API credentials provided, some features may be limited")

            # Start new connection with improved error handling
            self.conn_key = self.bm.start_multiplex_socket(
                ['btcusdt@trade', 'btcusdt@depth'],
                self._message_handler
            )
            self.bm.start()

            self.connected = True
            self.reconnect_attempts = 0  # Reset counter on successful connection
            logger.info("WebSocket connection established successfully")
            return True

        except BinanceAPIException as e:
            logger.error(f"Binance API error: {str(e)}")
            if "Invalid API-key" in str(e):
                logger.critical("Authentication failed - please check your API credentials")
                self.keep_running = False  # Stop reconnection attempts
            return False
        except Exception as e:
            logger.error(f"WebSocket setup error: {str(e)}")
            return False

    def _message_handler(self, msg: Dict):
        """Handle incoming messages with comprehensive error recovery"""
        try:
            logger.debug(f"Received message: {msg.get('e', 'unknown_event')}")

            if isinstance(msg, dict) and msg.get('e') == 'error':
                logger.error(f"WebSocket error message: {msg.get('m')}")
                self._handle_error(msg)
                return

            stream = msg.get('stream', '')
            if stream in self.handlers:
                try:
                    self.handlers[stream](msg.get('data', {}))
                except Exception as e:
                    logger.error(f"Handler error for stream {stream}: {str(e)}")
            else:
                logger.debug(f"No handler registered for stream: {stream}")

        except Exception as e:
            logger.error(f"Message handling error: {str(e)}")

    def _handle_error(self, error_msg: Any):
        """Enhanced error handling with specific error codes"""
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
                self.reconnect()
            elif error_code == 451:  # Authentication error
                logger.critical("Authentication failed. Please check API credentials.")
                self.keep_running = False
                self.stop()
            else:
                logger.warning(f"Unhandled error code: {error_code}")

        except Exception as e:
            logger.error(f"Error handling error: {str(e)}")

    def reconnect(self):
        """Advanced reconnection logic with exponential backoff"""
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
            success = self.setup_socket()

            if success:
                logger.info("Reconnection successful")
                self.last_reconnect = now
                self.reconnect_delay = 1  # Reset delay
                return True

            # Exponential backoff with jitter
            jitter = random.uniform(0, 0.1) * self.reconnect_delay
            self.reconnect_delay = min(self.reconnect_delay * 2 + jitter, self.max_reconnect_delay)
            self.reconnect_attempts += 1
            self.last_reconnect = now

            logger.warning(f"Reconnection failed. Next attempt in {self.reconnect_delay:.1f}s")
            return False

        except Exception as e:
            logger.error(f"Reconnection attempt failed: {str(e)}")
            self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
            self.reconnect_attempts += 1
            return False

    def register_handler(self, stream: str, handler: Callable):
        """Register a handler for specific streams with validation"""
        if not callable(handler):
            raise ValueError("Handler must be callable")
        self.handlers[stream] = handler
        logger.info(f"Handler registered for stream: {stream}")

    def start(self):
        """Start WebSocket connection with verification"""
        if self.setup_socket():
            logger.info("WebSocket started successfully")
            return True
        return False

    def stop(self):
        """Clean shutdown of WebSocket connection"""
        try:
            logger.info("Initiating WebSocket shutdown...")
            self.keep_running = False
            if self.conn_key:
                self.bm.stop_socket(self.conn_key)
            self.bm.close()
            self.connected = False
            logger.info("WebSocket connection closed cleanly")
        except Exception as e:
            logger.error(f"Error during WebSocket shutdown: {str(e)}")

    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self.connected

    async def send_message(self, message: Dict[str, Any]) -> bool:
        """Send message with improved error handling and retry logic"""
        if not self.connected:
            logger.warning("Not connected, attempting to reconnect...")
            if not self.reconnect():
                return False

        try:
            msg_str = json.dumps(message)
            logger.debug(f"Sending message: {msg_str[:100]}...")

            if hasattr(self.client, 'send_message'):
                await self.client.send_message(msg_str)
                return True
            else:
                logger.error("Message sending not supported by current client")
                self.connected = False
                return False

        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            self.connected = False
            return False