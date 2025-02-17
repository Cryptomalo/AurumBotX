import os
from datetime import datetime, timedelta
import logging
import warnings
from typing import Optional, Dict, List, Any
from enum import Enum
import json
import asyncio
from collections import defaultdict
from twilio.rest import Client
from queue import PriorityQueue
import time

logger = logging.getLogger(__name__)

class NotificationPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class NotificationCategory(Enum):
    TRADE = "trade"
    MARKET = "market"
    SYSTEM = "system"
    SECURITY = "security"
    PORTFOLIO = "portfolio"

class NotificationManager:
    def __init__(self):
        self.twilio_client = None
        self.from_phone = None
        self.to_phone = None
        self.setup_complete = False
        self.notification_history = defaultdict(list)
        self.rate_limits = {
            NotificationPriority.LOW: 3600,  # 1 hour
            NotificationPriority.MEDIUM: 1800,  # 30 minutes
            NotificationPriority.HIGH: 300,  # 5 minutes
            NotificationPriority.CRITICAL: 0  # No delay for critical
        }
        self.notification_queue = PriorityQueue()
        self.is_processing = False

    def setup(self, to_phone_number: str) -> bool:
        """Initialize notification channels"""
        try:
            # Get and clean credentials
            account_sid = os.getenv('TWILIO_ACCOUNT_SID', '').strip()
            auth_token = os.getenv('TWILIO_AUTH_TOKEN', '').strip()
            self.from_phone = os.getenv('TWILIO_PHONE_NUMBER', '').strip()

            if not all([account_sid, auth_token, self.from_phone]):
                logger.warning("Missing Twilio credentials - notifications will be logged only")
                return True  # Return True to allow operation without Twilio

            # Initialize Twilio client with cleaned credentials
            self.twilio_client = Client(account_sid, auth_token)
            self.to_phone = self._validate_and_format_phone_number(to_phone_number)
            self.setup_complete = True

            # Start notification processor
            asyncio.create_task(self._process_notification_queue())

            logger.info("Notification manager setup completed")
            return True

        except Exception as e:
            logger.error(f"Error setting up notification manager: {str(e)}")
            return True  # Return True to allow operation without Twilio

    def _validate_and_format_phone_number(self, phone_number: str) -> Optional[str]:
        """Validate and format phone number to E.164 format"""
        try:
            cleaned = ''.join(filter(str.isdigit, phone_number))
            if len(cleaned) == 10:  # US number without country code
                cleaned = '1' + cleaned
            if not cleaned.startswith('+'):
                cleaned = '+' + cleaned
            if len(cleaned) < 10 or len(cleaned) > 15:
                logger.error(f"Invalid phone number length: {cleaned}")
                return None
            return cleaned
        except Exception as e:
            logger.error(f"Error formatting phone number: {str(e)}")
            return None

    async def _process_notification_queue(self):
        """Process queued notifications"""
        self.is_processing = True
        while self.is_processing:
            try:
                if not self.notification_queue.empty():
                    priority, timestamp, notification = self.notification_queue.get()
                    category = notification.get('category', NotificationCategory.SYSTEM)

                    # Check rate limiting
                    if self._should_send_notification(category, priority):
                        await self._send_notification(notification)
                        self.notification_history[category].append({
                            'timestamp': datetime.now(),
                            'priority': priority,
                            'content': notification
                        })

                await asyncio.sleep(1)  # Prevent CPU overuse
            except Exception as e:
                logger.error(f"Error processing notification queue: {str(e)}")
                await asyncio.sleep(5)  # Back off on error

    def _should_send_notification(self, category: NotificationCategory, 
                                priority: NotificationPriority) -> bool:
        """Check if notification should be sent based on rate limits"""
        if not self.notification_history[category]:
            return True

        last_notification = self.notification_history[category][-1]['timestamp']
        time_since_last = (datetime.now() - last_notification).total_seconds()
        return time_since_last >= self.rate_limits[priority]

    async def _send_notification(self, notification: Dict[str, Any]) -> bool:
        """Send notification through configured channels"""
        try:
            if not self.setup_complete:
                logger.warning("Notification manager not setup")
                return False

            message = self._format_notification_message(notification)

            # Send via SMS
            if self.twilio_client and self.to_phone:
                self.twilio_client.messages.create(
                    body=message,
                    from_=self.from_phone,
                    to=self.to_phone
                )

            logger.info(f"Notification sent successfully: {notification.get('type', 'unknown')}")
            return True

        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False

    def _format_notification_message(self, notification: Dict[str, Any]) -> str:
        """Format notification message based on type and content"""
        try:
            message_type = notification.get('type', 'general')
            priority = notification.get('priority', NotificationPriority.MEDIUM)

            prefix = "🚨" if priority == NotificationPriority.CRITICAL else "ℹ️"

            if message_type == 'trade':
                return self._format_trade_notification(notification, prefix)
            elif message_type == 'market':
                return self._format_market_notification(notification, prefix)
            elif message_type == 'system':
                return self._format_system_notification(notification, prefix)
            else:
                return f"{prefix} {notification.get('message', 'No message content')}"

        except Exception as e:
            logger.error(f"Error formatting notification: {str(e)}")
            return "Error formatting notification"

    def _format_trade_notification(self, notification: Dict[str, Any], prefix: str) -> str:
        """Format trade-specific notification"""
        action = notification.get('action', 'UNKNOWN')
        symbol = notification.get('symbol', 'UNKNOWN')
        price = notification.get('price', 0.0)
        quantity = notification.get('quantity', 0.0)
        profit_loss = notification.get('profit_loss')

        message = f"{prefix} Trade Alert - {symbol}\n"
        message += f"📊 Action: {action}\n"
        message += f"💰 Price: ${price:.8f}\n"
        message += f"📈 Quantity: {quantity:.6f}\n"

        if profit_loss is not None:
            message += f"💸 P/L: ${profit_loss:.2f}\n"

        message += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return message

    def _format_market_notification(self, notification: Dict[str, Any], prefix: str) -> str:
        """Format market-specific notification"""
        symbol = notification.get('symbol', 'UNKNOWN')
        event = notification.get('event', 'UNKNOWN')
        details = notification.get('details', {})

        message = f"{prefix} Market Alert - {symbol}\n"
        message += f"📊 Event: {event}\n"

        for key, value in details.items():
            message += f"{key}: {value}\n"

        message += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return message

    def _format_system_notification(self, notification: Dict[str, Any], prefix: str) -> str:
        """Format system-specific notification"""
        event = notification.get('event', 'UNKNOWN')
        status = notification.get('status', 'UNKNOWN')
        details = notification.get('details', 'No additional details')

        message = f"{prefix} System Alert\n"
        message += f"🔧 Event: {event}\n"
        message += f"📊 Status: {status}\n"
        message += f"ℹ️ Details: {details}\n"
        message += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return message

    async def queue_notification(self, notification: Dict[str, Any], 
                               priority: NotificationPriority = NotificationPriority.MEDIUM):
        """Queue a notification for processing"""
        try:
            timestamp = time.time()
            self.notification_queue.put((priority.value, timestamp, notification))
            logger.debug(f"Notification queued with priority {priority}")
            return True
        except Exception as e:
            logger.error(f"Error queuing notification: {str(e)}")
            return False

    def get_notification_history(self, category: Optional[NotificationCategory] = None,
                               limit: int = 100) -> List[Dict[str, Any]]:
        """Get notification history for a category"""
        try:
            if category:
                history = self.notification_history[category]
            else:
                history = []
                for cat_history in self.notification_history.values():
                    history.extend(cat_history)

            # Sort by timestamp and limit
            return sorted(history, 
                        key=lambda x: x['timestamp'],
                        reverse=True)[:limit]
        except Exception as e:
            logger.error(f"Error getting notification history: {str(e)}")
            return []

    async def stop(self):
        """Stop notification processing"""
        self.is_processing = False
        logger.info("Notification manager stopped")


