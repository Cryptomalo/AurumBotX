import logging
from typing import Dict, List, Optional
import asyncio
from datetime import datetime
import pandas as pd
from utils.indicators import TechnicalIndicators
from utils.sentiment_analyzer import SentimentAnalyzer
from utils.strategies.base_strategy import BaseStrategy
from utils.strategies.scalping import ScalpingStrategy
from utils.strategies.swing_trading import SwingTradingStrategy
from utils.strategies.dex_sniping import DexSnipingStrategy
from utils.strategies.meme_coin_sniping import MemeCoinStrategy

logger = logging.getLogger(__name__)

class StrategyManager:
    def __init__(self):
        self.indicators = TechnicalIndicators()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.active_strategies: Dict[str, BaseStrategy] = {}
        self.strategy_performance: Dict[str, Dict] = {}
        self._initialize_strategies()

    def _initialize_strategies(self):
        """Inizializza le strategie disponibili"""
        self.available_strategies = {
            'scalping': ScalpingStrategy,
            'swing': SwingTradingStrategy,
            'dex_sniping': DexSnipingStrategy,
            'meme_coin': MemeCoinStrategy
        }

    async def activate_strategy(self, strategy_name: str, config: Dict) -> bool:
        """Attiva una strategia di trading"""
        try:
            if strategy_name not in self.available_strategies:
                logger.error(f"Strategia {strategy_name} non trovata")
                return False

            strategy_class = self.available_strategies[strategy_name]
            strategy = strategy_class(config)
            self.active_strategies[strategy_name] = strategy
            
            # Inizializza il tracking delle performance
            self.strategy_performance[strategy_name] = {
                'start_time': datetime.now(),
                'trades': 0,
                'profit_loss': 0.0,
                'win_rate': 0.0
            }
            
            logger.info(f"Strategia {strategy_name} attivata con successo")
            return True

        except Exception as e:
            logger.error(f"Errore nell'attivazione della strategia {strategy_name}: {e}")
            return False

    async def execute_strategies(self, market_data: pd.DataFrame) -> List[Dict]:
        """Esegue tutte le strategie attive"""
        signals = []
        try:
            # Analisi tecnica
            market_data = self.indicators.add_all_indicators(market_data)
            
            # Analisi sentiment
            sentiment_data = await self.sentiment_analyzer.analyze_social_sentiment(
                market_data['symbol'].iloc[0]
            )

            # Esegue ogni strategia attiva
            for strategy_name, strategy in self.active_strategies.items():
                try:
                    strategy_signals = await strategy.analyze_market(
                        market_data,
                        sentiment_data
                    )
                    
                    if strategy_signals:
                        for signal in strategy_signals:
                            signal['strategy'] = strategy_name
                            signals.append(signal)
                            
                        # Aggiorna statistiche
                        self._update_performance(strategy_name, strategy_signals)
                        
                except Exception as e:
                    logger.error(f"Errore nell'esecuzione della strategia {strategy_name}: {e}")
                    continue

            return signals

        except Exception as e:
            logger.error(f"Errore nell'esecuzione delle strategie: {e}")
            return []

    def _update_performance(self, strategy_name: str, signals: List[Dict]):
        """Aggiorna le statistiche di performance della strategia"""
        try:
            perf = self.strategy_performance[strategy_name]
            perf['trades'] += len(signals)
            
            # Calcola P&L e win rate
            for signal in signals:
                if 'profit_loss' in signal:
                    perf['profit_loss'] += signal['profit_loss']
                    
            if perf['trades'] > 0:
                winning_trades = sum(1 for s in signals if s.get('profit_loss', 0) > 0)
                perf['win_rate'] = (winning_trades / perf['trades']) * 100
                
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento performance: {e}")

    def get_performance_metrics(self) -> Dict[str, Dict]:
        """Restituisce le metriche di performance per tutte le strategie"""
        return self.strategy_performance

    def optimize_strategies(self, market_conditions: Dict) -> None:
        """Ottimizza i parametri delle strategie in base alle condizioni di mercato"""
        try:
            for strategy in self.active_strategies.values():
                if hasattr(strategy, 'optimize_parameters'):
                    strategy.optimize_parameters(market_conditions)
        except Exception as e:
            logger.error(f"Errore nell'ottimizzazione delle strategie: {e}")

    async def deactivate_strategy(self, strategy_name: str) -> bool:
        """Disattiva una strategia"""
        try:
            if strategy_name in self.active_strategies:
                await self.active_strategies[strategy_name].cleanup()
                del self.active_strategies[strategy_name]
                logger.info(f"Strategia {strategy_name} disattivata")
                return True
            return False
        except Exception as e:
            logger.error(f"Errore nella disattivazione della strategia {strategy_name}: {e}")
            return False
