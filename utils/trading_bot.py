import asyncio
import logging
import json
import time
import websockets
import threading
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import openai
from utils.database import DatabaseManager
from utils.indicators import TechnicalIndicators
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class WebSocketHandler:
    def __init__(self, logger: logging.Logger, db: Any):
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connected: bool = False
        self.logger = logger
        self.max_retries: int = 5
        self.retry_delay: int = 1
        self.last_heartbeat: float = time.time()
        self.heartbeat_interval: int = 30
        self.reconnect_lock: threading.Lock = threading.Lock()
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.should_run: bool = True
        self.db = db
        self.last_batch_process: float = time.time()
        self._initialize_db()
        self.technical_indicators: TechnicalIndicators = TechnicalIndicators()
        self._message_buffer: List[Dict] = []
        self.buffer_size: int = 1000
        self.batch_interval: float = 1.0  # seconds
        self.testnet: bool = True  # Add testnet attribute

        # OpenAI setup for error correction
        self.openai_client = openai.OpenAI()

    def _initialize_db(self) -> None:
        """Initialize database connection using DatabaseManager"""
        try:
            if isinstance(self.db, DatabaseManager):
                db_url = os.getenv('DATABASE_URL')
                if not db_url:
                    raise ValueError("DATABASE_URL environment variable not set")

                if not self.db.initialize(db_url):
                    raise Exception("Failed to initialize database connection")

                self.logger.info("Database connection established successfully")
                return

            self.logger.info("Using custom database handler")

        except Exception as e:
            self.logger.error(f"Database initialization error: {str(e)}")
            raise

    async def _preprocess_message(self, msg: Dict) -> Optional[Dict]:
        """Preprocessa i messaggi con validazione"""
        try:
            if not isinstance(msg, dict):
                raise ValueError("Invalid message format")

            required_fields = ['s', 'c', 'v']
            if not all(field in msg for field in required_fields):
                raise ValueError("Missing required fields in message")

            return {
                'symbol': str(msg.get('s', '')),
                'price': float(msg.get('c', 0)),
                'volume': float(msg.get('v', 0)),
                'timestamp': datetime.now().timestamp()
            }
        except Exception as e:
            self.logger.error(f"Message preprocessing error: {str(e)}")
            return None

    async def connect_websocket(self) -> bool:
        """Connette al WebSocket con gestione errori avanzata"""
        try:
            if self.ws:
                await self.ws.close()

            self.ws = await websockets.connect(
                "wss://testnet.binance.vision/ws/!ticker@arr" if self.testnet else "wss://stream.binance.com:9443/ws/!ticker@arr",
                ping_interval=20,
                ping_timeout=20,
                close_timeout=15,
                max_size=2**23,
                compression=None,
                max_queue=2**10,
                extra_headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Origin': 'https://www.binance.com'
                }
            )
            await self._subscribe_channels()
            self.connected = True
            self.last_heartbeat = time.time()

            # Start heartbeat in background
            if not self.heartbeat_thread or not self.heartbeat_thread.is_alive():
                self.heartbeat_thread = threading.Thread(target=self._run_heartbeat, daemon=True)
                self.heartbeat_thread.start()

            # Start message processing
            asyncio.create_task(self._process_messages())

            self.logger.info("WebSocket connection established successfully")
            return True

        except Exception as e:
            error_context = f"WebSocket connection error: {str(e)}"
            fix_suggestion = await self._ai_error_correction(error_context)
            self.logger.error(f"{error_context}\nAI Suggestion: {fix_suggestion}")
            return False

    async def _process_messages(self) -> None:
        """Process incoming WebSocket messages with error handling"""
        while self.connected and self.ws:
            try:
                message = await self.ws.recv()
                await self._on_message(message)
            except websockets.exceptions.ConnectionClosed:
                self.logger.error("WebSocket connection closed unexpectedly")
                self.connected = False
                await self.handle_websocket_error(Exception("Connection closed"))
                break
            except Exception as e:
                self.logger.error(f"Message processing error: {str(e)}")
                await self._ai_error_correction(f"Message processing error: {str(e)}")
                continue

    def _run_heartbeat(self) -> None:
        """Monitor connection health"""
        while self.connected and self.should_run:
            try:
                current_time = time.time()
                if current_time - self.last_heartbeat > self.heartbeat_interval * 2:
                    self.logger.warning("Heartbeat timeout detected, initiating reconnection...")
                    asyncio.run(self.handle_websocket_error(Exception("Heartbeat timeout")))
                time.sleep(self.heartbeat_interval / 2)  # Check twice per interval
            except Exception as e:
                self.logger.error(f"Heartbeat monitoring error: {str(e)}")
                break

    async def handle_websocket_error(self, error: Exception) -> bool:
        """Gestisce errori WebSocket con retry intelligente"""
        retry_count = 0
        current_delay = self.retry_delay

        while retry_count < self.max_retries and self.should_run:
            try:
                self.logger.info(f"Attempting reconnection {retry_count + 1}/{self.max_retries}")
                if await self.connect_websocket():
                    self.logger.info("Reconnection successful")
                    return True

                current_delay = min(current_delay * 2, 30)  # Exponential backoff capped at 30s
                self.logger.info(f"Reconnection failed, waiting {current_delay}s before next attempt")
                await asyncio.sleep(current_delay)
                retry_count += 1

            except Exception as e:
                error_context = f"Reconnection error: {str(e)}"
                fix_suggestion = await self._ai_error_correction(error_context)
                self.logger.error(f"{error_context}\nAI Suggestion: {fix_suggestion}")
                retry_count += 1

        self.logger.critical("Failed to establish WebSocket connection after all retries")
        return False

    async def _ai_error_correction(self, error_context: str) -> str:
        """Usa OpenAI per analisi errori e suggerimenti"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",  # Using stable GPT-4 model
                messages=[{
                    "role": "system",
                    "content": "You are an expert trading bot error analyzer. Analyze the error and suggest fixes."
                }, {
                    "role": "user",
                    "content": f"Trading bot error context:\n{error_context}"
                }],
                temperature=0.7,
                max_tokens=150,
                response_format={"type": "text"}
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"AI error correction failed: {str(e)}")
            return "Error analysis failed"

    async def _on_message(self, message: str) -> None:
        """Process and validate incoming messages"""
        try:
            data = json.loads(message)
            self.last_heartbeat = time.time()

            if len(self._message_buffer) < self.buffer_size:
                self._message_buffer.append(data)

            current_time = time.time()
            if (len(self._message_buffer) >= 10 or
                (current_time - self.last_batch_process) > self.batch_interval):
                await self._process_message_batch(self._message_buffer)
                self._message_buffer = []
                self.last_batch_process = current_time

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decoding error: {str(e)}")
        except Exception as e:
            error_context = f"Message handling error: {str(e)}"
            fix_suggestion = await self._ai_error_correction(error_context)
            self.logger.error(f"{error_context}\nAI Suggestion: {fix_suggestion}")

    async def _process_message_batch(self, messages: List[Dict]) -> None:
        """Process messages in batches with optimized handling"""
        try:
            # Process messages in parallel
            processed_data: List[Dict] = []
            tasks = [self._preprocess_message(msg) for msg in messages]
            processed_msgs = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions and None values
            for msg in processed_msgs:
                if msg is not None and not isinstance(msg, Exception):
                    processed_data.append(msg)

            if processed_data:
                df = pd.DataFrame(processed_data)
                df = self.technical_indicators.add_all_indicators(df)
                await self._analyze_signals(df)
                await self._handle_processed_batch(processed_data)

        except Exception as e:
            error_context = f"Batch processing error: {str(e)}"
            fix_suggestion = await self._ai_error_correction(error_context)
            self.logger.error(f"{error_context}\nAI Suggestion: {fix_suggestion}")

    async def _analyze_signals(self, df: pd.DataFrame) -> None:
        """Analyze market signals with risk management"""
        try:
            signals = self.technical_indicators.get_trading_signals(df)
            if signals:
                self.logger.info(f"Trading signals detected: {signals}")
                # Implement trading logic here
        except Exception as e:
            self.logger.error(f"Signal analysis error: {str(e)}")

    async def _handle_processed_batch(self, processed_data: List[Dict]) -> None:
        """Gestisce il batch processato"""
        try:
            if self.db and processed_data:
                await self.db.insert_many(processed_data)
        except Exception as e:
            self.logger.error(f"Database insertion error: {e}")

    async def _subscribe_channels(self) -> None:
        """Subscribe to required WebSocket channels"""
        try:
            channels = [
                "!ticker@arr",  # All market tickers
                "!miniTicker@arr"  # All market mini tickers
            ]

            for channel in channels:
                subscribe_message = {
                    "method": "SUBSCRIBE",
                    "params": [channel],
                    "id": int(time.time() * 1000)
                }
                await self.ws.send(json.dumps(subscribe_message))
                self.logger.info(f"Subscribed to channel: {channel}")

        except Exception as e:
            self.logger.error(f"Error subscribing to channels: {str(e)}")
            raise

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
        self.logger.info("WebSocket handler cleaned up")

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    class MockDB:
        def connect(self) -> None:
            print("Connecting to mock database...")
            pass
        async def insert_many(self, data: List[Dict]) -> None:
            print(f"Inserting {len(data)} records into mock database...")
            pass

    async def main() -> None:
        db = MockDB()
        handler = WebSocketHandler(logger, db)

        try:
            if await handler.connect_websocket():
                print("WebSocket connection established successfully.")
                # Keep the connection alive
                while handler.check_connection():
                    await asyncio.sleep(1)
            else:
                print("Failed to establish WebSocket connection.")
        except KeyboardInterrupt:
            print("Shutting down...")
            await handler.cleanup()
        except Exception as e:
            print(f"Error: {str(e)}")
            await handler.cleanup()

    asyncio.run(main())