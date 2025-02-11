
import pandas as pd
from typing import Dict, Any
import numpy as np

class SocialTradingManager:
    def __init__(self):
        self.traders = {}
        self.performance_metrics = {}
        self.copy_settings = {}
        
    def add_trader(self, trader_id: str, strategy_config: Dict[str, Any]):
        """Aggiunge un nuovo trader da seguire"""
        self.traders[trader_id] = {
            'strategy': strategy_config,
            'performance': {
                'win_rate': 0,
                'profit_factor': 0,
                'avg_return': 0
            }
        }
        
    def copy_trade(self, trader_id: str, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Copia trade da trader selezionato con gestione rischio"""
        if trader_id not in self.traders:
            return None
            
        # Applica filtri e modificatori
        risk_factor = self.copy_settings.get('risk_factor', 1.0)
        min_confidence = self.copy_settings.get('min_confidence', 0.7)
        
        if signal['confidence'] < min_confidence:
            return None
            
        modified_signal = signal.copy()
        modified_signal['size_factor'] *= risk_factor
        
        return modified_signal
        
    def update_performance(self, trader_id: str, trade_result: Dict[str, Any]):
        """Aggiorna metriche performance trader"""
        if trader_id in self.traders:
            perf = self.traders[trader_id]['performance']
            perf['win_rate'] = self._calculate_win_rate(trade_result)
            perf['profit_factor'] = self._calculate_profit_factor(trade_result)
            perf['avg_return'] = self._calculate_avg_return(trade_result)
