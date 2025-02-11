import asyncio
import logging
import json
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

        # Setup Binance client
        self.client = Client(self.api_key, self.api_secret, testnet=self.testnet)
        self.bm = BinanceSocketManager(self.client)
        self.conn_key = None

    def setup_socket(self):
        """Setup WebSocket with proper error handling"""
        try:
            # Close existing connection if any
            if self.conn_key:
                self.bm.stop_socket(self.conn_key)

            # Start new connection
            self.conn_key = self.bm.start_multiplex_socket(
                ['btcusdt@trade', 'btcusdt@depth'], self._message_handler
            )
            self.bm.start()
            self.connected = True
            logger.info("WebSocket connection established successfully")
            return True

        except BinanceAPIException as e:
            logger.error(f"Binance API error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"WebSocket setup error: {str(e)}")
            return False

    def _message_handler(self, msg: Dict):
        """Handle incoming messages with error recovery"""
        try:
            if msg.get('e') == 'error':
                logger.error(f"WebSocket error: {msg.get('m')}")
                self._handle_error(msg)
                return

            stream = msg.get('stream', '')
            if stream in self.handlers:
                try:
                    self.handlers[stream](msg.get('data', {}))
                except Exception as e:
                    logger.error(f"Handler error for {stream}: {str(e)}")
        except Exception as e:
            logger.error(f"Message handling error: {str(e)}")

    def _handle_error(self, error_msg: Dict):
        """Handle WebSocket errors with recovery logic"""
        try:
            error_code = error_msg.get('code', 0)
            if error_code in [1002, 1006, 1012]:  # Connection errors
                logger.warning(f"Connection error {error_code}, attempting reconnect...")
                self.reconnect()
            elif error_code == 451:  # Authentication error
                logger.error("Authentication failed. Please check API credentials.")
                self.stop()
            else:
                logger.warning(f"Unhandled error code: {error_code}")
        except Exception as e:
            logger.error(f"Error handling error: {str(e)}")

    def reconnect(self):
        """Handle reconnection with exponential backoff"""
        if not self.keep_running:
            return False

        now = datetime.now()
        if now - self.last_reconnect < timedelta(seconds=self.reconnect_delay):
            return False

        try:
            logger.info(f"Attempting to reconnect... (delay: {self.reconnect_delay}s)")
            success = self.setup_socket()

            if success:
                logger.info("Reconnection successful")
                self.last_reconnect = now
                self.reconnect_delay = 1  # Reset delay
                return True

            # Exponential backoff
            self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
            self.last_reconnect = now
            return False

        except Exception as e:
            logger.error(f"Reconnection failed: {str(e)}")
            self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
            return False

    def register_handler(self, stream: str, handler: Callable):
        """Register a handler for specific streams"""
        self.handlers[stream] = handler
        logger.info(f"Handler registered for stream: {stream}")

    def start(self):
        """Start WebSocket connection"""
        if self.setup_socket():
            logger.info("WebSocket started successfully")
            return True
        return False

    def stop(self):
        """Clean shutdown of WebSocket connection"""
        try:
            self.keep_running = False
            if self.conn_key:
                self.bm.stop_socket(self.conn_key)
            self.bm.close()
            self.connected = False
            logger.info("WebSocket connection closed cleanly")
        except Exception as e:
            logger.error(f"Error closing WebSocket: {str(e)}")

    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self.connected

    async def send_message(self, message: Dict[str, Any]) -> bool:
        """Send message with retry logic"""
        if not self.connected:
            if not self.reconnect():
                return False

        try:
            # Convert message to JSON string
            msg_str = json.dumps(message)

            # Use Binance client to send message
            if hasattr(self.client, 'send_message'):
                await self.client.send_message(msg_str)
                return True
            else:
                logger.error("Message sending not supported by current client")
                return False

        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            self.connected = False
            return False