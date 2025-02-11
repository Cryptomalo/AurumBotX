import logging
from typing import Dict, List, Optional, Union
import asyncio
from datetime import datetime
import pandas as pd
import numpy as np
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
        self.risk_limits = {
            'max_position_size': 0.1,  # 10% del portfolio
            'max_daily_loss': 0.02,    # 2% massima perdita giornaliera
            'stop_loss': 0.03,         # 3% stop loss per trade
            'take_profit': 0.05        # 5% take profit per trade
        }

    def _initialize_strategies(self):
        """Inizializza le strategie disponibili con configurazione avanzata"""
        self.available_strategies = {
            'scalping': {
                'class': ScalpingStrategy,
                'default_config': {
                    'timeframe': '1m',
                    'indicators': ['RSI', 'MACD', 'BB'],
                    'entry_rules': ['RSI_OVERSOLD', 'MACD_CROSS'],
                    'exit_rules': ['RSI_OVERBOUGHT', 'BB_UPPER'],
                    'risk_per_trade': 0.01
                }
            },
            'swing': {
                'class': SwingTradingStrategy,
                'default_config': {
                    'timeframe': '4h',
                    'indicators': ['EMA', 'RSI', 'VOLUME'],
                    'entry_rules': ['EMA_CROSS', 'VOLUME_SURGE'],
                    'exit_rules': ['TREND_REVERSAL', 'PROFIT_TARGET'],
                    'risk_per_trade': 0.02
                }
            },
            'dex_sniping': {
                'class': DexSnipingStrategy,
                'default_config': {
                    'min_liquidity': 5,
                    'max_buy_tax': 10,
                    'min_holders': 50,
                    'risk_per_trade': 0.005
                }
            },
            'meme_coin': {
                'class': MemeCoinStrategy,
                'default_config': {
                    'sentiment_threshold': 0.7,
                    'viral_coefficient': 0.8,
                    'risk_per_trade': 0.01
                }
            }
        }

    async def activate_strategy(self, strategy_name: str, config: Dict) -> bool:
        """Attiva una strategia di trading con gestione avanzata del rischio"""
        try:
            if strategy_name not in self.available_strategies:
                logger.error(f"Strategia {strategy_name} non trovata")
                return False

            # Merge default config with user config
            strategy_config = {
                **self.available_strategies[strategy_name]['default_config'],
                **config,
                'risk_limits': self.risk_limits
            }

            strategy_class = self.available_strategies[strategy_name]['class']
            strategy = strategy_class(strategy_config)
            self.active_strategies[strategy_name] = strategy

            # Inizializza il tracking avanzato delle performance
            self.strategy_performance[strategy_name] = {
                'start_time': datetime.now(),
                'trades': 0,
                'profit_loss': 0.0,
                'win_rate': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'volatility': 0.0,
                'risk_adjusted_return': 0.0
            }

            logger.info(f"Strategia {strategy_name} attivata con configurazione avanzata")
            return True

        except Exception as e:
            logger.error(f"Errore nell'attivazione della strategia {strategy_name}: {e}")
            return False

    async def execute_strategies(self, market_data: pd.DataFrame) -> List[Dict]:
        """Esegue tutte le strategie attive con gestione avanzata del rischio"""
        signals = []
        try:
            # Analisi tecnica avanzata
            market_data = self.indicators.add_all_indicators(market_data)

            # Analisi sentiment e mercato
            symbol = market_data['symbol'].iloc[0]
            sentiment_data = await self.sentiment_analyzer.analyze_social_sentiment(symbol)

            # Calcola risk score globale
            risk_score = self._calculate_risk_score(market_data, sentiment_data)

            # Esegue ogni strategia con controllo del rischio
            for strategy_name, strategy in self.active_strategies.items():
                try:
                    if self._check_risk_limits(strategy_name):
                        strategy_signals = await strategy.analyze_market(
                            market_data,
                            sentiment_data,
                            risk_score
                        )

                        if strategy_signals:
                            filtered_signals = self._filter_signals_by_risk(
                                strategy_signals,
                                strategy_name
                            )

                            for signal in filtered_signals:
                                signal['strategy'] = strategy_name
                                signal['risk_score'] = risk_score
                                signals.append(signal)

                            # Aggiorna statistiche avanzate
                            self._update_performance(strategy_name, filtered_signals)

                except Exception as e:
                    logger.error(f"Errore nell'esecuzione della strategia {strategy_name}: {e}")
                    continue

            return signals

        except Exception as e:
            logger.error(f"Errore nell'esecuzione delle strategie: {e}")
            return []

    def _calculate_risk_score(self, market_data: pd.DataFrame, sentiment_data: Dict) -> float:
        """Calcola un risk score composito"""
        try:
            # Volatilità del mercato
            volatility = market_data['Returns'].std() * np.sqrt(252)

            # Sentiment score
            sentiment_score = sentiment_data.get('score', 0.5)

            # Volume anomaly
            volume_ma = market_data['Volume'].rolling(20).mean()
            volume_ratio = market_data['Volume'].iloc[-1] / volume_ma.iloc[-1]

            # Trend strength
            trend_strength = self.indicators.calculate_trend_strength(market_data)

            # Composite risk score (0-1)
            risk_score = np.mean([
                volatility / 2,  # Normalize volatility
                1 - sentiment_score,
                min(volume_ratio / 5, 1),
                1 - trend_strength
            ])

            return min(max(risk_score, 0), 1)

        except Exception as e:
            logger.error(f"Errore nel calcolo del risk score: {e}")
            return 0.5

    def _check_risk_limits(self, strategy_name: str) -> bool:
        """Verifica i limiti di rischio per una strategia"""
        try:
            perf = self.strategy_performance[strategy_name]

            # Verifica perdita giornaliera massima
            if perf['profit_loss'] < -self.risk_limits['max_daily_loss']:
                logger.warning(f"Strategia {strategy_name} ha raggiunto il limite di perdita giornaliera")
                return False

            return True

        except Exception as e:
            logger.error(f"Errore nella verifica dei limiti di rischio: {e}")
            return False

    def _filter_signals_by_risk(
        self,
        signals: List[Dict],
        strategy_name: str
    ) -> List[Dict]:
        """Filtra i segnali in base al rischio"""
        try:
            filtered_signals = []
            for signal in signals:
                # Verifica dimensione posizione
                if signal.get('position_size', 0) > self.risk_limits['max_position_size']:
                    continue

                # Aggiungi stop loss e take profit
                signal['stop_loss'] = signal['entry_price'] * (1 - self.risk_limits['stop_loss'])
                signal['take_profit'] = signal['entry_price'] * (1 + self.risk_limits['take_profit'])

                filtered_signals.append(signal)

            return filtered_signals

        except Exception as e:
            logger.error(f"Errore nel filtraggio dei segnali: {e}")
            return []

    def _update_performance(self, strategy_name: str, signals: List[Dict]):
        """Aggiorna le statistiche avanzate di performance della strategia"""
        try:
            perf = self.strategy_performance[strategy_name]
            perf['trades'] += len(signals)

            # Aggiorna P&L e win rate
            profits = []
            for signal in signals:
                if 'profit_loss' in signal:
                    profit = signal['profit_loss']
                    perf['profit_loss'] += profit
                    profits.append(profit)

            if profits:
                # Calcola metriche avanzate
                returns = pd.Series(profits)
                perf['volatility'] = returns.std()
                perf['sharpe_ratio'] = self._calculate_sharpe_ratio(returns)
                perf['max_drawdown'] = self._calculate_max_drawdown(returns)

                # Win rate e risk-adjusted return
                winning_trades = sum(1 for p in profits if p > 0)
                perf['win_rate'] = (winning_trades / len(profits)) * 100
                perf['risk_adjusted_return'] = perf['profit_loss'] / (perf['volatility'] or 1)

        except Exception as e:
            logger.error(f"Errore nell'aggiornamento performance: {e}")

    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calcola Sharpe Ratio annualizzato"""
        try:
            if returns.empty:
                return 0.0
            rf_rate = 0.02  # Risk-free rate
            excess_returns = returns - (rf_rate / 252)
            if excess_returns.std() == 0:
                return 0.0
            sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
            return float(sharpe)
        except Exception as e:
            logger.error(f"Errore nel calcolo dello Sharpe Ratio: {e}")
            return 0.0

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calcola il Maximum Drawdown"""
        try:
            if returns.empty:
                return 0.0
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            return float(abs(drawdown.min()))
        except Exception as e:
            logger.error(f"Errore nel calcolo del Maximum Drawdown: {e}")
            return 0.0

    def get_performance_metrics(self) -> Dict[str, Dict]:
        """Restituisce metriche di performance complete per tutte le strategie"""
        return self.strategy_performance

    def optimize_strategies(self, market_conditions: Dict) -> None:
        """Ottimizza i parametri delle strategie in base alle condizioni di mercato"""
        try:
            for strategy_name, strategy in self.active_strategies.items():
                perf = self.strategy_performance[strategy_name]

                # Aggiusta parametri in base alle performance
                if perf['sharpe_ratio'] < 1.0:
                    # Riduci il rischio
                    strategy.config['risk_per_trade'] *= 0.8
                elif perf['win_rate'] < 40:
                    # Aggiusta parametri di entrata/uscita
                    strategy.optimize_parameters(market_conditions)

                logger.info(f"Strategia {strategy_name} ottimizzata")

        except Exception as e:
            logger.error(f"Errore nell'ottimizzazione delle strategie: {e}")

    async def deactivate_strategy(self, strategy_name: str) -> bool:
        """Disattiva una strategia con cleanup"""
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