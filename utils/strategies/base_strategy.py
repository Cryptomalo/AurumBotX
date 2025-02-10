from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any

class BaseStrategy(ABC):
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.is_active = False

    @abstractmethod
    def analyze_market(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analizza il mercato e genera segnali di trading
        Returns:
            Dict con i segnali di trading e le metriche
        """
        pass

    @abstractmethod
    def generate_signals(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera segnali di trading basati sull'analisi
        Returns:
            Dict con le decisioni di trading
        """
        pass

    @abstractmethod
    def validate_trade(self, signal: Dict[str, Any], current_portfolio: Dict[str, Any]) -> bool:
        """
        Valida un potenziale trade prima dell'esecuzione
        Returns:
            bool: True se il trade è valido
        """
        pass

    def get_name(self) -> str:
        return self.name

    def is_strategy_active(self) -> bool:
        return self.is_active

    def activate(self):
        self.is_active = True

    def deactivate(self):
        self.is_active = False
