import logging
import asyncio
import psutil
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.database_manager import DatabaseManager
from utils.websocket_handler import WebSocketHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=f'system_checkup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)
logger = logging.getLogger(__name__)

async def check_memory_usage(warning_threshold_mb=800, critical_threshold_mb=950) -> dict:
    """Monitor memory usage of the application with detailed metrics"""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / 1024 / 1024
        memory_percent = process.memory_percent()

        status = {
            "status": "healthy",
            "memory_usage_mb": round(memory_usage_mb, 2),
            "memory_percent": round(memory_percent, 2),
            "warning_threshold_mb": warning_threshold_mb,
            "critical_threshold_mb": critical_threshold_mb
        }

        if memory_usage_mb > critical_threshold_mb:
            status["status"] = "critical"
            logger.critical(f"Critical memory usage: {memory_usage_mb:.2f} MB")
        elif memory_usage_mb > warning_threshold_mb:
            status["status"] = "warning"
            logger.warning(f"High memory usage: {memory_usage_mb:.2f} MB")
        else:
            logger.info(f"Memory usage: {memory_usage_mb:.2f} MB ({memory_percent:.1f}%)")

        return status
    except Exception as e:
        logger.error(f"Memory check failed: {str(e)}")
        return {"status": "error", "error": str(e)}

async def check_database_connection() -> dict:
    """Verify database connection with detailed metrics"""
    db = None
    try:
        db = DatabaseManager()
        start_time = datetime.now()

        if not await db.initialize():
            logger.error("Database initialization failed")
            return {"status": "error", "error": "Database initialization failed"}

        if not await db.test_connection():
            logger.error("Database connection test failed")
            return {"status": "error", "error": "Connection test failed"}

        response_time = (datetime.now() - start_time).total_seconds() * 1000
        pool_metrics = {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
            "pool_size": db.pool_size,
            "max_overflow": db.max_overflow
        }

        logger.info(f"Database connection healthy - Response time: {response_time:.2f}ms")
        return pool_metrics

    except Exception as e:
        logger.error(f"Database check failed: {str(e)}")
        return {"status": "error", "error": str(e)}
    finally:
        if db and hasattr(db, 'cleanup'):
            await db.cleanup()

async def check_websocket_connection() -> dict:
    """Verify WebSocket connection with detailed status"""
    handler = None
    try:
        handler = WebSocketHandler()
        start_time = datetime.now()

        if not await handler.initialize():
            logger.error("WebSocket initialization failed")
            return {"status": "error", "error": "Initialization failed"}

        connection_time = (datetime.now() - start_time).total_seconds() * 1000
        websocket_status = {
            "status": "healthy",
            "connection_time_ms": round(connection_time, 2),
            "active_streams": len(handler.active_streams),
            "reconnect_attempts": handler.reconnect_attempts,
            "max_reconnect_attempts": handler.max_reconnect_attempts
        }

        logger.info(f"WebSocket connection healthy - Connection time: {connection_time:.2f}ms")
        return websocket_status

    except Exception as e:
        logger.error(f"WebSocket check failed: {str(e)}")
        return {"status": "error", "error": str(e)}
    finally:
        if handler and hasattr(handler, 'cleanup'):
            await handler.cleanup()

async def run_system_checkup() -> dict:
    """Run comprehensive system checkup with detailed metrics"""
    logger.info("Starting system checkup...")

    checkup_results = {
        "timestamp": datetime.now().isoformat(),
        "system_status": "healthy",
        "components": {}
    }

    # Memory check
    checkup_results["components"]["memory"] = await check_memory_usage()

    # Database check
    checkup_results["components"]["database"] = await check_database_connection()

    # WebSocket check
    checkup_results["components"]["websocket"] = await check_websocket_connection()

    # Determine overall system status
    component_statuses = [
        component["status"] 
        for component in checkup_results["components"].values()
    ]

    if "error" in component_statuses:
        checkup_results["system_status"] = "error"
    elif "critical" in component_statuses:
        checkup_results["system_status"] = "critical"
    elif "warning" in component_statuses:
        checkup_results["system_status"] = "warning"

    logger.info(f"System checkup completed - Status: {checkup_results['system_status']}")
    return checkup_results

if __name__ == "__main__":
    try:
        result = asyncio.run(run_system_checkup())
        logger.info(f"Checkup Results: {result}")
        sys.exit(0 if result["system_status"] == "healthy" else 1)
    except Exception as e:
        logger.error(f"System checkup failed: {str(e)}")
        sys.exit(1)