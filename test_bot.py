import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AurumBot Trading API",
    description="Trading Bot Control Interface",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test data
trade_data = {
    "trades": [],
    "start_time": datetime.now()
}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AurumBot Trading API",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/status")
async def get_status():
    """Get bot status"""
    return {
        "status": "running",
        "uptime": str(datetime.now() - trade_data["start_time"]),
        "trades": len(trade_data["trades"])
    }

@app.post("/test")
async def test_trading():
    """Execute test trade"""
    try:
        test_trade = {
            'success': True,
            'symbol': 'BTC/USDT',
            'action': 'buy',
            'price': 50000,
            'amount': 0.1,
            'timestamp': datetime.now().isoformat()
        }
        trade_data["trades"].append(test_trade)
        return test_trade
    except Exception as e:
        logger.error(f"Test trade error: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/metrics")
async def get_metrics():
    """Get trading metrics"""
    return {
        "total_trades": len(trade_data["trades"]),
        "active_pairs": ["BTC/USDT", "ETH/USDT"],
        "last_update": datetime.now().isoformat()
    }

if __name__ == "__main__":
    logger.info("Starting FastAPI server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3001,
        log_level="info"
    )