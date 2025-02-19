import asyncio
import logging
from utils.system_checkup import run_system_checkup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting system monitor...")
    asyncio.run(run_system_checkup())
