import logging
import asyncio
import qrcode
import io
from typing import List, Dict, Optional, Set, Union
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.tl.types import Message, Channel, User, Dialog
import re
import os

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
        self.connection_state = "disconnected"
        self.setup_instructions = self._generate_setup_instructions()

    def _generate_setup_instructions(self) -> Dict[str, str]:
        """Generate setup instructions for the user"""
        return {
            "title": "🔧 Configurazione Bot Telegram",
            "steps": [
                "1. Vai su https://my.telegram.org/auth e accedi",
                "2. Clicca su 'API Development Tools'",
                "3. Crea una nuova applicazione con questi dati:",
                "   - App title: AurumBot",
                "   - Short name: aurum_bot",
                "   - Platform: Desktop",
                "   - Description: Crypto trading bot for monitoring and analysis",
                "4. Copia l'api_id (numero) e api_hash (stringa) che ricevi",
                "5. Inserisci questi valori nelle variabili d'ambiente:"
                "   TELEGRAM_API_ID e TELEGRAM_API_HASH"
            ],
            "bot_username": "@aurum_crypto_bot",
            "channel_link": "https://t.me/aurum_signals"
        }

    def get_setup_status(self) -> Dict[str, Union[str, Dict]]:
        """Get current setup status and instructions"""
        has_api_id = bool(os.getenv("TELEGRAM_API_ID"))
        has_api_hash = bool(os.getenv("TELEGRAM_API_HASH"))

        return {
            "status": "ready" if (has_api_id and has_api_hash) else "needs_setup",
            "connection_state": self.connection_state,
            "credentials_status": {
                "api_id": "configurato" if has_api_id else "mancante",
                "api_hash": "configurato" if has_api_hash else "mancante"
            },
            "instructions": self.setup_instructions
        }

    async def start(self) -> bool:
        """Start Telegram client"""
        if not os.getenv("TELEGRAM_API_ID") or not os.getenv("TELEGRAM_API_HASH"):
            logger.warning("Telegram API credentials not configured")
            self.connection_state = "needs_setup"
            return False

        try:
            if self.client and self.client.is_connected():
                await self.client.disconnect()
                self.client = None

            self.client = TelegramClient(
                self.session_file,
                api_id=int(os.getenv("TELEGRAM_API_ID")),
                api_hash=os.getenv("TELEGRAM_API_HASH"),
                system_version="Windows 10",
                device_model="Desktop",
                app_version="1.0",
            )

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

                    messages = await self.client.get_messages(dialog.entity, limit=100)

                    for message in messages:
                        if not self.scanning:
                            break
                        await self._process_message(message, channel_name)

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

        detected = set()
        text = message.text.upper()

        for pattern in self.coin_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                symbol = match.group(1).upper() if len(match.groups()) > 0 else match.group(0).upper()
                if len(symbol) >= 3 and symbol.isalnum():
                    detected.add(symbol)

        timestamp = message.date
        for symbol in detected:
            if symbol not in self.detected_coins:
                self.detected_coins[symbol] = {
                    'first_seen': timestamp,
                    'channels': {channel_name},
                    'mention_count': 1,
                    'recent_mentions': [(timestamp, channel_name)],
                    'latest_message': message.text[:200]
                }
            else:
                self.detected_coins[symbol]['mention_count'] += 1
                self.detected_coins[symbol]['channels'].add(channel_name)
                self.detected_coins[symbol]['recent_mentions'].append(
                    (timestamp, channel_name)
                )
                self.detected_coins[symbol]['recent_mentions'] = [
                    m for m in self.detected_coins[symbol]['recent_mentions']
                    if m[0] > datetime.now() - timedelta(hours=24)
                ]

    def get_trending_coins(self, min_mentions: int = 3, hours: int = 24) -> List[Dict[str, Union[str, int, float]]]:
        """Get trending coins based on recent mentions with advanced metrics"""
        trending = []
        cutoff_time = datetime.now() - timedelta(hours=hours)

        for symbol, data in self.detected_coins.items():
            recent_mentions = [m for m in data['recent_mentions'] if m[0] > cutoff_time]
            recent_count = len(recent_mentions)

            if recent_count >= min_mentions:
                time_weights = [(datetime.now() - m[0]).total_seconds() / 3600 for m, _ in recent_mentions]
                trending_score = sum(1 / (1 + w) for w in time_weights)

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

    coin_patterns = [
        r'(\$[A-Z]+)',  # Match $SYMBOL
        r'([A-Z]{3,10})/(?:USD|USDT|ETH|BTC)\b',  # Match trading pairs
        r'([A-Z]+) token',  # Match TOKEN token
        r'([A-Z]+) coin',   # Match COIN coin
        r'#([A-Z]+)\b',     # Match #SYMBOL
        r'([A-Z]{3,10})(?:\s+(?:address|contract))',  # Match contract addresses
        r'0x[a-fA-F0-9]{40}',  # Match Ethereum contract addresses
    ]