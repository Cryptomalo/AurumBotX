import pandas as pd
from typing import Dict, Any, Optional
import numpy as np
from datetime import datetime

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

    def copy_trade(self, trader_id: str, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Copia trade da trader selezionato con gestione rischio"""
        if trader_id not in self.traders:
            return {
                'error': 'Trader non trovato',
                'trader_id': trader_id,
                'timestamp': datetime.now().isoformat()
            }

        # Applica filtri e modificatori
        risk_factor = self.copy_settings.get('risk_factor', 1.0)
        min_confidence = self.copy_settings.get('min_confidence', 0.7)

        if signal['confidence'] < min_confidence:
            return {
                'error': 'Confidence troppo bassa',
                'confidence': signal['confidence'],
                'min_required': min_confidence,
                'timestamp': datetime.now().isoformat()
            }

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

    def _calculate_win_rate(self, trade_result: Dict[str, Any]) -> float:
        """Calcola il win rate basato sui risultati del trade"""
        try:
            total_trades = trade_result.get('total_trades', 0)
            if total_trades == 0:
                return 0.0

            winning_trades = trade_result.get('winning_trades', 0)
            return (winning_trades / total_trades) * 100

        except Exception:
            return 0.0

    def _calculate_profit_factor(self, trade_result: Dict[str, Any]) -> float:
        """Calcola il profit factor basato sui risultati del trade"""
        try:
            total_profit = trade_result.get('total_profit', 0.0)
            total_loss = abs(trade_result.get('total_loss', 0.0))

            if total_loss == 0:
                return 1.0 if total_profit > 0 else 0.0

            return total_profit / total_loss

        except Exception:
            return 0.0

    def _calculate_avg_return(self, trade_result: Dict[str, Any]) -> float:
        """Calcola il ritorno medio per trade"""
        try:
            total_trades = trade_result.get('total_trades', 0)
            if total_trades == 0:
                return 0.0

            net_profit = trade_result.get('total_profit', 0.0) - abs(trade_result.get('total_loss', 0.0))
            return net_profit / total_trades

        except Exception:
            return 0.0