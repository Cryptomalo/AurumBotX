import asyncio
import logging
import websockets
import json
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class WebSocketHandler:
    def __init__(self, url: str, api_key: Optional[str] = None):
        """Initialize WebSocket handler with retry mechanism"""
        self.url = url
        self.api_key = api_key
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.last_reconnect = datetime.now()
        self.reconnect_delay = 1  # Start with 1 second delay
        self.max_reconnect_delay = 60  # Maximum 60 seconds between retries
        self.handlers: Dict[str, Callable] = {}

        # Additional configurations for robust connection
        self.ping_interval = 20
        self.ping_timeout = 10
        self.close_timeout = 5

    async def connect(self) -> bool:
        """Establish WebSocket connection with retry logic"""
        try:
            # Enhanced headers with additional authentication
            headers = {
                "User-Agent": "AurumBot/1.0",
                "Accept": "application/json",
                "Connection": "keep-alive"
            }

            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self.ws = await websockets.connect(
                self.url,
                extra_headers=headers,
                ping_interval=self.ping_interval,
                ping_timeout=self.ping_timeout,
                close_timeout=self.close_timeout,
                max_size=10 * 1024 * 1024  # 10MB max message size
            )

            self.connected = True
            self.reconnect_delay = 1  # Reset delay on successful connection
            logger.info("WebSocket connection established successfully")
            return True

        except websockets.exceptions.InvalidStatusCode as e:
            if e.status_code == 451:
                logger.error(f"Access denied (HTTP 451). Checking API key validity...")
                return False
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            return False

    async def reconnect(self) -> bool:
        """Handle reconnection with exponential backoff"""
        now = datetime.now()

        # Prevent too frequent reconnection attempts
        if now - self.last_reconnect < timedelta(seconds=self.reconnect_delay):
            return False

        try:
            logger.info(f"Attempting to reconnect... (delay: {self.reconnect_delay}s)")
            success = await self.connect()

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

    async def listen(self):
        """Listen for messages with automatic reconnection"""
        while True:
            try:
                if not self.connected or not self.ws:
                    if not await self.reconnect():
                        await asyncio.sleep(self.reconnect_delay)
                        continue

                logger.info("Starting to listen for messages...")  # Added connection status log
                async for message in self.ws:
                    try:
                        data = json.loads(message)
                        logger.debug(f"Raw message received: {message[:200]}...")  # Added raw message logging
                        await self._handle_message(data)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON received: {message}")
                    except Exception as e:
                        logger.error(f"Error handling message: {str(e)}")

            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"WebSocket connection closed: {str(e)}")
                self.connected = False
                continue

            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                self.connected = False
                await asyncio.sleep(self.reconnect_delay)

    async def send(self, message: Dict[str, Any]) -> bool:
        """Send message with retry logic"""
        if not self.connected or not self.ws:
            if not await self.reconnect():
                return False

        try:
            await self.ws.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            self.connected = False
            return False

    def register_handler(self, message_type: str, handler: Callable):
        """Register a handler for specific message types"""
        self.handlers[message_type] = handler

    async def _handle_message(self, data: Dict[str, Any]):
        """Route messages to appropriate handlers"""
        try:
            logger.info(f"Received message: {data}")  # Added detailed logging
            message_type = data.get('type')
            if message_type in self.handlers:
                try:
                    await self.handlers[message_type](data)
                except Exception as e:
                    logger.error(f"Handler error for {message_type}: {str(e)}")
            else:
                logger.debug(f"No handler for message type: {message_type}")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")

    async def close(self):
        """Clean shutdown of WebSocket connection"""
        if self.ws:
            try:
                await self.ws.close()
                logger.info("WebSocket connection closed cleanly")
            except Exception as e:
                logger.error(f"Error closing WebSocket: {str(e)}")
            finally:
                self.connected = False
                self.ws = None