import os
import asyncio
import logging
import sys
import unittest
from unittest.mock import Mock, patch
import pytest

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.websocket_handler import WebSocketHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestWebSocketHandler(unittest.TestCase):
    def setUp(self):
        """Setup test environment with mocked dependencies"""
        self.mock_client = Mock()
        self.mock_bm = Mock()

        # Setup patches
        self.client_patcher = patch('utils.websocket_handler.Client', return_value=self.mock_client)
        self.bm_patcher = patch('utils.websocket_handler.BinanceSocketManager', return_value=self.mock_bm)

        # Start patches
        self.mock_client_class = self.client_patcher.start()
        self.mock_bm_class = self.bm_patcher.start()

        # Create handler instance
        self.handler = WebSocketHandler(api_key="test_key", api_secret="test_secret", testnet=True)

    def tearDown(self):
        """Cleanup patches"""
        self.client_patcher.stop()
        self.bm_patcher.stop()

    def test_initial_connection(self):
        """Test initial WebSocket connection setup"""
        # Configure mock
        self.mock_bm.start_multiplex_socket.return_value = "test_conn_key"

        # Test connection
        success = self.handler.setup_socket()
        self.assertTrue(success)
        self.assertTrue(self.handler.is_connected())

        # Verify correct method calls
        self.mock_bm.start_multiplex_socket.assert_called_once()
        self.mock_bm.start.assert_called_once()

    def test_reconnection_logic(self):
        """Test reconnection with exponential backoff"""
        # Configure mock to fail first then succeed
        self.mock_bm.start_multiplex_socket.side_effect = [Exception("Connection failed"), "test_conn_key"]

        # First attempt should fail
        success = self.handler.setup_socket()
        self.assertFalse(success)

        # Reconnection should succeed
        success = self.handler.reconnect()
        self.assertTrue(success)

        # Verify backoff delay was reset
        self.assertEqual(self.handler.reconnect_delay, 1)

    def test_message_handler(self):
        """Test message handling with various scenarios"""
        received_messages = []

        def test_handler(msg):
            received_messages.append(msg)

        # Register handler
        self.handler.register_handler('btcusdt@trade', test_handler)

        # Test valid message
        test_msg = {
            'stream': 'btcusdt@trade',
            'data': {'price': '50000', 'quantity': '1.0'}
        }
        self.handler._message_handler(test_msg)

        # Verify message was processed
        self.assertEqual(len(received_messages), 1)
        self.assertEqual(received_messages[0], test_msg['data'])

    def test_error_handling(self):
        """Test error handling with different error codes"""
        # Mock reconnect method
        self.handler.reconnect = Mock()

        # Test connection error
        error_msg = {'e': 'error', 'code': 1002, 'm': 'Connection lost'}
        self.handler._message_handler(error_msg)

        # Verify reconnect was attempted
        self.handler.reconnect.assert_called_once()

        # Test authentication error
        error_msg = {'e': 'error', 'code': 451, 'm': 'Invalid API key'}
        self.handler._message_handler(error_msg)

        # Verify handler was stopped
        self.assertFalse(self.handler.keep_running)

@pytest.mark.asyncio
async def test_websocket_connection():
    """Integration test for WebSocket connection"""
    try:
        handler = WebSocketHandler(testnet=True)

        # Test message handler
        async def handle_market_data(data):
            logger.info(f"Received market data: {data}")

        # Register handler
        handler.register_handler("btcusdt@trade", handle_market_data)

        # Test connection
        success = handler.start()
        assert success, "Failed to establish initial connection"

        logger.info("Connection established successfully")

        # Test message sending
        test_msg = {
            "method": "SUBSCRIBE",
            "params": ["btcusdt@trade"],
            "id": 1
        }

        success = await handler.send_message(test_msg)
        assert success, "Failed to send test message"

        logger.info("Test message sent successfully")

        # Wait briefly to observe behavior
        await asyncio.sleep(5)

        # Cleanup
        handler.stop()
        return True

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    unittest.main()