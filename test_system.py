
import asyncio
import logging
from datetime import datetime
from utils.system_checkup import run_system_checkup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=f'system_checkup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)

async def main():
    print("Starting system checkup...")
    result = await run_system_checkup()
    print(f"System check completed. All systems operational: {result}")

if __name__ == "__main__":
    asyncio.run(main())
