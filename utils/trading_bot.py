import asyncio
import logging
import json
import time
import websockets
import threading
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from utils.models import TradingData, get_database_session
from utils.indicators import TechnicalIndicators

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
        self.db_session = get_database_session()
        self.last_batch_process: float = time.time()
        self.technical_indicators = TechnicalIndicators()
        self._message_buffer: List[Dict] = []
        self.buffer_size: int = 1000
        self.batch_interval: float = 1.0
        self.testnet: bool = True

    async def connect_websocket(self) -> bool:
        """Connect to WebSocket with error handling"""
        try:
            if self.ws:
                await self.ws.close()

            ws_url = "wss://testnet.binance.vision/ws/!ticker@arr" if self.testnet else "wss://stream.binance.com:9443/ws/!ticker@arr"

            self.ws = await websockets.connect(
                ws_url,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=15,
                max_size=2**23,
                compression=None,
                max_queue=2**10
            )

            await self._subscribe_channels()
            self.connected = True
            self.last_heartbeat = time.time()

            if not self.heartbeat_thread or not self.heartbeat_thread.is_alive():
                self.heartbeat_thread = threading.Thread(target=self._run_heartbeat, daemon=True)
                self.heartbeat_thread.start()

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
                logger.error("WebSocket connection closed unexpectedly")
                self.connected = False
                await self.handle_websocket_error()
                break
            except Exception as e:
                logger.error(f"Message processing error: {str(e)}")
                continue

    def _run_heartbeat(self) -> None:
        """Monitor connection health"""
        while self.connected and self.should_run:
            try:
                current_time = time.time()
                if current_time - self.last_heartbeat > self.heartbeat_interval * 2:
                    logger.warning("Heartbeat timeout detected")
                    asyncio.run(self.handle_websocket_error())
                time.sleep(self.heartbeat_interval / 2)
            except Exception as e:
                logger.error(f"Heartbeat monitoring error: {str(e)}")
                break

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
                logger.info(f"Reconnection failed, waiting {current_delay}s")
                await asyncio.sleep(current_delay)
                retry_count += 1

            except Exception as e:
                logger.error(f"Reconnection error: {str(e)}")
                retry_count += 1

        logger.critical("Failed to establish WebSocket connection after all retries")
        return False

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
            logger.error(f"JSON decoding error: {str(e)}")
        except Exception as e:
            logger.error(f"Message handling error: {str(e)}")

    async def _process_message_batch(self, messages: List[Dict]) -> None:
        """Process messages in batches"""
        try:
            processed_data = []
            for msg in messages:
                if isinstance(msg, dict) and all(k in msg for k in ['s', 'c', 'v']):
                    processed_data.append({
                        'symbol': str(msg['s']),
                        'price': float(msg['c']),
                        'volume': float(msg['v']),
                        'timestamp': datetime.now()
                    })

            if processed_data:
                df = pd.DataFrame(processed_data)
                df = self.technical_indicators.add_all_indicators(df)
                await self._analyze_signals(df)
                await self._save_to_database(processed_data)

        except Exception as e:
            logger.error(f"Batch processing error: {str(e)}")

    async def _analyze_signals(self, df: pd.DataFrame) -> None:
        """Analyze market signals"""
        try:
            signals = self.technical_indicators.get_trading_signals(df)
            if signals:
                logger.info(f"Trading signals detected: {signals}")
        except Exception as e:
            logger.error(f"Signal analysis error: {str(e)}")

    async def _save_to_database(self, processed_data: List[Dict]) -> None:
        """Save data to database"""
        try:
            for data in processed_data:
                trading_data = TradingData(
                    symbol=data['symbol'],
                    price=data['price'],
                    volume=data['volume'],
                    timestamp=data['timestamp']
                )
                self.db_session.add(trading_data)
            self.db_session.commit()
            logger.info(f"Successfully saved {len(processed_data)} records")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Database error: {str(e)}")

    async def _subscribe_channels(self) -> None:
        """Subscribe to WebSocket channels"""
        try:
            channels = ["!ticker@arr", "!miniTicker@arr"]
            for channel in channels:
                subscribe_message = {
                    "method": "SUBSCRIBE",
                    "params": [channel],
                    "id": int(time.time() * 1000)
                }
                await self.ws.send(json.dumps(subscribe_message))
                logger.info(f"Subscribed to channel: {channel}")
        except Exception as e:
            logger.error(f"Channel subscription error: {str(e)}")
            raise

    def check_connection(self) -> bool:
        """Check connection status"""
        return bool(self.ws and self.connected)

    async def cleanup(self) -> None:
        """Cleanup resources"""
        self.should_run = False
        if self.ws:
            await self.ws.close()
        self.connected = False
        if self.db_session:
            self.db_session.close()
        logger.info("WebSocket handler cleaned up")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    class MockDB:
        def __init__(self, engine):
            self.engine = engine
            self.Session = scoped_session(sessionmaker(bind=self.engine))

        async def insert_many(self, session, data: List[Dict]) -> None:
            print(f"Inserting {len(data)} records into mock database...")
            # Replace with actual database insertion logic using the session
            pass

    async def main() -> None:
        db_url = os.getenv('DATABASE_URL', 'sqlite:///:memory:') #default to in memory DB if env var not set.
        engine = create_engine(db_url)
        Base.metadata.create_all(engine) #added line to create tables
        db = MockDB(engine)
        handler = WebSocketHandler()

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