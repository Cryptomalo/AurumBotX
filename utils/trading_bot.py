import asyncio
import logging
import json
import time
import websocket
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
        self.openai_client = openai.OpenAI()

    def _ai_error_correction(self, error_context: str) -> str:
        """Usa OpenAI per analizzare e correggere errori"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",  # Using latest model
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
            return None

    def connect_websocket(self):
        """Connette al WebSocket con gestione errori migliorata"""
        try:
            if self.ws:
                self.ws.close()

            websocket.enableTrace(True)
            self.ws = websocket.WebSocketApp(
                "wss://stream.binance.com:9443/ws/!ticker@arr",
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )

            self.ws_thread = threading.Thread(target=self.ws.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()

            return True
        except Exception as e:
            error_context = f"Connection error: {str(e)}"
            fix_suggestion = self._ai_error_correction(error_context)
            self.logger.error(f"{error_context}\nAI Suggestion: {fix_suggestion}")
            return False

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            self.last_heartbeat = time.time()

            if not hasattr(self, '_message_buffer'):
                self._message_buffer = []

            if len(self._message_buffer) < 1000:
                self._message_buffer.append(data)

            if len(self._message_buffer) >= 10 or (time.time() - self.last_batch_process) > 1.0:
                self._process_message_batch(self._message_buffer)
                self._message_buffer = []
                self.last_batch_process = time.time()

        except Exception as e:
            error_context = f"Message processing error: {str(e)}"
            fix_suggestion = self._ai_error_correction(error_context)
            self.logger.error(f"{error_context}\nAI Suggestion: {fix_suggestion}")

    def _process_message_batch(self, messages):
        """Processa messaggi in batch con analisi tecnica avanzata"""
        try:
            # Preprocessa i dati
            processed_data = [self._preprocess_message(msg) for msg in messages]

            # Analisi tecnica in tempo reale
            df = pd.DataFrame(processed_data)
            if not df.empty:
                df = self.technical_indicators.add_all_indicators(df)
                self._analyze_signals(df)

            # Salva nel database
            self._handle_processed_batch(processed_data)

        except Exception as e:
            error_context = f"Batch processing error: {str(e)}"
            fix_suggestion = self._ai_error_correction(error_context)
            self.logger.error(f"{error_context}\nAI Suggestion: {fix_suggestion}")

    def _analyze_signals(self, df: pd.DataFrame):
        """Analizza segnali di trading in tempo reale"""
        try:
            signals = self.technical_indicators.get_trading_signals(df)
            if signals:
                self.logger.info(f"Trading signals detected: {signals}")
                # Implementa qui la logica di trading basata sui segnali
        except Exception as e:
            self.logger.error(f"Signal analysis error: {e}")

    def _preprocess_message(self, msg):
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

    def _handle_processed_batch(self, processed_data):
        """Gestisce il batch processato"""
        try:
            if self.db and processed_data:
                self.db.insert_many(processed_data)
        except Exception as e:
            self.logger.error(f"Database insertion error: {e}")

    def _initialize_db(self):
        """Inizializza la connessione al database"""
        retries = 3
        while retries > 0:
            try:
                self.db.connect()
                break
            except Exception as e:
                retries -= 1
                self.logger.error(f"Database connection error: {str(e)}")
                if retries > 0:
                    time.sleep(5)

    def check_connection(self):
        """Verifica stato connessione"""
        try:
            return self.ws and self.ws.sock and self.ws.sock.connected
        except:
            return False

    def setup_heartbeat(self):
        """Configura heartbeat per mantenere connessione"""
        def heartbeat():
            while self.check_connection():
                try:
                    if self.ws and hasattr(self.ws, 'sock'):
                        self.ws.sock.ping()
                    time.sleep(30)
                except Exception as e:
                    self.logger.error(f"Heartbeat error: {str(e)}")
                    break

        if self.heartbeat_thread is None or not self.heartbeat_thread.is_alive():
            self.heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
            self.heartbeat_thread.start()

    def handle_websocket_error(self, error):
        """Gestisce errori WebSocket con retry intelligente"""
        retry_count = 0
        current_delay = self.retry_delay

        while retry_count < self.max_retries:
            try:
                self.logger.info(f"Tentativo riconnessione {retry_count + 1}/{self.max_retries}")
                if self.connect_websocket():
                    self.setup_heartbeat()
                    return True

                current_delay = min(current_delay * 2, 30)  # Exponential backoff
                time.sleep(current_delay)
                retry_count += 1

            except Exception as e:
                error_context = f"Reconnection error: {str(e)}"
                fix_suggestion = self._ai_error_correction(error_context)
                self.logger.error(f"{error_context}\nAI Suggestion: {fix_suggestion}")
                retry_count += 1

        self.logger.critical("Failed to establish WebSocket connection after all retries")
        return False


# Example usage (adapt to your application)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Replace with your actual database object
class MockDB:
    def connect(self):
        print("Connecting to mock database...")
        pass
    def insert_many(self,data):
        print(f"Inserting {len(data)} records into mock database...")
        pass

db = MockDB()
websocket_handler = WebSocketHandler(logger, db)
if websocket_handler.connect_websocket():
    print("WebSocket connection established successfully.")
else:
    print("Failed to establish WebSocket connection.")