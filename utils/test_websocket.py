import os
import asyncio
import logging
import sys
import unittest
from unittest.mock import Mock, patch
import pytest
from asyncio import new_event_loop, set_event_loop
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.websocket_handler import WebSocketHandler

logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for more detailed logs
logger = logging.getLogger(__name__)

class TestWebSocketHandler(unittest.TestCase):
    def setUp(self):
        """Setup test environment with mocked dependencies"""
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = new_event_loop()
            set_event_loop(self.loop)

        # Create mocks
        self.mock_client = Mock()
        self.mock_twm = Mock()
        self.mock_twm.is_alive.return_value = True
        self.mock_twm.start.return_value = None
        self.mock_twm.start_multiplex_socket.return_value = True

        # Setup patches
        self.client_patcher = patch('utils.websocket_handler.Client', return_value=self.mock_client)
        self.twm_patcher = patch('utils.websocket_handler.ThreadedWebsocketManager', return_value=self.mock_twm)

        # Start patches
        self.mock_client_class = self.client_patcher.start()
        self.mock_twm_class = self.twm_patcher.start()

        # Create handler instance with test configuration
        self.handler = WebSocketHandler(api_key="test_key", api_secret="test_secret", testnet=True)

    def tearDown(self):
        """Cleanup patches and event loop"""
        self.client_patcher.stop()
        self.twm_patcher.stop()

        if self.loop and not self.loop.is_closed():
            pending = asyncio.all_tasks(self.loop)
            if pending:
                self.loop.run_until_complete(asyncio.gather(*pending))
            self.loop.close()

    def test_initial_connection(self):
        """Test initial WebSocket connection setup"""
        success = self.handler.setup_socket()
        self.assertTrue(success)
        self.assertTrue(self.handler.is_connected())

        # Verify correct method calls
        self.mock_twm.start.assert_called_once()
        self.mock_twm.start_multiplex_socket.assert_called_once()

    def test_reconnection_logic(self):
        """Test reconnection with exponential backoff"""
        # Initial setup - force first connection to fail
        self.mock_twm.start.side_effect = Exception("Connection failed")
        self.mock_twm.is_alive.return_value = False

        # First attempt should fail
        success = self.handler.setup_socket()
        self.assertFalse(success)
        self.assertFalse(self.handler.is_connected())

        # Reset state for reconnection
        self.handler.connected = False
        self.handler.reconnect_attempts = 0
        self.handler.last_reconnect = datetime.min
        self.handler.reconnect_delay = 1

        # Create new mock for successful reconnection
        new_mock = Mock(name="new_twm")
        new_mock.is_alive.return_value = True
        new_mock.start.side_effect = None
        new_mock.start.return_value = None
        new_mock.start_multiplex_socket.return_value = True

        # Configure TWM class to return new mock
        self.mock_twm_class.reset_mock()
        self.mock_twm_class.return_value = new_mock

        # Verify initial state
        self.assertFalse(self.handler.is_connected())
        self.assertEqual(self.handler.reconnect_attempts, 0)

        # Attempt reconnection
        success = self.handler.reconnect()

        # Verify reconnection succeeded
        self.assertTrue(success, "Reconnection failed when it should succeed")
        self.assertTrue(self.handler.is_connected())
        self.assertEqual(self.handler.reconnect_attempts, 1)

        # Verify correct method calls on new mock
        new_mock.start.assert_called_once()
        new_mock.is_alive.assert_called()
        new_mock.start_multiplex_socket.assert_called_once()

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
        self.handler.reconnect = Mock()

        # Test connection error
        error_msg = {'e': 'error', 'code': 1002, 'm': 'Connection lost'}
        self.handler._message_handler(error_msg)
        self.handler.reconnect.assert_called_once()

        # Test authentication error
        error_msg = {'e': 'error', 'code': 451, 'm': 'Invalid API key'}
        self.handler._message_handler(error_msg)

        # Verify handler was stopped
        self.assertFalse(self.handler.keep_running)

    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Integration test for WebSocket connection"""
        try:
            handler = WebSocketHandler(testnet=True)

            async def handle_market_data(data):
                logger.info(f"Received market data: {data}")

            handler.register_handler("btcusdt@trade", handle_market_data)
            success = handler.start()
            self.assertTrue(success)

            await asyncio.sleep(1)
            handler.stop()
        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
            raise

if __name__ == "__main__":
    unittest.main()