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
            'max_position_size': 0.1,  # 10% massimo per posizione
            'max_daily_loss': 0.02,    # 2% massimo di perdita giornaliera
            'stop_loss': 0.03,         # 3% stop loss per trade
            'take_profit': 0.05        # 5% take profit per trade
        }
        self.is_live_testing = False
        self.test_start_time = None

    async def configure_for_live_testing(self):
        """Configura il manager e le strategie per il testing con dati reali"""
        try:
            logger.info("Configuring StrategyManager for live testing...")
            self.is_live_testing = True
            self.test_start_time = datetime.now()

            # Configura limiti di rischio più conservativi per il testing
            self.risk_limits.update({
                'max_position_size': 0.05,  # Ridotto al 5%
                'max_daily_loss': 0.01,     # Ridotto all'1%
                'stop_loss': 0.02,          # Ridotto al 2%
                'take_profit': 0.03         # Ridotto al 3%
            })

            # Configura ogni strategia attiva per il live testing
            for strategy_name, strategy in self.active_strategies.items():
                logger.info(f"Configuring strategy {strategy_name} for live testing")
                if hasattr(strategy, 'configure_for_live_testing'):
                    await strategy.configure_for_live_testing()

                # Reset performance metrics per il nuovo test
                self.strategy_performance[strategy_name] = {
                    'start_time': self.test_start_time,
                    'trades': 0,
                    'profit_loss': 0.0,
                    'win_rate': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'volatility': 0.0,
                    'risk_adjusted_return': 0.0
                }

            logger.info("StrategyManager successfully configured for live testing")
            return True

        except Exception as e:
            logger.error(f"Error configuring for live testing: {str(e)}")
            self.is_live_testing = False
            return False

    async def cleanup(self):
        """Pulisce le risorse e chiude le connessioni"""
        try:
            logger.info("Starting StrategyManager cleanup...")

            # Disattiva il modalità live testing
            self.is_live_testing = False

            # Cleanup per ogni strategia attiva
            for strategy_name, strategy in list(self.active_strategies.items()):
                try:
                    logger.info(f"Cleaning up strategy {strategy_name}")
                    if hasattr(strategy, 'cleanup'):
                        await strategy.cleanup()

                    # Salva le performance finali
                    if strategy_name in self.strategy_performance:
                        end_time = datetime.now()
                        duration = end_time - self.strategy_performance[strategy_name]['start_time']
                        logger.info(f"Strategy {strategy_name} ran for {duration}")
                        logger.info(f"Final performance metrics: {self.strategy_performance[strategy_name]}")

                    # Rimuovi la strategia dalla lista attive
                    del self.active_strategies[strategy_name]

                except Exception as e:
                    logger.error(f"Error cleaning up strategy {strategy_name}: {str(e)}")

            # Reset delle variabili interne
            self.strategy_performance.clear()
            self.test_start_time = None

            logger.info("StrategyManager cleanup completed successfully")
            return True

        except Exception as e:
            logger.error(f"Error during StrategyManager cleanup: {str(e)}")
            return False

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
        """Calcola un risk score composito basato su multipli fattori"""
        try:
            # Volatilità del mercato (ATR e BB Width)
            volatility_atr = market_data['ATR'].iloc[-1] / market_data['Close'].iloc[-1]
            volatility_bb = market_data['BB_Width'].iloc[-1]
            volatility_score = (volatility_atr + volatility_bb) / 2

            # Momentum e trend strength
            momentum_score = 0.0
            if 'ROC' in market_data.columns and 'MFI' in market_data.columns:
                roc = market_data['ROC'].iloc[-1]
                mfi = market_data['MFI'].iloc[-1]
                momentum_score = (
                    (roc / 100 if abs(roc) < 100 else np.sign(roc)) +
                    (mfi / 100)
                ) / 2

            # Volume analysis
            volume_ratio = market_data['Volume_Ratio'].iloc[-1]
            volume_score = min(volume_ratio / 3, 1.0)  # Normalize

            # Trend analysis usando multiple MA
            sma_scores = []
            for period in [20, 50, 200]:
                if f'SMA_{period}' in market_data.columns:
                    current_price = market_data['Close'].iloc[-1]
                    sma = market_data[f'SMA_{period}'].iloc[-1]
                    sma_scores.append(1 if current_price > sma else 0)
            trend_score = sum(sma_scores) / len(sma_scores) if sma_scores else 0.5

            # MACD signal
            macd_score = 0.5
            if all(x in market_data.columns for x in ['MACD', 'Signal']):
                macd = market_data['MACD'].iloc[-1]
                signal = market_data['Signal'].iloc[-1]
                macd_score = 1 if macd > signal else 0

            # RSI analysis
            rsi_score = 0.5
            if 'RSI' in market_data.columns:
                rsi = market_data['RSI'].iloc[-1]
                rsi_score = (
                    0.9 if rsi < 30 else  # Oversold
                    0.1 if rsi > 70 else  # Overbought
                    0.5  # Neutral
                )

            # Sentiment integration
            sentiment_score = sentiment_data.get('score', 0.5)
            sentiment_confidence = sentiment_data.get('confidence', 0.5)
            adjusted_sentiment = sentiment_score * sentiment_confidence

            # Composite risk score (0-1)
            weights = {
                'volatility': 0.25,
                'momentum': 0.15,
                'volume': 0.10,
                'trend': 0.20,
                'macd': 0.10,
                'rsi': 0.10,
                'sentiment': 0.10
            }

            risk_score = sum([
                weights['volatility'] * volatility_score,
                weights['momentum'] * momentum_score,
                weights['volume'] * volume_score,
                weights['trend'] * trend_score,
                weights['macd'] * macd_score,
                weights['rsi'] * rsi_score,
                weights['sentiment'] * adjusted_sentiment
            ])

            # Normalize final score
            return min(max(risk_score, 0), 1)

        except Exception as e:
            logger.error(f"Errore nel calcolo del risk score: {e}", exc_info=True)
            return 0.5  # Default a rischio medio in caso di errore

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
                # Verifica dimensione posizione massima
                if signal.get('position_size', 0) > self.risk_limits['max_position_size']:
                    continue

                # Calcola stop loss dinamico basato su ATR
                atr = signal.get('atr', self.risk_limits['stop_loss'])
                dynamic_stop = min(
                    atr * 2,  # 2x ATR come massimo stop loss
                    self.risk_limits['stop_loss']  # Limite massimo configurato
                )

                # Applica il position sizing ottimale
                risk_per_trade = signal.get('risk_per_trade', 0.01)  # 1% default
                position_size = self._calculate_position_size(
                    signal['entry_price'],
                    dynamic_stop,
                    risk_per_trade
                )

                # Aggiorna il segnale con i nuovi parametri
                signal.update({
                    'stop_loss': signal['entry_price'] * (1 - dynamic_stop),
                    'take_profit': signal['entry_price'] * (1 + (dynamic_stop * 1.5)),  # Risk:Reward 1:1.5
                    'position_size': position_size,
                    'max_loss': position_size * dynamic_stop  # Perdita massima potenziale
                })

                filtered_signals.append(signal)

            return filtered_signals

        except Exception as e:
            logger.error(f"Errore nel filtraggio dei segnali: {e}")
            return []

    def _calculate_position_size(
        self,
        entry_price: float,
        stop_loss_pct: float,
        risk_per_trade: float
    ) -> float:
        """Calcola la dimensione ottimale della posizione"""
        try:
            # Implementa il modello di Kelly Criterion modificato
            win_rate = self.strategy_performance.get('win_rate', 50) / 100
            if win_rate < 0.5:  # Se win rate < 50%, riduci il rischio
                risk_per_trade *= 0.5

            # Calcola il position size ottimale
            account_size = 1.0  # Normalizzato a 1 (100%)
            risk_amount = account_size * risk_per_trade
            position_size = risk_amount / stop_loss_pct

            # Applica limiti di sicurezza
            max_position = self.risk_limits['max_position_size']
            return min(position_size, max_position)

        except Exception as e:
            logger.error(f"Errore nel calcolo del position size: {e}")
            return self.risk_limits['max_position_size'] * 0.5  # Default a metà del massimo

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

                # Performance-based optimization
                if perf['sharpe_ratio'] < 1.0 or perf['max_drawdown'] > 0.1:
                    # Riduci il rischio se la performance è scarsa
                    strategy.config['risk_per_trade'] *= 0.8
                    strategy.config['position_size_limit'] *= 0.8
                    logger.info(f"Reduced risk for {strategy_name} due to poor performance")

                elif perf['win_rate'] < 45:
                    # Aggiusta timeframe e parametri se win rate è basso
                    if 'timeframe' in strategy.config:
                        # Move to higher timeframe for more reliable signals
                        current_tf = strategy.config['timeframe']
                        if current_tf == '1m':
                            strategy.config['timeframe'] = '5m'
                        elif current_tf == '5m':
                            strategy.config['timeframe'] = '15m'
                    logger.info(f"Adjusted timeframe for {strategy_name} due to low win rate")

                elif perf['volatility'] > 0.02:  # 2% daily volatility
                    # Increase minimum confidence threshold in volatile markets
                    strategy.config['min_confidence'] = min(
                        0.8,
                        strategy.config.get('min_confidence', 0.5) + 0.1
                    )
                    logger.info(f"Increased confidence threshold for {strategy_name} due to high volatility")

                # Market condition based optimization
                if market_conditions.get('trend') == 'ranging':
                    # In ranging markets, focus on mean reversion
                    strategy.config['mean_reversion_weight'] = 0.7
                    strategy.config['trend_following_weight'] = 0.3
                elif market_conditions.get('trend') == 'trending':
                    # In trending markets, focus on trend following
                    strategy.config['mean_reversion_weight'] = 0.3
                    strategy.config['trend_following_weight'] = 0.7

                # Volatility based optimization
                if market_conditions.get('volatility', 0) > 0.02:
                    # In high volatility, widen stops and reduce position size
                    strategy.config['stop_loss_multiplier'] = 1.5
                    strategy.config['position_size_multiplier'] = 0.7
                else:
                    # In low volatility, tighten stops and increase position size
                    strategy.config['stop_loss_multiplier'] = 1.0
                    strategy.config['position_size_multiplier'] = 1.0

                logger.info(f"Strategy {strategy_name} ottimizzata")

        except Exception as e:
            logger.error(f"Errore nell'ottimizzazione delle strategie: {e}", exc_info=True)

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

    async def validate_optimization(self, strategy_name: str, market_data: pd.DataFrame) -> Dict:
        """Valida le modifiche alla strategia attraverso backtesting"""
        try:
            if strategy_name not in self.active_strategies:
                return {'valid': False, 'error': 'Strategia non trovata'}

            strategy = self.active_strategies[strategy_name]
            original_config = strategy.config.copy()

            # Esegui backtest con configurazione originale
            original_results = await self._run_backtest(strategy, market_data)

            # Ottimizza la strategia
            market_conditions = self._analyze_market_conditions(market_data)
            self.optimize_strategies(market_conditions)

            # Esegui backtest con nuova configurazione
            new_results = await self._run_backtest(strategy, market_data)

            # Confronta i risultati
            improvements = {
                'sharpe_ratio': new_results['sharpe_ratio'] - original_results['sharpe_ratio'],
                'max_drawdown': original_results['max_drawdown'] - new_results['max_drawdown'],
                'win_rate': new_results['win_rate'] - original_results['win_rate'],
                'profit_factor': new_results['profit_factor'] - original_results['profit_factor']
            }

            # Verifica se le modifiche sono effettivamente migliorative
            is_better = (
                improvements['sharpe_ratio'] > 0 and
                improvements['max_drawdown'] > 0 and
                improvements['win_rate'] > -5  # Allow small decrease in win rate if other metrics improve
            )

            if not is_better:
                # Ripristina configurazione originale
                strategy.config = original_config
                logger.warning(f"Optimization reverted for {strategy_name} - no improvement")
                return {
                    'valid': False,
                    'improvements': improvements,
                    'message': 'Optimization did not improve performance'
                }

            logger.info(f"Optimization validated for {strategy_name}")
            return {
                'valid': True,
                'improvements': improvements,
                'message': 'Optimization improved performance'
            }

        except Exception as e:
            logger.error(f"Error validating optimization: {e}", exc_info=True)
            return {'valid': False, 'error': str(e)}

    def _analyze_market_conditions(self, market_data: pd.DataFrame) -> Dict:
        """Analizza le condizioni di mercato per l'ottimizzazione"""
        try:
            latest_data = market_data.tail(100)  # Analizza ultimi 100 periodi

            # Calcola trend
            sma20 = latest_data['Close'].rolling(20).mean()
            sma50 = latest_data['Close'].rolling(50).mean()
            trend_strength = abs(sma20.iloc[-1] - sma50.iloc[-1]) / sma50.iloc[-1]

            # Calcola volatilità
            volatility = latest_data['Returns'].std() * np.sqrt(252)

            # Identifica regime di mercato
            if trend_strength < 0.01:  # 1% difference between SMAs
                market_type = 'ranging'
            else:
                market_type = 'trending'

            return {
                'trend': market_type,
                'trend_strength': trend_strength,
                'volatility': volatility,
                'volume_profile': latest_data['Volume_Ratio'].mean(),
                'avg_true_range': latest_data['ATR'].mean()
            }

        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}", exc_info=True)
            return {}

    async def _run_backtest(self, strategy: BaseStrategy, market_data: pd.DataFrame) -> Dict:
        """Esegue backtest della strategia"""
        try:
            signals = []
            metrics = {
                'total_trades': 0,
                'winning_trades': 0,
                'total_profit': 0,
                'max_drawdown': 0,
                'returns': []
            }

            # Simula trading su dati storici
            for i in range(len(market_data) - 1):
                data_slice = market_data.iloc[:i+1]
                new_signals = await strategy.analyze_market(
                    data_slice,
                    {'score': 0.5, 'confidence': 0.5},  # Default sentiment
                    0.5  # Default risk score
                )

                for signal in new_signals:
                    metrics['total_trades'] += 1

                    # Simula risultato trade
                    entry_price = signal['entry_price']
                    next_price = market_data['Close'].iloc[i+1]
                    profit_loss = (next_price - entry_price) / entry_price

                    if profit_loss > 0:
                        metrics['winning_trades'] += 1

                    metrics['total_profit'] += profit_loss
                    metrics['returns'].append(profit_loss)

                    # Aggiorna max drawdown
                    if len(metrics['returns']) > 0:
                        cumulative = pd.Series(metrics['returns']).cumsum()
                        drawdown = (cumulative - cumulative.expanding().max())
                        metrics['max_drawdown'] = abs(min(drawdown.min(), metrics['max_drawdown']))

            # Calcola metriche finali
            if metrics['total_trades'] > 0:
                win_rate = (metrics['winning_trades'] / metrics['total_trades']) * 100
                returns_series = pd.Series(metrics['returns'])
                sharpe_ratio = self._calculate_sharpe_ratio(returns_series)
                profit_factor = abs(sum(x for x in metrics['returns'] if x > 0) / 
                                  sum(abs(x) for x in metrics['returns'] if x < 0))
            else:
                win_rate = 0
                sharpe_ratio = 0
                profit_factor = 0

            return {
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': metrics['max_drawdown'],
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'total_trades': metrics['total_trades']
            }

        except Exception as e:
            logger.error(f"Error in backtest: {e}", exc_info=True)
            return {
                'sharpe_ratio': 0,
                'max_drawdown': 1,
                'win_rate': 0,
                'profit_factor': 0,
                'total_trades': 0
            }