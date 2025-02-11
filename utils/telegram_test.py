import os
import logging
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_telegram_connection():
    """Test the Telegram connection with provided credentials"""
    try:
        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        
        if not api_id or not api_hash:
            logger.error("Telegram credentials not found in environment variables")
            return False
            
        client = TelegramClient('aurum_bot', int(api_id), api_hash)
        
        logger.info("Attempting to connect to Telegram...")
        await client.connect()
        
        if await client.is_user_authorized():
            me = await client.get_me()
            logger.info(f"Successfully connected as: {me.username}")
            return True
        else:
            logger.warning("Authentication required. Please run the full login script")
            return False
            
    except Exception as e:
        logger.error(f"Error testing Telegram connection: {e}")
        return False
    finally:
        if 'client' in locals():
            await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_telegram_connection())
