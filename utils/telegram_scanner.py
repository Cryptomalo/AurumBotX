import logging
import asyncio
import qrcode
import io
from typing import List, Dict, Optional, Set, Union
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.tl.types import Message, Channel, User, Dialog
import re

logger = logging.getLogger(__name__)

class TelegramScanner:
    def __init__(self, api_id=None, api_hash=None):
        """Initialize TelegramScanner with session management"""
        self.session_file = "aurum_bot.session"
        self.api_id = api_id
        self.api_hash = api_hash
        self.client = None
        self.scanning = False
        self.detected_coins = {}
        self.monitored_channels: Set[int] = set()
        self.coin_patterns = [
            r'(\$[A-Z]+)',  # Match $SYMBOL
            r'([A-Z]{3,10})/(?:USD|USDT|ETH|BTC)\b',  # Match trading pairs
            r'([A-Z]+) token',  # Match TOKEN token
            r'([A-Z]+) coin',   # Match COIN coin
            r'#([A-Z]+)\b',     # Match #SYMBOL
            r'([A-Z]{3,10})(?:\s+(?:address|contract))',  # Match contract addresses
            r'0x[a-fA-F0-9]{40}',  # Match Ethereum contract addresses
        ]
        self.qr_login = None
        self.connection_state = "disconnected"

    async def start(self) -> bool:
        """Start Telegram client with QR login"""
        try:
            if self.client and self.client.is_connected():
                await self.client.disconnect()
                self.client = None

            # Initialize client with API credentials if provided, otherwise use QR
            self.client = TelegramClient(
                self.session_file,
                api_id=self.api_id if self.api_id else 1,
                api_hash=self.api_hash if self.api_hash else "placeholder",
                system_version="Windows 10",
                device_model="Desktop",
                app_version="1.0",
            )
            
            # Use API key authentication if credentials provided
            if self.api_id and self.api_hash:
                await self.client.start()
            else:
                # Use QR login as fallback

            # Generate QR login widget
            self.qr_login = await self.client.qr_login()

            # Convert QR to image
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4
            )
            qr.add_data(self.qr_login.url)
            qr.make(fit=True)

            # Create QR image
            img = qr.make_image(fill_color="black", back_color="white")

            # Save QR to buffer
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            self.connection_state = "awaiting_qr_scan"
            logger.info("Waiting for QR code scan...")

            # Wait for user to scan QR
            try:
                await asyncio.wait_for(self.qr_login.wait(), timeout=120)
                self.connection_state = "connecting"

                # Start client
                await self.client.connect()

                if await self.client.is_user_authorized():
                    me = await self.client.get_me()
                    logger.info(f"Successfully logged in as {me.username if me.username else me.id}")
                    self.connection_state = "connected"
                    return True
                else:
                    logger.error("Failed to authorize with Telegram")
                    self.connection_state = "unauthorized"
                    return False

            except asyncio.TimeoutError:
                logger.error("QR code scan timeout")
                self.connection_state = "timeout"
                return False

        except Exception as e:
            logger.error(f"Error starting Telegram client: {e}", exc_info=True)
            self.connection_state = "error"
            return False

    def get_connection_state(self) -> str:
        """Get current connection state"""
        return self.connection_state

    async def scan_channels(self, scan_limit: int = 1000):
        """Scan subscribed channels for potential meme coins"""
        if not self.client or not await self.client.is_user_authorized():
            logger.error("Client not connected or not authorized")
            return

        self.scanning = True
        try:
            # Get all dialogs (channels, groups, etc.)
            all_dialogs = await self.client.get_dialogs(limit=scan_limit)
            channels = [d for d in all_dialogs if isinstance(d.entity, (Channel, User)) 
                       and d.entity.id not in self.monitored_channels]

            logger.info(f"Found {len(channels)} new channels to scan")

            for dialog in channels:
                if not self.scanning:
                    break

                try:
                    channel_name = getattr(dialog, 'name', f"Channel {dialog.id}")
                    logger.info(f"Scanning channel: {channel_name}")

                    # Get recent messages
                    messages = await self.client.get_messages(dialog.entity, limit=100)

                    for message in messages:
                        if not self.scanning:
                            break
                        await self._process_message(message, channel_name)

                    # Add to monitored channels
                    self.monitored_channels.add(dialog.entity.id)

                except Exception as e:
                    logger.error(f"Error scanning channel {dialog.id}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scanning channels: {e}", exc_info=True)
        finally:
            self.scanning = False

    async def _process_message(self, message: Message, channel_name: str):
        """Process message to detect potential meme coins"""
        if not message.text:
            return

        # Find potential coin mentions
        detected = set()
        text = message.text.upper()  # Convert to uppercase for better matching

        for pattern in self.coin_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                symbol = match.group(1).upper() if len(match.groups()) > 0 else match.group(0).upper()
                if len(symbol) >= 3 and symbol.isalnum():  # Filter valid symbols
                    detected.add(symbol)

        # Update coin tracking
        timestamp = message.date
        for symbol in detected:
            if symbol not in self.detected_coins:
                self.detected_coins[symbol] = {
                    'first_seen': timestamp,
                    'channels': {channel_name},
                    'mention_count': 1,
                    'recent_mentions': [(timestamp, channel_name)],
                    'latest_message': message.text[:200]  # Store truncated message
                }
            else:
                self.detected_coins[symbol]['mention_count'] += 1
                self.detected_coins[symbol]['channels'].add(channel_name)
                self.detected_coins[symbol]['recent_mentions'].append(
                    (timestamp, channel_name)
                )
                # Keep only recent mentions (last 24 hours)
                self.detected_coins[symbol]['recent_mentions'] = [
                    m for m in self.detected_coins[symbol]['recent_mentions']
                    if m[0] > datetime.now() - timedelta(hours=24)
                ]

    def get_trending_coins(self, min_mentions: int = 3, hours: int = 24) -> List[Dict[str, Union[str, int, float]]]:
        """Get trending coins based on recent mentions with advanced metrics"""
        trending = []
        cutoff_time = datetime.now() - timedelta(hours=hours)

        for symbol, data in self.detected_coins.items():
            # Filter recent mentions
            recent_mentions = [m for m in data['recent_mentions'] if m[0] > cutoff_time]
            recent_count = len(recent_mentions)

            if recent_count >= min_mentions:
                # Calculate trending score
                time_weights = [(datetime.now() - m[0]).total_seconds() / 3600 for m, _ in recent_mentions]
                trending_score = sum(1 / (1 + w) for w in time_weights)  # Higher score for recent mentions

                # Calculate velocity (mentions per hour)
                if recent_mentions:
                    time_span = (max(m[0] for m, _ in recent_mentions) - min(m[0] for m, _ in recent_mentions)).total_seconds() / 3600
                    velocity = recent_count / (time_span if time_span > 0 else 1)
                else:
                    velocity = 0

                trending.append({
                    'symbol': symbol,
                    'total_mentions': data['mention_count'],
                    'recent_mentions': recent_count,
                    'channels': len(data['channels']),
                    'first_seen': data['first_seen'].isoformat(),
                    'trending_score': round(trending_score, 2),
                    'velocity': round(velocity, 2),
                    'latest_message': data.get('latest_message', '')
                })

        # Sort by trending score and velocity
        return sorted(trending, key=lambda x: (x['trending_score'], x['velocity']), reverse=True)

    async def stop(self):
        """Stop scanning and disconnect client"""
        self.scanning = False
        if self.client:
            await self.client.disconnect()
            self.connection_state = "disconnected"
            logger.info("Telegram client disconnected")

    def reset_monitoring(self):
        """Reset monitoring state for a fresh scan"""
        self.monitored_channels.clear()
        self.detected_coins.clear()
        logger.info("Monitoring state reset")