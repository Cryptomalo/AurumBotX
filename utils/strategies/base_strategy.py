from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.is_active = False
        self.last_analysis_time = None
        self.performance_metrics = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_profit_loss': 0.0,
            'win_rate': 0.0
        }

    @abstractmethod
    async def analyze_market(
        self,
        market_data: pd.DataFrame,
        sentiment_data: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze market and generate trading signals
        Args:
            market_data: DataFrame with market data
            sentiment_data: Optional social media sentiment data
        Returns:
            List of trading signals
        """
        pass

    @abstractmethod
    async def validate_trade(
        self,
        signal: Dict[str, Any],
        portfolio: Dict[str, Any]
    ) -> bool:
        """
        Validate a potential trade before execution
        Args:
            signal: Trading signal to validate
            portfolio: Current portfolio state
        Returns:
            bool: True if trade is valid
        """
        pass

    @abstractmethod
    async def execute_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trade based on the signal
        Args:
            signal: Trading signal to execute
        Returns:
            Trade execution result
        """
        pass

    def update_performance(self, trade_result: Dict[str, Any]) -> None:
        """Update strategy performance metrics"""
        try:
            self.performance_metrics['total_trades'] += 1
            if trade_result.get('success', False):
                self.performance_metrics['successful_trades'] += 1
                self.performance_metrics['total_profit_loss'] += trade_result.get('profit_loss', 0)
            else:
                self.performance_metrics['failed_trades'] += 1

            if self.performance_metrics['total_trades'] > 0:
                self.performance_metrics['win_rate'] = (
                    self.performance_metrics['successful_trades'] / 
                    self.performance_metrics['total_trades']
                ) * 100
        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            **self.performance_metrics,
            'last_update': datetime.now().isoformat()
        }

    async def cleanup(self) -> None:
        """Cleanup strategy resources"""
        try:
            self.is_active = False
            logger.info(f"Strategy {self.name} deactivated")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def is_strategy_active(self) -> bool:
        """Check if strategy is active"""
        return self.is_active

    def activate(self) -> None:
        """Activate the strategy"""
        self.is_active = True
        logger.info(f"Strategy {self.name} activated")

    def deactivate(self) -> None:
        """Deactivate the strategy"""
        self.is_active = False
        logger.info(f"Strategy {self.name} deactivated")

    def get_config(self) -> Dict[str, Any]:
        """Get current strategy configuration"""
        return {
            'name': self.name,
            'config': self.config,
            'is_active': self.is_active,
            'performance_metrics': self.performance_metrics,
            'timestamp': datetime.now().isoformat()
        }

    def set_config(self, config: Dict[str, Any]) -> None:
        """Set strategy configuration"""
        try:
            self.name = config.get('name', self.name)
            self.config.update(config.get('config', {}))
            self.is_active = config.get('is_active', self.is_active)
            if 'performance_metrics' in config:
                self.performance_metrics.update(config['performance_metrics'])
            logger.info(f"Configuration updated for strategy {self.name}")
        except Exception as e:
            logger.error(f"Error updating configuration: {str(e)}")
            raise