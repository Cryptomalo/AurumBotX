import asyncio
import logging
import json
import time
import websockets
import threading
from datetime import datetime
from typing import Dict, List, Optional
import openai
from utils.database import get_db
from utils.indicators import TechnicalIndicators
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class WebSocketHandler:
    def __init__(self, logger, db):
        self.ws = None
        self.connected = False
        self.logger = logger
        self.max_retries = 5
        self.retry_delay = 1
        self.last_heartbeat = time.time()
        self.heartbeat_interval = 30
        self.reconnect_lock = threading.Lock()
        self.heartbeat_thread = None
        self.should_run = True
        self.db = db
        self.last_batch_process = time.time()
        self._initialize_db()
        self.technical_indicators = TechnicalIndicators()

        # OpenAI setup for error correction
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        self.openai_client = openai.OpenAI()

    def _initialize_db(self):
        """Inizializza la connessione al database"""
        retries = 3
        while retries > 0:
            try:
                if hasattr(self.db, 'connect'):
                    self.db.connect()
                break
            except Exception as e:
                retries -= 1
                self.logger.error(f"Database connection error: {str(e)}")
                if retries > 0:
                    time.sleep(5)

    async def _preprocess_message(self, msg):
        """Preprocessa i messaggi raw"""
        try:
            return {
                'symbol': msg.get('s', ''),
                'price': float(msg.get('c', 0)),
                'volume': float(msg.get('v', 0)),
                'timestamp': datetime.now().timestamp()
            }
        except Exception as e:
            self.logger.error(f"Preprocessing error: {e}")
            return None

    async def _handle_processed_batch(self, processed_data):
        """Gestisce il batch processato"""
        try:
            if self.db and processed_data:
                await self.db.insert_many(processed_data)
        except Exception as e:
            self.logger.error(f"Database insertion error: {e}")

    async def connect_websocket(self):
        """Connette al WebSocket con gestione errori migliorata"""
        try:
            if self.ws:
                await self.ws.close()

            self.ws = await websockets.connect(
                "wss://stream.binance.com:9443/ws/!ticker@arr",
                ping_interval=20,
                ping_timeout=10
            )
            self.connected = True

            # Start heartbeat
            if not self.heartbeat_thread or not self.heartbeat_thread.is_alive():
                self.heartbeat_thread = threading.Thread(target=self._run_heartbeat, daemon=True)
                self.heartbeat_thread.start()

            # Start message processing
            asyncio.create_task(self._process_messages())

            return True
        except Exception as e:
            error_context = f"Connection error: {str(e)}"
            fix_suggestion = await self._ai_error_correction(error_context)
            self.logger.error(f"{error_context}\nAI Suggestion: {fix_suggestion}")
            return False

    async def _ai_error_correction(self, error_context: str) -> str:
        """Usa OpenAI per analizzare e correggere errori"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",  # Latest model as of May 2024
                messages=[{
                    "role": "system",
                    "content": "You are an expert trading bot error analyzer. Analyze the error and suggest fixes."
                }, {
                    "role": "user",
                    "content": f"Trading bot error context:\n{error_context}"
                }],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"AI error correction failed: {e}")
            return "Error analysis failed"

    async def _process_messages(self):
        """Process incoming WebSocket messages"""
        while self.connected:
            try:
                message = await self.ws.recv()
                await self._on_message(message)
            except websockets.exceptions.ConnectionClosed:
                self.logger.error("WebSocket connection closed")
                self.connected = False
                await self.handle_websocket_error(Exception("Connection closed"))
                break
            except Exception as e:
                self.logger.error(f"Message processing error: {e}")
                continue

    def _run_heartbeat(self):
        """Run heartbeat in a separate thread"""
        while self.connected:
            try:
                time.sleep(self.heartbeat_interval)
                if time.time() - self.last_heartbeat > self.heartbeat_interval * 2:
                    self.logger.warning("Heartbeat timeout, reconnecting...")
                    asyncio.run(self.handle_websocket_error(Exception("Heartbeat timeout")))
            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")
                break

    async def handle_websocket_error(self, error):
        """Gestisce errori WebSocket con retry intelligente"""
        retry_count = 0
        current_delay = self.retry_delay

        while retry_count < self.max_retries:
            try:
                self.logger.info(f"Tentativo riconnessione {retry_count + 1}/{self.max_retries}")
                if await self.connect_websocket():
                    return True

                current_delay = min(current_delay * 2, 30)  # Exponential backoff
                await asyncio.sleep(current_delay)
                retry_count += 1

            except Exception as e:
                error_context = f"Reconnection error: {str(e)}"
                fix_suggestion = await self._ai_error_correction(error_context)
                self.logger.error(f"{error_context}\nAI Suggestion: {fix_suggestion}")
                retry_count += 1

        self.logger.critical("Failed to establish WebSocket connection after all retries")
        return False

    async def _on_message(self, message):
        try:
            data = json.loads(message)
            self.last_heartbeat = time.time()

            if not hasattr(self, '_message_buffer'):
                self._message_buffer = []

            if len(self._message_buffer) < 1000:
                self._message_buffer.append(data)

            if len(self._message_buffer) >= 10 or (time.time() - self.last_batch_process) > 1.0:
                await self._process_message_batch(self._message_buffer)
                self._message_buffer = []
                self.last_batch_process = time.time()

        except Exception as e:
            error_context = f"Message processing error: {str(e)}"
            fix_suggestion = await self._ai_error_correction(error_context)
            self.logger.error(f"{error_context}\nAI Suggestion: {fix_suggestion}")

    async def _process_message_batch(self, messages):
        """Processa messaggi in batch con analisi tecnica avanzata"""
        try:
            processed_data = []
            for msg in messages:
                processed_msg = await self._preprocess_message(msg)
                if processed_msg:
                    processed_data.append(processed_msg)

            if processed_data:
                df = pd.DataFrame(processed_data)
                df = self.technical_indicators.add_all_indicators(df)
                await self._analyze_signals(df)
                await self._handle_processed_batch(processed_data)

        except Exception as e:
            error_context = f"Batch processing error: {str(e)}"
            fix_suggestion = await self._ai_error_correction(error_context)
            self.logger.error(f"{error_context}\nAI Suggestion: {fix_suggestion}")

    async def _analyze_signals(self, df: pd.DataFrame):
        """Analizza segnali di trading in tempo reale"""
        try:
            signals = self.technical_indicators.get_trading_signals(df)
            if signals:
                self.logger.info(f"Trading signals detected: {signals}")
                # Implementa qui la logica di trading basata sui segnali
        except Exception as e:
            self.logger.error(f"Signal analysis error: {e}")

    def check_connection(self):
        """Verifica stato connessione"""
        try:
            return self.ws and self.connected
        except:
            return False

    def setup_heartbeat(self): #Removed the async keyword as it's run in a thread
        """Configura heartbeat per mantenere connessione"""
        while self.check_connection():
            try:
                if self.ws and hasattr(self.ws, 'ping'):
                    asyncio.run(self.ws.ping())
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                self.logger.error(f"Heartbeat error: {str(e)}")
                break


# Example usage (adapt to your application)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Replace with your actual database object
class MockDB:
    def connect(self):
        print("Connecting to mock database...")
        pass
    async def insert_many(self,data):
        print(f"Inserting {len(data)} records into mock database...")
        pass

db = MockDB()
websocket_handler = WebSocketHandler(logger, db)

async def main():
    if await websocket_handler.connect_websocket():
        print("WebSocket connection established successfully.")
    else:
        print("Failed to establish WebSocket connection.")

asyncio.run(main())