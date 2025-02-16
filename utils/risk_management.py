import logging
from typing import Dict, Any, Optional
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Default risk parameters
        self.max_position_size = 0.1  # 10% of portfolio
        self.max_risk_per_trade = 0.02  # 2% risk per trade
        self.max_daily_risk = 0.05  # 5% max daily risk
        self.min_risk_reward_ratio = 2.0
        
    def calculate_position_size(self, 
                              portfolio_value: float,
                              entry_price: float,
                              stop_loss: float,
                              confidence: float = 0.5) -> Dict[str, float]:
        """Calculate optimal position size based on risk parameters"""
        try:
            # Calculate basic position size based on max risk per trade
            risk_amount = portfolio_value * self.max_risk_per_trade
            
            # Calculate position size based on stop loss distance
            price_risk = abs(entry_price - stop_loss) / entry_price
            if price_risk == 0:
                return {'size': 0, 'risk_amount': 0}
                
            base_position = risk_amount / price_risk
            
            # Adjust based on confidence
            adjusted_position = base_position * (0.5 + confidence/2)
            
            # Ensure we don't exceed max position size
            max_position = portfolio_value * self.max_position_size
            final_position = min(adjusted_position, max_position)
            
            return {
                'size': final_position,
                'risk_amount': final_position * price_risk
            }
            
        except Exception as e:
            self.logger.error(f"Position size calculation error: {str(e)}")
            return {'size': 0, 'risk_amount': 0}
            
    def validate_trade(self,
                      entry_price: float,
                      take_profit: float,
                      stop_loss: float,
                      position_size: float,
                      portfolio_value: float) -> Dict[str, Any]:
        """Validate if trade meets risk management criteria"""
        try:
            # Calculate risk-reward ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Calculate position risk
            position_risk = (position_size * risk / entry_price) / portfolio_value
            
            # Validate against criteria
            validations = {
                'risk_reward_valid': risk_reward_ratio >= self.min_risk_reward_ratio,
                'position_size_valid': position_size <= (portfolio_value * self.max_position_size),
                'risk_per_trade_valid': position_risk <= self.max_risk_per_trade,
                'metrics': {
                    'risk_reward_ratio': risk_reward_ratio,
                    'position_risk_percent': position_risk * 100
                }
            }
            
            validations['valid'] = all([
                validations['risk_reward_valid'],
                validations['position_size_valid'],
                validations['risk_per_trade_valid']
            ])
            
            return validations
            
        except Exception as e:
            self.logger.error(f"Trade validation error: {str(e)}")
            return {'valid': False, 'error': str(e)}
            
    def update_risk_parameters(self, 
                             performance_metrics: Dict[str, float],
                             market_volatility: float):
        """Dynamically adjust risk parameters based on performance"""
        try:
            # Adjust max position size based on win rate
            win_rate = performance_metrics.get('win_rate', 0.5)
            if win_rate > 0.6:
                self.max_position_size = min(0.15, self.max_position_size * 1.1)
            elif win_rate < 0.4:
                self.max_position_size = max(0.05, self.max_position_size * 0.9)
                
            # Adjust risk per trade based on volatility
            if market_volatility > 0.02:  # High volatility
                self.max_risk_per_trade = max(0.01, self.max_risk_per_trade * 0.9)
            else:
                self.max_risk_per_trade = min(0.03, self.max_risk_per_trade * 1.1)
                
        except Exception as e:
            self.logger.error(f"Risk parameter update error: {str(e)}")
