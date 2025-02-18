import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
from utils.backup_manager import BackupManager
from utils.database import DatabaseManager
from utils.strategies.strategy_manager import StrategyManager

logger = logging.getLogger(__name__)

class AutoOptimizer:
    def __init__(self, db: DatabaseManager, strategy_manager: StrategyManager):
        self.db = db
        self.strategy_manager = strategy_manager
        self.backup_manager = BackupManager()
        self.optimization_interval = timedelta(hours=6)
        self.last_optimization = None
        self.performance_threshold = 0.02  # 2% improvement threshold
        self.max_params_history = 10
        
    async def optimize_strategies(self):
        """Auto-optimize trading strategies based on performance metrics"""
        try:
            current_time = datetime.now()
            
            if (self.last_optimization and 
                current_time - self.last_optimization < self.optimization_interval):
                return
                
            logger.info("Starting strategy auto-optimization")
            
            # Backup current configuration
            current_config = await self.strategy_manager.get_all_configurations()
            self.backup_manager.save_trading_config(current_config, "auto_optimization")
            
            # Get performance metrics for all strategies
            metrics = await self.get_performance_metrics()
            
            # Optimize each strategy
            for strategy_name, performance in metrics.items():
                try:
                    if self._needs_optimization(performance):
                        logger.info(f"Optimizing {strategy_name} strategy")
                        
                        # Get optimal parameters
                        new_params = await self._optimize_strategy_parameters(
                            strategy_name, 
                            performance
                        )
                        
                        if new_params:
                            # Backup before updating
                            self.backup_manager.save_trading_config(
                                {strategy_name: new_params},
                                f"{strategy_name}_optimization"
                            )
                            
                            # Update strategy parameters
                            await self.strategy_manager.update_strategy_parameters(
                                strategy_name,
                                new_params
                            )
                            
                            logger.info(f"Successfully optimized {strategy_name}")
                        
                except Exception as e:
                    logger.error(f"Error optimizing {strategy_name}: {e}")
                    continue
            
            self.last_optimization = current_time
            logger.info("Strategy optimization completed")
            
        except Exception as e:
            logger.error(f"Error during strategy optimization: {e}")
            
    async def get_performance_metrics(self) -> Dict[str, Dict]:
        """Get performance metrics for all active strategies"""
        try:
            metrics = {}
            strategies = await self.strategy_manager.get_active_strategies()
            
            for strategy in strategies:
                session = self.db.get_session()
                try:
                    # Get recent simulation results
                    results = session.execute(text("""
                        SELECT 
                            win_rate,
                            profit_loss,
                            sharpe_ratio,
                            max_drawdown,
                            volatility
                        FROM simulation_results
                        WHERE strategy_id = :strategy_id
                        AND created_at >= :start_date
                        ORDER BY created_at DESC
                        LIMIT 100
                    """), {
                        'strategy_id': strategy.id,
                        'start_date': datetime.now() - timedelta(days=7)
                    }).fetchall()
                    
                    if results:
                        metrics[strategy.name] = {
                            'win_rate': np.mean([r.win_rate for r in results]),
                            'profit_loss': np.mean([r.profit_loss for r in results]),
                            'sharpe_ratio': np.mean([r.sharpe_ratio for r in results]),
                            'max_drawdown': np.mean([r.max_drawdown for r in results]),
                            'volatility': np.mean([r.volatility for r in results])
                        }
                        
                finally:
                    session.close()
                    
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}
            
    def _needs_optimization(self, performance: Dict) -> bool:
        """Determine if strategy needs optimization based on performance"""
        # Check if performance is below thresholds
        return (
            performance.get('win_rate', 0) < 0.5 or
            performance.get('profit_loss', 0) < 0 or
            performance.get('sharpe_ratio', 0) < 1.0 or
            performance.get('max_drawdown', 0) < -0.1
        )
        
    async def _optimize_strategy_parameters(
        self,
        strategy_name: str,
        current_performance: Dict
    ) -> Optional[Dict]:
        """Find optimal parameters for a strategy using grid search"""
        try:
            # Get parameter ranges for optimization
            param_ranges = self.strategy_manager.get_parameter_ranges(strategy_name)
            
            best_params = None
            best_performance = float('-inf')
            
            # Grid search through parameter combinations
            for params in self._generate_parameter_combinations(param_ranges):
                # Test parameters
                performance = await self._evaluate_parameters(
                    strategy_name,
                    params,
                    current_performance
                )
                
                # Update best parameters if improvement threshold is met
                if (
                    performance > best_performance and
                    performance > current_performance.get('profit_loss', 0) * 
                    (1 + self.performance_threshold)
                ):
                    best_performance = performance
                    best_params = params
                    
            return best_params
            
        except Exception as e:
            logger.error(f"Error optimizing parameters for {strategy_name}: {e}")
            return None
            
    def _generate_parameter_combinations(self, param_ranges: Dict) -> List[Dict]:
        """Generate combinations of parameters for grid search"""
        # Implementation of parameter grid generation
        # This is a simplified version - extend based on strategy requirements
        combinations = []
        
        # Example: Generate combinations of risk levels and timeframes
        risk_levels = np.linspace(
            param_ranges.get('risk_level', [0.01])[0],
            param_ranges.get('risk_level', [0.05])[-1],
            5
        )
        
        timeframes = param_ranges.get('timeframe', ['1m', '5m', '15m', '1h'])
        
        for risk in risk_levels:
            for timeframe in timeframes:
                combinations.append({
                    'risk_level': risk,
                    'timeframe': timeframe
                })
                
        return combinations
        
    async def _evaluate_parameters(
        self,
        strategy_name: str,
        params: Dict,
        current_performance: Dict
    ) -> float:
        """Evaluate a set of parameters using historical data"""
        try:
            # Run strategy simulation with parameters
            simulation_result = await self.strategy_manager.run_strategy_simulation(
                strategy_name,
                params
            )
            
            # Calculate weighted performance score
            score = (
                simulation_result.get('profit_loss', 0) * 0.4 +
                simulation_result.get('win_rate', 0) * 0.3 +
                simulation_result.get('sharpe_ratio', 0) * 0.2 -
                abs(simulation_result.get('max_drawdown', 0)) * 0.1
            )
            
            return score
            
        except Exception as e:
            logger.error(f"Error evaluating parameters: {e}")
            return float('-inf')
