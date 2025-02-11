import time
import threading
import logging

class WebSocketHandler:
    def __init__(self, logger):
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


    def connect_websocket(self):
        try:
            if self.ws:
                self.ws.close()
            
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
            self.logger.error(f"Connection error: {str(e)}")
            return False

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            self.last_heartbeat = time.time()
            
            # Buffer messaggi per processamento batch
            if not hasattr(self, '_message_buffer'):
                self._message_buffer = []
            self._message_buffer.append(data)
            
            # Processa batch quando buffer pieno
            if len(self._message_buffer) >= 10:
                self._process_message_batch(self._message_buffer)
                self._message_buffer = []
                
        except Exception as e:
            self.logger.error(f"Message processing error: {str(e)}")
            
    def _process_message_batch(self, messages):
        """Processa messaggi in batch per migliori performance"""
        try:
            processed_data = [self._preprocess_message(msg) for msg in messages]
            self._handle_processed_batch(processed_data)
        except Exception as e:
            self.logger.error(f"Batch processing error: {str(e)}")

    def _on_error(self, ws, error):
        self.logger.error(f"WebSocket error: {str(error)}")
        self.connected = False
        self.handle_websocket_error(error)

    def _on_close(self, ws, close_status_code, close_msg):
        self.logger.warning("WebSocket connection closed")
        self.connected = False
        if self.should_run:
            self.handle_websocket_error(Exception("Connection closed"))

    def _on_open(self, ws):
        self.logger.info("WebSocket connection established")
        self.connected = True
        self.setup_heartbeat()


    def reconnect_websocket(self):
        try:
            # Your websocket reconnection code here. Example:
            # self.ws = websocket.WebSocketApp(...)
            # self.ws.run_forever()
            self.connected = True
            return True
        except Exception as e:
            self.logger.error(f"Reconnect failed: {e}")
            return False



    def handle_websocket_error(self, e: Exception):
        """Gestisce errori WebSocket con retry exponenziale e heartbeat"""
        retry_count = 0
        current_delay = self.retry_delay

        while retry_count < self.max_retries:
            try:
                self.logger.info(f"Tentativo riconnessione {retry_count + 1}/{self.max_retries}")
                if self.reconnect_websocket():
                    self.setup_heartbeat()
                    return True

                current_delay = min(current_delay * 2, 30)
                time.sleep(current_delay)
                retry_count += 1

            except Exception as conn_error:
                self.logger.error(f"Errore riconnessione: {str(conn_error)}")
                retry_count += 1

        self.logger.critical("Impossibile stabilire connessione WebSocket")
        return False

    def check_connection(self):
        """Verifica stato connessione"""
        try:
            return self.ws and self.ws.connected # Replace with your actual connection check
        except:
            return False

    def setup_heartbeat(self):
        """Configura heartbeat per mantenere connessione"""
        def heartbeat():
            while self.check_connection():
                self.ws.ping() # Replace with your actual ping method
                time.sleep(30)

        threading.Thread(target=heartbeat, daemon=True).start()


# Example usage (adapt to your application)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

websocket_handler = WebSocketHandler(logger)
if websocket_handler.connect_websocket():
    print("WebSocket connection established successfully.")
else:
    print("Failed to establish WebSocket connection.")