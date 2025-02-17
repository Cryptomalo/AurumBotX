import os
import sys
import asyncio
import logging
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from utils.notifications import NotificationManager, NotificationPriority, NotificationCategory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_notifications():
    """Test the enhanced notification system"""
    try:
        # Initialize notification manager
        notifier = NotificationManager()

        # Setup with Twilio phone number from environment
        success = notifier.setup(os.getenv('TWILIO_PHONE_NUMBER'))
        if not success:
            logger.error("Failed to setup notification manager")
            return

        # Test trade notification
        trade_notification = {
            'type': 'trade',
            'category': NotificationCategory.TRADE,
            'action': 'BUY',
            'symbol': 'BTC/USDT',
            'price': 45000.00,
            'quantity': 0.1,
            'profit_loss': 150.25
        }
        await notifier.queue_notification(
            trade_notification, 
            priority=NotificationPriority.HIGH
        )

        # Test market notification
        market_notification = {
            'type': 'market',
            'category': NotificationCategory.MARKET,
            'symbol': 'ETH/USDT',
            'event': 'PRICE_ALERT',
            'details': {
                'Current Price': '$2850.00',
                'Target': '$3000.00',
                'Change': '+5.2%'
            }
        }
        await notifier.queue_notification(
            market_notification, 
            priority=NotificationPriority.MEDIUM
        )

        # Test system notification
        system_notification = {
            'type': 'system',
            'category': NotificationCategory.SYSTEM,
            'event': 'API_ERROR',
            'status': 'WARNING',
            'details': 'Rate limit approaching, throttling requests'
        }
        await notifier.queue_notification(
            system_notification, 
            priority=NotificationPriority.CRITICAL
        )

        # Wait for notifications to be processed
        await asyncio.sleep(5)

        # Get and display notification history
        history = notifier.get_notification_history(limit=10)
        logger.info(f"Notification History: {len(history)} entries")
        for entry in history:
            logger.info(f"Notification: {entry['content']['type']} - "
                       f"Priority: {entry['priority']} - "
                       f"Time: {entry['timestamp']}")

        # Stop notification manager
        await notifier.stop()
        logger.info("Notification test completed")

    except Exception as e:
        logger.error(f"Error in notification test: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_notifications())