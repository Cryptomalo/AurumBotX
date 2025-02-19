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
from utils.data_loader import CryptoDataLoader
from utils.sentiment_analyzer import SentimentAnalyzer
from utils.prediction_model import PredictionModel
from utils.ai_trading import AITrading

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
    try:
        db = DatabaseManager()
        start_time = datetime.now()

        # Test connection with safe attribute access
        if await db.test_connection():
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            pool_metrics = {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
            }

            # Safely add pool metrics if available
            if hasattr(db, 'pool'):
                pool_metrics["pool_size"] = getattr(db, 'pool_size', None)
                if hasattr(db.pool, '_holders'):
                    pool_metrics["active_connections"] = len(db.pool._holders)

            logger.info(f"Database connection healthy - Response time: {response_time:.2f}ms")
            return pool_metrics
        else:
            logger.error("Database connection test failed")
            return {"status": "error", "error": "Connection test failed"}
    except Exception as e:
        logger.error(f"Database check failed: {str(e)}")
        return {"status": "error", "error": str(e)}

async def check_websocket_connection() -> dict:
    """Verify WebSocket connection with detailed status"""
    try:
        handler = WebSocketHandler()
        start_time = datetime.now()

        if await handler.initialize():
            # Test connection and measure response time
            connection_time = (datetime.now() - start_time).total_seconds() * 1000

            websocket_status = {
                "status": "healthy",
                "connection_time_ms": round(connection_time, 2),
                "active_streams": len(handler.active_streams) if hasattr(handler, 'active_streams') else 0,
                "reconnection_attempts": getattr(handler, 'reconnect_attempts', 0),
                "last_reconnect": handler.last_reconnect.isoformat() if hasattr(handler, 'last_reconnect') else None
            }

            logger.info(f"WebSocket connection healthy - Connection time: {connection_time:.2f}ms")
            await handler.cleanup()
            return websocket_status

        logger.error("WebSocket connection test failed")
        return {"status": "error", "error": "Connection initialization failed"}
    except Exception as e:
        logger.error(f"WebSocket check failed: {str(e)}")
        return {"status": "error", "error": str(e)}

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

    # Log overall status
    logger.info(f"System checkup completed - Status: {checkup_results['system_status']}")
    logger.info(f"Detailed Results: {checkup_results}")
    return checkup_results

if __name__ == "__main__":
    asyncio.run(run_system_checkup())