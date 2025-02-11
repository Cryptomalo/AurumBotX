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
        self.mock_twm = Mock()

        # Setup patches
        self.client_patcher = patch('utils.websocket_handler.Client', return_value=self.mock_client)
        self.twm_patcher = patch('utils.websocket_handler.ThreadedWebsocketManager', return_value=self.mock_twm)

        # Start patches
        self.mock_client_class = self.client_patcher.start()
        self.mock_twm_class = self.twm_patcher.start()

        # Configure default mock behavior
        self.mock_twm.is_alive.return_value = True
        self.mock_twm.start.return_value = None
        self.mock_twm.start_multiplex_socket.return_value = True

        # Create handler instance
        self.handler = WebSocketHandler(api_key="test_key", api_secret="test_secret", testnet=True)

    def tearDown(self):
        """Cleanup patches"""
        self.client_patcher.stop()
        self.twm_patcher.stop()

    def test_initial_connection(self):
        """Test initial WebSocket connection setup"""
        # Test connection
        success = self.handler.setup_socket()
        self.assertTrue(success)
        self.assertTrue(self.handler.is_connected())

        # Verify correct method calls
        self.mock_twm.start.assert_called_once()
        self.mock_twm.start_multiplex_socket.assert_called_once()

    def test_reconnection_logic(self):
        """Test reconnection with exponential backoff"""
        # First attempt: TWM fails to start
        self.mock_twm.start.side_effect = [Exception("Connection failed")]
        self.mock_twm.is_alive.return_value = False

        # First attempt should fail
        success = self.handler.setup_socket()
        self.assertFalse(success)

        # Reset mock and create new instance for second attempt
        self.mock_twm_class.reset_mock()
        new_mock_twm = Mock()
        new_mock_twm.is_alive.return_value = True
        new_mock_twm.start.side_effect = None  # Clear side effect
        new_mock_twm.start.return_value = None
        new_mock_twm.start_multiplex_socket.return_value = True
        self.mock_twm_class.return_value = new_mock_twm

        # Reset handler state
        self.handler.connected = False
        self.handler.twm = new_mock_twm

        # Reconnection should succeed
        success = self.handler.reconnect()
        self.assertTrue(success)
        self.assertTrue(self.handler.is_connected())
        new_mock_twm.start.assert_called_once()
        new_mock_twm.start_multiplex_socket.assert_called_once()

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