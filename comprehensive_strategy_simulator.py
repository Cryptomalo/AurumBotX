#!/usr/bin/env python3
"""
Simulatore Completo Strategie AurumBotX
Simula e compara tutte le strategie disponibili con dati reali
"""

import os
import sys
import asyncio
import logging
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns

# Aggiungi path del progetto
sys.path.append('/home/ubuntu/AurumBotX')

from utils.ai_trading import AITrading
from utils.data_loader import CryptoDataLoader
from utils.strategies.swing_trading import SwingTradingStrategy
from utils.strategies.scalping import ScalpingStrategy

class ComprehensiveStrategySimulator:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('StrategySimulator')
        self.results = {}
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def print_header(self, title):
        """Header professionale"""
        print(f"\n{'='*100}")
        print(f"🎯 {title}")
        print(f"{'='*100}")
        
    def print_section(self, title):
        """Sezione"""
        print(f"\n📋 {title}")
        print(f"{'-'*80}")
    
    async def run_comprehensive_simulation(self):
        """Esegue simulazione completa di tutte le strategie"""
        self.print_header("SIMULAZIONE COMPLETA STRATEGIE AURUMBOTX")
        
        try:
            # 1. Inizializzazione
            await self.initialize_components()
            
            # 2. Configurazioni strategie
            strategy_configs = self.get_strategy_configurations()
            
            # 3. Ottieni dati di mercato
            market_data = await self.get_market_data()
            
            # 4. Simula ogni strategia
            for strategy_name, config in strategy_configs.items():
                self.logger.info(f"🔄 Simulazione strategia: {strategy_name}")
                result = await self.simulate_strategy(strategy_name, config, market_data)
                self.results[strategy_name] = result
            
            # 5. Analisi comparativa
            await self.comparative_analysis()
            
            # 6. Raccomandazioni
            await self.generate_recommendations()
            
            # 7. Salva risultati
            await self.save_results()
            
        except Exception as e:
            self.logger.error(f"❌ Errore simulazione: {e}")
            import traceback
            traceback.print_exc()
    
    async def initialize_components(self):
        """Inizializza componenti necessari"""
        self.print_section("INIZIALIZZAZIONE COMPONENTI")
        
        self.data_loader = CryptoDataLoader(use_live_data=True, testnet=True)
        await self.data_loader.initialize()
        print("  ✅ Data Loader inizializzato")
        
        self.ai_trading = AITrading()
        await self.ai_trading.initialize()
        print("  ✅ AI Trading inizializzato")
        
        print("  ✅ Tutti i componenti inizializzati")
    
    def get_strategy_configurations(self):
        """Definisce configurazioni per tutte le strategie"""
        self.print_section("CONFIGURAZIONI STRATEGIE")
        
        configs = {
            "swing_trading_conservative": {
                "type": "swing",
                "profit_target": 0.03,  # 3%
                "stop_loss": 0.02,      # 2%
                "trend_period": 20,
                "min_trend_strength": 0.4,
                "description": "Swing Trading Conservativo"
            },
            "swing_trading_moderate": {
                "type": "swing", 
                "profit_target": 0.05,  # 5%
                "stop_loss": 0.03,      # 3%
                "trend_period": 20,
                "min_trend_strength": 0.6,
                "description": "Swing Trading Moderato (Attuale)"
            },
            "swing_trading_aggressive": {
                "type": "swing",
                "profit_target": 0.08,  # 8%
                "stop_loss": 0.05,      # 5%
                "trend_period": 14,
                "min_trend_strength": 0.7,
                "description": "Swing Trading Aggressivo"
            },
            "scalping_conservative": {
                "type": "scalping",
                "profit_target": 0.005, # 0.5%
                "stop_loss": 0.003,     # 0.3%
                "trend_period": 5,
                "min_trend_strength": 0.3,
                "description": "Scalping Conservativo"
            },
            "scalping_moderate": {
                "type": "scalping",
                "profit_target": 0.01,  # 1%
                "stop_loss": 0.007,     # 0.7%
                "trend_period": 10,
                "min_trend_strength": 0.5,
                "description": "Scalping Moderato"
            },
            "scalping_aggressive": {
                "type": "scalping",
                "profit_target": 0.02,  # 2%
                "stop_loss": 0.015,     # 1.5%
                "trend_period": 15,
                "min_trend_strength": 0.6,
                "description": "Scalping Aggressivo"
            }
        }
        
        for name, config in configs.items():
            print(f"  📊 {config['description']}")
            print(f"    🎯 Profit: {config['profit_target']:.1%} | 🛡️ Stop: {config['stop_loss']:.1%}")
            print(f"    📈 Period: {config['trend_period']} | 💪 Strength: {config['min_trend_strength']:.1%}")
        
        return configs
    
    async def get_market_data(self):
        """Ottieni dati di mercato per simulazione"""
        self.print_section("DATI MERCATO PER SIMULAZIONE")
        
        # Ottieni dati storici per diversi timeframe
        timeframes = ['1h', '4h', '1d']
        market_data = {}
        
        for tf in timeframes:
            self.logger.info(f"📊 Recupero dati {tf}...")
            data = await self.data_loader.get_historical_data('BTCUSDT', '30d', tf)
            
            if data is not None and not data.empty:
                market_data[tf] = data
                print(f"  ✅ {tf}: {len(data)} candele")
            else:
                print(f"  ❌ {tf}: Nessun dato")
        
        return market_data
    
    async def simulate_strategy(self, strategy_name: str, config: Dict, market_data: Dict):
        """Simula una strategia specifica"""
        self.print_section(f"SIMULAZIONE: {config['description']}")
        
        try:
            # Inizializza strategia
            if config['type'] == 'swing':
                strategy = SwingTradingStrategy(config)
            elif config['type'] == 'scalping':
                strategy = ScalpingStrategy(config)
            else:
                raise ValueError(f"Tipo strategia non supportato: {config['type']}")
            
            # Simula su diversi timeframe
            timeframe_results = {}
            
            for tf, data in market_data.items():
                if data is None or data.empty:
                    continue
                
                self.logger.info(f"  📊 Simulazione su timeframe {tf}...")
                
                # Simula trading
                tf_result = await self.simulate_trading(strategy, data, tf, config)
                timeframe_results[tf] = tf_result
                
                print(f"    {tf}: {tf_result['total_trades']} trade, "
                      f"P&L: {tf_result['total_pnl']:.2%}, "
                      f"Win Rate: {tf_result['win_rate']:.1%}")
            
            # Calcola metriche aggregate
            aggregate_result = self.calculate_aggregate_metrics(timeframe_results, config)
            
            return {
                'config': config,
                'timeframe_results': timeframe_results,
                'aggregate': aggregate_result
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore simulazione {strategy_name}: {e}")
            return None
    
    async def simulate_trading(self, strategy, data: pd.DataFrame, timeframe: str, config: Dict):
        """Simula trading su dati specifici"""
        
        # Calcola indicatori tecnici
        data = self.add_technical_indicators(data)
        
        # Variabili simulazione
        initial_balance = 10000  # $10,000 iniziali
        balance = initial_balance
        position = None
        trades = []
        
        # Simula ogni candela
        for i in range(50, len(data)):  # Inizia da 50 per avere abbastanza dati per indicatori
            current_data = data.iloc[:i+1]
            current_price = current_data['Close'].iloc[-1]
            
            try:
                # Analizza mercato (versione semplificata)
                market_analysis = {
                    'price': current_price,
                    'rsi': current_data['RSI'].iloc[-1] if 'RSI' in current_data.columns else 50,
                    'sma_20': current_data['SMA_20'].iloc[-1] if 'SMA_20' in current_data.columns else current_price,
                    'sma_50': current_data['SMA_50'].iloc[-1] if 'SMA_50' in current_data.columns else current_price,
                }
                
                # Genera segnali (versione semplificata)
                signals = await self.generate_simple_signals(strategy, market_analysis, config)
                
                # Gestisci posizione esistente
                if position:
                    # Check stop loss
                    if position['type'] == 'long':
                        if current_price <= position['stop_loss']:
                            # Stop loss hit
                            pnl = (current_price - position['entry_price']) / position['entry_price']
                            trades.append({
                                'entry_time': position['entry_time'],
                                'exit_time': current_data.index[-1],
                                'entry_price': position['entry_price'],
                                'exit_price': current_price,
                                'type': 'long',
                                'pnl': pnl,
                                'exit_reason': 'stop_loss'
                            })
                            balance *= (1 + pnl)
                            position = None
                        elif current_price >= position['profit_target']:
                            # Profit target hit
                            pnl = (current_price - position['entry_price']) / position['entry_price']
                            trades.append({
                                'entry_time': position['entry_time'],
                                'exit_time': current_data.index[-1],
                                'entry_price': position['entry_price'],
                                'exit_price': current_price,
                                'type': 'long',
                                'pnl': pnl,
                                'exit_reason': 'profit_target'
                            })
                            balance *= (1 + pnl)
                            position = None
                    
                    elif position['type'] == 'short':
                        if current_price >= position['stop_loss']:
                            # Stop loss hit
                            pnl = (position['entry_price'] - current_price) / position['entry_price']
                            trades.append({
                                'entry_time': position['entry_time'],
                                'exit_time': current_data.index[-1],
                                'entry_price': position['entry_price'],
                                'exit_price': current_price,
                                'type': 'short',
                                'pnl': pnl,
                                'exit_reason': 'stop_loss'
                            })
                            balance *= (1 + pnl)
                            position = None
                        elif current_price <= position['profit_target']:
                            # Profit target hit
                            pnl = (position['entry_price'] - current_price) / position['entry_price']
                            trades.append({
                                'entry_time': position['entry_time'],
                                'exit_time': current_data.index[-1],
                                'entry_price': position['entry_price'],
                                'exit_price': current_price,
                                'type': 'short',
                                'pnl': pnl,
                                'exit_reason': 'profit_target'
                            })
                            balance *= (1 + pnl)
                            position = None
                
                # Apri nuova posizione se nessuna posizione attiva
                if not position and signals:
                    signal = signals[0]
                    if signal['confidence'] >= 0.6:  # Soglia minima confidenza
                        if signal['action'].lower() == 'buy':
                            position = {
                                'type': 'long',
                                'entry_time': current_data.index[-1],
                                'entry_price': current_price,
                                'stop_loss': current_price * (1 - config['stop_loss']),
                                'profit_target': current_price * (1 + config['profit_target'])
                            }
                        elif signal['action'].lower() == 'sell':
                            position = {
                                'type': 'short',
                                'entry_time': current_data.index[-1],
                                'entry_price': current_price,
                                'stop_loss': current_price * (1 + config['stop_loss']),
                                'profit_target': current_price * (1 - config['profit_target'])
                            }
                
            except Exception as e:
                # Ignora errori individuali e continua
                continue
        
        # Calcola metriche
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = len([t for t in trades if t['pnl'] <= 0])
        
        total_pnl = (balance - initial_balance) / initial_balance
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        avg_win = np.mean([t['pnl'] for t in trades if t['pnl'] > 0]) if winning_trades > 0 else 0
        avg_loss = np.mean([t['pnl'] for t in trades if t['pnl'] <= 0]) if losing_trades > 0 else 0
        
        return {
            'timeframe': timeframe,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'final_balance': balance,
            'trades': trades
        }
    
    async def generate_simple_signals(self, strategy, market_analysis: Dict, config: Dict):
        """Genera segnali semplificati per simulazione"""
        try:
            # Logica semplificata basata su RSI e trend
            rsi = market_analysis.get('rsi', 50)
            price = market_analysis.get('price', 0)
            sma_20 = market_analysis.get('sma_20', price)
            sma_50 = market_analysis.get('sma_50', price)
            
            # Determina trend
            trend_bullish = sma_20 > sma_50
            trend_strength = abs(sma_20 - sma_50) / price if price > 0 else 0
            
            signals = []
            
            # Logica swing trading
            if config['type'] == 'swing':
                if (trend_bullish and rsi < 40 and 
                    trend_strength >= config['min_trend_strength']):
                    signals.append({
                        'action': 'buy',
                        'confidence': min(0.9, 0.5 + trend_strength),
                        'price': price,
                        'reason': 'Trend bullish + RSI oversold'
                    })
                elif (not trend_bullish and rsi > 60 and 
                      trend_strength >= config['min_trend_strength']):
                    signals.append({
                        'action': 'sell',
                        'confidence': min(0.9, 0.5 + trend_strength),
                        'price': price,
                        'reason': 'Trend bearish + RSI overbought'
                    })
            
            # Logica scalping
            elif config['type'] == 'scalping':
                if rsi < 30:
                    signals.append({
                        'action': 'buy',
                        'confidence': 0.7,
                        'price': price,
                        'reason': 'RSI oversold scalping'
                    })
                elif rsi > 70:
                    signals.append({
                        'action': 'sell',
                        'confidence': 0.7,
                        'price': price,
                        'reason': 'RSI overbought scalping'
                    })
            
            return signals
            
        except Exception as e:
            return []
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggiunge indicatori tecnici"""
        try:
            # SMA
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            return df
        except Exception as e:
            self.logger.error(f"Errore calcolo indicatori: {e}")
            return df
    
    def calculate_aggregate_metrics(self, timeframe_results: Dict, config: Dict):
        """Calcola metriche aggregate"""
        try:
            all_trades = []
            total_pnl = 0
            total_trades = 0
            
            for tf, result in timeframe_results.items():
                if result:
                    all_trades.extend(result['trades'])
                    total_pnl += result['total_pnl']
                    total_trades += result['total_trades']
            
            if not all_trades:
                return {
                    'total_trades': 0,
                    'win_rate': 0,
                    'avg_pnl': 0,
                    'sharpe_ratio': 0,
                    'max_drawdown': 0,
                    'profit_factor': 0
                }
            
            # Calcola metriche
            winning_trades = [t for t in all_trades if t['pnl'] > 0]
            losing_trades = [t for t in all_trades if t['pnl'] <= 0]
            
            win_rate = len(winning_trades) / len(all_trades)
            avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
            
            # Profit factor
            total_wins = sum([t['pnl'] for t in winning_trades])
            total_losses = abs(sum([t['pnl'] for t in losing_trades]))
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
            
            # Sharpe ratio semplificato
            returns = [t['pnl'] for t in all_trades]
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
            
            # Max drawdown semplificato
            cumulative_returns = np.cumsum(returns)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = cumulative_returns - running_max
            max_drawdown = np.min(drawdown)
            
            return {
                'total_trades': len(all_trades),
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'avg_pnl': np.mean(returns),
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'profit_factor': profit_factor,
                'total_pnl': total_pnl / len(timeframe_results)  # Media tra timeframe
            }
            
        except Exception as e:
            self.logger.error(f"Errore calcolo metriche aggregate: {e}")
            return {}
    
    async def comparative_analysis(self):
        """Analisi comparativa delle strategie"""
        self.print_header("ANALISI COMPARATIVA STRATEGIE")
        
        if not self.results:
            print("❌ Nessun risultato disponibile per l'analisi")
            return
        
        # Crea tabella comparativa
        comparison_data = []
        
        for strategy_name, result in self.results.items():
            if result and 'aggregate' in result:
                agg = result['aggregate']
                comparison_data.append({
                    'Strategia': result['config']['description'],
                    'Tipo': result['config']['type'].title(),
                    'Profit Target': f"{result['config']['profit_target']:.1%}",
                    'Stop Loss': f"{result['config']['stop_loss']:.1%}",
                    'Trade Totali': agg.get('total_trades', 0),
                    'Win Rate': f"{agg.get('win_rate', 0):.1%}",
                    'P&L Medio': f"{agg.get('avg_pnl', 0):.2%}",
                    'Sharpe Ratio': f"{agg.get('sharpe_ratio', 0):.2f}",
                    'Max Drawdown': f"{agg.get('max_drawdown', 0):.2%}",
                    'Profit Factor': f"{agg.get('profit_factor', 0):.2f}"
                })
        
        if comparison_data:
            df_comparison = pd.DataFrame(comparison_data)
            
            print("📊 TABELLA COMPARATIVA STRATEGIE")
            print("=" * 120)
            print(df_comparison.to_string(index=False))
            
            # Ranking
            self.print_section("RANKING STRATEGIE")
            
            # Ordina per Sharpe Ratio
            df_sorted = df_comparison.copy()
            df_sorted['Sharpe_Numeric'] = df_sorted['Sharpe Ratio'].str.replace('inf', '999').astype(float)
            df_sorted = df_sorted.sort_values('Sharpe_Numeric', ascending=False)
            
            print("🏆 TOP 3 STRATEGIE (per Sharpe Ratio):")
            for i, (_, row) in enumerate(df_sorted.head(3).iterrows(), 1):
                print(f"  {i}. {row['Strategia']}")
                print(f"     📊 Sharpe: {row['Sharpe Ratio']} | Win Rate: {row['Win Rate']} | P&L: {row['P&L Medio']}")
    
    async def generate_recommendations(self):
        """Genera raccomandazioni basate sui risultati"""
        self.print_section("RACCOMANDAZIONI STRATEGICHE")
        
        if not self.results:
            print("❌ Nessun risultato per generare raccomandazioni")
            return
        
        recommendations = []
        
        # Analizza risultati
        best_strategy = None
        best_sharpe = -999
        
        for strategy_name, result in self.results.items():
            if result and 'aggregate' in result:
                agg = result['aggregate']
                sharpe = agg.get('sharpe_ratio', 0)
                
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_strategy = (strategy_name, result)
        
        if best_strategy:
            name, result = best_strategy
            config = result['config']
            agg = result['aggregate']
            
            recommendations.append(f"🏆 STRATEGIA RACCOMANDATA: {config['description']}")
            recommendations.append(f"   📊 Sharpe Ratio: {agg.get('sharpe_ratio', 0):.2f}")
            recommendations.append(f"   🎯 Win Rate: {agg.get('win_rate', 0):.1%}")
            recommendations.append(f"   💰 P&L Medio: {agg.get('avg_pnl', 0):.2%}")
            
            # Raccomandazioni specifiche
            if agg.get('win_rate', 0) < 0.5:
                recommendations.append("⚠️ Win rate basso - considerare ottimizzazione parametri")
            
            if agg.get('max_drawdown', 0) < -0.1:
                recommendations.append("⚠️ Drawdown elevato - considerare riduzione risk")
            
            if agg.get('total_trades', 0) < 10:
                recommendations.append("⚠️ Pochi trade - considerare parametri meno restrittivi")
        
        # Raccomandazioni generali
        recommendations.append("")
        recommendations.append("📋 RACCOMANDAZIONI GENERALI:")
        recommendations.append("   1. Testare strategia migliore per 1 settimana in testnet")
        recommendations.append("   2. Monitorare performance real-time")
        recommendations.append("   3. Ottimizzare parametri basandosi sui risultati")
        recommendations.append("   4. Implementare risk management avanzato")
        recommendations.append("   5. Considerare portfolio multi-strategia")
        
        for rec in recommendations:
            print(f"  {rec}")
    
    async def save_results(self):
        """Salva risultati della simulazione"""
        self.print_section("SALVATAGGIO RISULTATI")
        
        try:
            # Crea directory risultati
            results_dir = "/home/ubuntu/AurumBotX/simulation_results"
            os.makedirs(results_dir, exist_ok=True)
            
            # Timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Salva risultati JSON
            json_file = f"{results_dir}/strategy_simulation_{timestamp}.json"
            with open(json_file, 'w') as f:
                # Converti numpy types per JSON serialization
                json_results = {}
                for k, v in self.results.items():
                    if v:
                        json_results[k] = self.convert_numpy_types(v)
                
                json.dump(json_results, f, indent=2, default=str)
            
            print(f"  ✅ Risultati JSON salvati: {json_file}")
            
            # Salva summary
            summary_file = f"{results_dir}/strategy_summary_{timestamp}.txt"
            with open(summary_file, 'w') as f:
                f.write("SIMULAZIONE STRATEGIE AURUMBOTX\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Strategie testate: {len(self.results)}\n\n")
                
                for strategy_name, result in self.results.items():
                    if result:
                        f.write(f"Strategia: {result['config']['description']}\n")
                        f.write(f"Tipo: {result['config']['type']}\n")
                        if 'aggregate' in result:
                            agg = result['aggregate']
                            f.write(f"Trade totali: {agg.get('total_trades', 0)}\n")
                            f.write(f"Win rate: {agg.get('win_rate', 0):.1%}\n")
                            f.write(f"Sharpe ratio: {agg.get('sharpe_ratio', 0):.2f}\n")
                        f.write("\n")
            
            print(f"  ✅ Summary salvato: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Errore salvataggio: {e}")
    
    def convert_numpy_types(self, obj):
        """Converte numpy types per JSON serialization"""
        if isinstance(obj, dict):
            return {k: self.convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_numpy_types(v) for v in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

async def main():
    """Main del simulatore strategie"""
    simulator = ComprehensiveStrategySimulator()
    await simulator.run_comprehensive_simulation()

if __name__ == "__main__":
    asyncio.run(main())

