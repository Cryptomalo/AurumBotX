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
    async def analyze_market(self, market_data: pd.DataFrame, sentiment_data: Optional[Dict] = None) -> List[Dict]:
        """
        Analizza il mercato e genera segnali di trading
        Args:
            market_data: DataFrame con i dati di mercato
            sentiment_data: Dati opzionali del sentiment dai social media
        Returns:
            Lista di segnali di trading
        """
        pass

    @abstractmethod
    async def validate_trade(self, signal: Dict[str, Any], portfolio: Dict[str, Any]) -> bool:
        """
        Valida un potenziale trade prima dell'esecuzione
        Args:
            signal: Segnale di trading da validare
            portfolio: Stato attuale del portfolio
        Returns:
            bool: True se il trade è valido
        """
        pass

    @abstractmethod
    async def execute_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Esegue un trade basato sul segnale
        Args:
            signal: Segnale di trading da eseguire
        Returns:
            Risultato dell'esecuzione del trade
        """
        pass

    def update_performance(self, trade_result: Dict[str, Any]):
        """Aggiorna le metriche di performance della strategia"""
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

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Restituisce le metriche di performance attuali"""
        return {
            **self.performance_metrics,
            'last_update': datetime.now().isoformat()
        }

    async def cleanup(self):
        """Pulizia risorse della strategia"""
        self.is_active = False
        logger.info(f"Strategia {self.name} disattivata")

    def optimize_parameters(self, market_conditions: Dict[str, Any]):
        """Ottimizza i parametri della strategia in base alle condizioni di mercato"""
        pass  # Implementato nelle sottoclassi

    def get_name(self) -> str:
        return self.name

    def is_strategy_active(self) -> bool:
        return self.is_active

    def activate(self):
        self.is_active = True
        logger.info(f"Strategia {self.name} attivata")

    def deactivate(self):
        self.is_active = False
        logger.info(f"Strategia {self.name} disattivata")

    def get_config(self) -> Dict[str, Any]:
        """Restituisce la configurazione corrente della strategia"""
        return {
            'name': self.name,
            'config': self.config,
            'is_active': self.is_active,
            'performance_metrics': self.performance_metrics,
            'timestamp': datetime.now().isoformat()
        }

    def set_config(self, config: Dict[str, Any]):
        """Imposta la configurazione della strategia"""
        try:
            self.name = config.get('name', self.name)
            self.config.update(config.get('config', {}))
            self.is_active = config.get('is_active', self.is_active)
            if 'performance_metrics' in config:
                self.performance_metrics.update(config['performance_metrics'])
            logger.info(f"Configurazione aggiornata per strategia {self.name}")
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento della configurazione: {str(e)}")
            raise