
import asyncio
import logging
from datetime import datetime
from utils.system_checkup import run_system_checkup
from utils.database_manager import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=f'system_check_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)

async def main():
    try:
        print("Starting system diagnostics...")
        
        # Database check
        db = DatabaseManager()
        if await db.initialize():
            print("✓ Database connection successful")
        else:
            print("✗ Database connection failed")
            
        # Run full system checkup
        result = await run_system_checkup()
        print(f"System check completed. Status: {'✓' if result else '✗'}")
        
    except Exception as e:
        print(f"Error during system check: {str(e)}")
        logging.error(f"System check failed: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(main())
