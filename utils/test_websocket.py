import os
import asyncio
import logging
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.websocket_handler import WebSocketHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_connection():
    """Test WebSocket connection with automatic recovery"""
    try:
        # Use Binance testnet WebSocket URL
        ws_url = "wss://testnet.binance.vision/ws"
        api_key = os.getenv("BINANCE_TESTNET_API_KEY")

        handler = WebSocketHandler(ws_url, api_key)

        # Test message handler
        async def handle_market_data(data):
            logger.info(f"Received market data: {data}")

        # Register handler for market data
        handler.register_handler("marketData", handle_market_data)

        # Attempt connection
        success = await handler.connect()
        if not success:
            logger.error("Initial connection failed")
            return False

        # Subscribe to multiple streams for better testing
        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": [
                "btcusdt@trade",    # Trade data
                "btcusdt@kline_1m", # 1 minute klines
                "btcusdt@depth"     # Order book updates
            ],
            "id": 1
        }

        logger.info("Sending subscription message...")
        if not await handler.send(subscribe_msg):
            logger.error("Failed to send subscription message")
            return False

        logger.info("Waiting for market data...")
        # Listen for messages for 60 seconds (increased from 30)
        try:
            listen_task = asyncio.create_task(handler.listen())
            await asyncio.sleep(60)  # Increased wait time
            listen_task.cancel()
        except asyncio.CancelledError:
            pass

        logger.info("Test completed, closing connection...")
        await handler.close()
        return True

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_websocket_connection())