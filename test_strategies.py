
import logging
from datetime import datetime
import asyncio
from utils.strategies.strategy_manager import StrategyManager
from utils.strategies.scalping import ScalpingStrategy
from utils.strategies.swing_trading import SwingTradingStrategy
from utils.strategies.dex_sniping import DexSnipingStrategy
from utils.strategies.meme_coin_sniping import MemeCoinStrategy

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=f'strategy_test_{datetime.now().strftime("%Y%m%d")}.log'
)
logger = logging.getLogger(__name__)

async def test_strategies():
    try:
        logger.info("Starting strategy tests")
        
        # Initialize strategy manager
        strategy_manager = StrategyManager()
        
        # Test configurations
        test_configs = {
            'scalping': {
                'timeframe': '1m',
                'risk_per_trade': 0.01
            },
            'swing': {
                'timeframe': '4h',
                'risk_per_trade': 0.02
            },
            'dex_sniping': {
                'rpc_url': 'https://bsc-dataseed.binance.org/',
                'min_liquidity': 5,
                'max_buy_tax': 10,
                'min_holders': 50
            },
            'meme_coin': {
                'sentiment_threshold': 0.7,
                'viral_coefficient': 0.8,
                'risk_per_trade': 0.01
            }
        }
        
        # Test each strategy
        for strategy_name, config in test_configs.items():
            logger.info(f"Testing {strategy_name} strategy")
            
            # Activate strategy
            success = await strategy_manager.activate_strategy(strategy_name, config)
            
            if success:
                logger.info(f"{strategy_name} strategy activated successfully")
                
                # Get performance metrics
                metrics = strategy_manager.get_performance_metrics()
                logger.info(f"{strategy_name} performance metrics: {metrics.get(strategy_name, {})}")
                
                # Deactivate strategy
                await strategy_manager.deactivate_strategy(strategy_name)
            else:
                logger.error(f"Failed to activate {strategy_name} strategy")

        logger.info("Strategy tests completed")

    except Exception as e:
        logger.error(f"Error during strategy testing: {e}")

if __name__ == "__main__":
    asyncio.run(test_strategies())