class TradingNotifier(NotificationManager):
    """
    Legacy compatibility class for TradingNotifier.
    @deprecated: Use NotificationManager instead for new code.
    """
    def __init__(self):
        warnings.warn("TradingNotifier is deprecated, use NotificationManager instead",
                     DeprecationWarning, stacklevel=2)
        super().__init__()

    def send_trade_notification(self, action, symbol, price, quantity, profit_loss=None):
        """Legacy method for sending trade notifications"""
        notification = {
            'type': 'trade',
            'category': NotificationCategory.TRADE,
            'action': action,
            'symbol': symbol,
            'price': price,
            'quantity': quantity,
            'profit_loss': profit_loss
        }
        asyncio.create_task(self.queue_notification(
            notification, NotificationPriority.HIGH))

    def send_error_notification(self, symbol, error_message):
        """Legacy method for sending error notifications"""
        notification = {
            'type': 'system',
            'category': NotificationCategory.SYSTEM,
            'event': 'ERROR',
            'status': 'ERROR',
            'details': f"Symbol: {symbol}, Error: {error_message}"
        }
        asyncio.create_task(self.queue_notification(
            notification, NotificationPriority.CRITICAL))

    def send_price_alert(self, symbol, price, change_percent):
        """Legacy method for sending price alerts"""
        notification = {
            'type': 'market',
            'category': NotificationCategory.MARKET,
            'symbol': symbol,
            'event': 'PRICE_ALERT',
            'details': {
                'Current Price': f"${price:.2f}",
                'Change': f"{change_percent:.2%}"
            }
        }
        asyncio.create_task(self.queue_notification(
            notification, NotificationPriority.MEDIUM))