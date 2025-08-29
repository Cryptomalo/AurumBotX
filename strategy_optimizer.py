#!/usr/bin/env python3
"""
AurumBotX Strategy Optimizer
Sistema di ottimizzazione strategie basato sui risultati di performance
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional, Tuple
import asyncio
from dataclasses import dataclass
import copy

# Aggiungi path del progetto
sys.path.append('/home/ubuntu/AurumBotX')

@dataclass
class OptimizationResult:
    """Risultato di ottimizzazione"""
    strategy_name: str
    original_config: Dict[str, Any]
    optimized_config: Dict[str, Any]
    performance_improvement: float
    confidence_score: float
    recommendations: List[str]

class StrategyOptimizer:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('StrategyOptimizer')
        self.optimization_date = datetime.now()
        
        # Configurazioni strategie disponibili
        self.strategy_configs = {
            'swing_trading': {
                'profit_target': 0.05,      # 5%
                'stop_loss': 0.03,          # 3%
                'trend_period': 20,
                'min_trend_strength': 0.6,
                'confidence_threshold': 0.7,
                'position_size_factor': 0.1
            },
            'scalping': {
                'profit_target': 0.02,      # 2%
                'stop_loss': 0.01,          # 1%
                'trend_period': 5,
                'min_trend_strength': 0.8,
                'confidence_threshold': 0.75,
                'position_size_factor': 0.05
            }
        }
        
        # Parametri di ottimizzazione
        self.optimization_ranges = {
            'profit_target': (0.01, 0.15, 0.01),    # min, max, step
            'stop_loss': (0.005, 0.08, 0.005),
            'trend_period': (5, 50, 5),
            'min_trend_strength': (0.3, 0.9, 0.1),
            'confidence_threshold': (0.6, 0.9, 0.05),
            'position_size_factor': (0.01, 0.2, 0.01)
        }
        
        # Metriche di performance
        self.performance_metrics = {}
        self.optimization_results = {}
        
    def setup_logging(self):
        """Setup logging per ottimizzazione"""
        Path('logs/optimization').mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/optimization/strategy_optimization_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
    
    def print_header(self, title):
        """Header professionale"""
        print(f"\n{'='*80}")
        print(f"🎯 {title}")
        print(f"{'='*80}")
        
    def print_section(self, title):
        """Sezione"""
        print(f"\n📋 {title}")
        print(f"{'-'*70}")
    
    def load_performance_data(self) -> Dict[str, Any]:
        """Carica dati di performance dalle analisi precedenti"""
        try:
            performance_data = {
                'trading_signals': [],
                'system_metrics': [],
                'ai_performance': {},
                'risk_metrics': {}
            }
            
            # Carica da file di analisi recenti
            analysis_files = list(Path('logs/analysis').glob('weekly_analysis_*.json'))
            
            if analysis_files:
                # Prendi il file più recente
                latest_file = max(analysis_files, key=os.path.getctime)
                
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                    performance_data.update(data)
                
                self.logger.info(f"📊 Caricati dati da: {latest_file}")
            
            # Carica anche dai log diretti
            log_files = list(Path('logs').glob('trades_*.log'))
            
            for log_file in log_files:
                try:
                    with open(log_file, 'r') as f:
                        for line in f:
                            if 'SIGNAL|' in line:
                                parts = line.strip().split('|')
                                if len(parts) >= 5:
                                    performance_data['trading_signals'].append({
                                        'pair': parts[1],
                                        'action': parts[2],
                                        'confidence': float(parts[3]),
                                        'price': float(parts[4])
                                    })
                except:
                    continue
            
            return performance_data
            
        except Exception as e:
            self.logger.error(f"Errore caricamento dati: {e}")
            return {}
    
    def calculate_strategy_performance_score(self, config: Dict[str, Any], 
                                           performance_data: Dict[str, Any]) -> float:
        """Calcola score di performance per una configurazione"""
        try:
            score = 0.0
            
            # Analisi segnali trading
            signals = performance_data.get('trading_signals', [])
            if signals:
                # Score basato su confidenza media
                confidences = [s['confidence'] for s in signals]
                avg_confidence = np.mean(confidences)
                score += avg_confidence * 40  # 40% del peso
                
                # Score basato su distribuzione azioni
                actions = [s['action'] for s in signals]
                buy_ratio = actions.count('buy') / len(actions) if actions else 0
                sell_ratio = actions.count('sell') / len(actions) if actions else 0
                balance_score = 1 - abs(buy_ratio - sell_ratio)  # Penalizza squilibri estremi
                score += balance_score * 20  # 20% del peso
            
            # Score basato su parametri di rischio
            profit_target = config.get('profit_target', 0.05)
            stop_loss = config.get('stop_loss', 0.03)
            risk_reward_ratio = profit_target / stop_loss if stop_loss > 0 else 1
            
            # Ottimale intorno a 1.5-2.0
            if 1.5 <= risk_reward_ratio <= 2.5:
                score += 25  # 25% del peso
            elif 1.0 <= risk_reward_ratio <= 3.0:
                score += 15
            else:
                score += 5
            
            # Score basato su confidence threshold
            confidence_threshold = config.get('confidence_threshold', 0.7)
            if 0.65 <= confidence_threshold <= 0.8:
                score += 15  # 15% del peso
            elif 0.6 <= confidence_threshold <= 0.85:
                score += 10
            else:
                score += 5
            
            return min(score, 100)  # Cap a 100
            
        except Exception as e:
            self.logger.error(f"Errore calcolo score: {e}")
            return 0.0
    
    def generate_parameter_variations(self, base_config: Dict[str, Any], 
                                    num_variations: int = 20) -> List[Dict[str, Any]]:
        """Genera variazioni dei parametri per ottimizzazione"""
        try:
            variations = []
            
            for _ in range(num_variations):
                variation = copy.deepcopy(base_config)
                
                # Varia ogni parametro nell'intervallo definito
                for param, (min_val, max_val, step) in self.optimization_ranges.items():
                    if param in variation:
                        # Genera valore casuale nell'intervallo
                        if isinstance(min_val, float):
                            new_value = np.random.uniform(min_val, max_val)
                            # Arrotonda al step più vicino
                            new_value = round(new_value / step) * step
                        else:
                            new_value = np.random.randint(min_val, max_val + 1)
                        
                        variation[param] = new_value
                
                variations.append(variation)
            
            return variations
            
        except Exception as e:
            self.logger.error(f"Errore generazione variazioni: {e}")
            return [base_config]
    
    def optimize_strategy(self, strategy_name: str, 
                         performance_data: Dict[str, Any]) -> OptimizationResult:
        """Ottimizza una strategia specifica"""
        try:
            self.logger.info(f"🔧 Ottimizzazione strategia: {strategy_name}")
            
            base_config = self.strategy_configs.get(strategy_name, {})
            if not base_config:
                raise ValueError(f"Strategia {strategy_name} non trovata")
            
            # Calcola score baseline
            baseline_score = self.calculate_strategy_performance_score(base_config, performance_data)
            self.logger.info(f"📊 Score baseline: {baseline_score:.2f}")
            
            # Genera variazioni
            variations = self.generate_parameter_variations(base_config, num_variations=50)
            
            # Testa ogni variazione
            best_config = base_config
            best_score = baseline_score
            
            for i, variation in enumerate(variations):
                score = self.calculate_strategy_performance_score(variation, performance_data)
                
                if score > best_score:
                    best_score = score
                    best_config = variation
                    self.logger.info(f"🎯 Nuovo miglior score: {score:.2f} (variazione {i+1})")
            
            # Calcola miglioramento
            improvement = ((best_score - baseline_score) / baseline_score * 100) if baseline_score > 0 else 0
            
            # Genera raccomandazioni
            recommendations = self.generate_optimization_recommendations(
                strategy_name, base_config, best_config, improvement
            )
            
            # Calcola confidence score
            confidence_score = min(best_score / 100, 1.0) * 100
            
            result = OptimizationResult(
                strategy_name=strategy_name,
                original_config=base_config,
                optimized_config=best_config,
                performance_improvement=improvement,
                confidence_score=confidence_score,
                recommendations=recommendations
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Errore ottimizzazione {strategy_name}: {e}")
            return OptimizationResult(
                strategy_name=strategy_name,
                original_config=base_config,
                optimized_config=base_config,
                performance_improvement=0,
                confidence_score=0,
                recommendations=[f"❌ Errore ottimizzazione: {str(e)}"]
            )
    
    def generate_optimization_recommendations(self, strategy_name: str,
                                            original_config: Dict[str, Any],
                                            optimized_config: Dict[str, Any],
                                            improvement: float) -> List[str]:
        """Genera raccomandazioni basate sull'ottimizzazione"""
        recommendations = []
        
        try:
            # Analizza cambiamenti significativi
            for param, new_value in optimized_config.items():
                if param in original_config:
                    old_value = original_config[param]
                    change_percent = ((new_value - old_value) / old_value * 100) if old_value != 0 else 0
                    
                    if abs(change_percent) > 10:  # Cambiamento significativo
                        direction = "aumentare" if change_percent > 0 else "diminuire"
                        recommendations.append(
                            f"📊 {param}: {direction} da {old_value} a {new_value:.3f} "
                            f"({change_percent:+.1f}%)"
                        )
            
            # Raccomandazioni basate su miglioramento
            if improvement > 10:
                recommendations.append("✅ Miglioramento significativo - Implementare subito")
            elif improvement > 5:
                recommendations.append("🎯 Miglioramento moderato - Test in ambiente controllato")
            elif improvement > 0:
                recommendations.append("📈 Miglioramento marginale - Monitorare attentamente")
            else:
                recommendations.append("⚠️ Nessun miglioramento - Mantenere configurazione attuale")
            
            # Raccomandazioni specifiche per strategia
            if strategy_name == 'swing_trading':
                profit_target = optimized_config.get('profit_target', 0)
                stop_loss = optimized_config.get('stop_loss', 0)
                
                if profit_target > 0.1:
                    recommendations.append("⚠️ Profit target alto - Verificare in mercati volatili")
                
                if stop_loss < 0.02:
                    recommendations.append("🚨 Stop loss basso - Rischio di stop frequenti")
                    
            elif strategy_name == 'scalping':
                trend_period = optimized_config.get('trend_period', 0)
                
                if trend_period > 10:
                    recommendations.append("📊 Periodo trend lungo per scalping - Verificare efficacia")
            
            # Raccomandazioni generali
            confidence_threshold = optimized_config.get('confidence_threshold', 0)
            if confidence_threshold > 0.8:
                recommendations.append("🎯 Soglia confidenza alta - Meno segnali ma più accurati")
            elif confidence_threshold < 0.65:
                recommendations.append("⚠️ Soglia confidenza bassa - Più segnali ma meno accurati")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Errore generazione raccomandazioni: {e}")
            return ["❌ Errore generazione raccomandazioni"]
    
    def apply_optimization_to_system(self, optimization_result: OptimizationResult) -> bool:
        """Applica ottimizzazione al sistema"""
        try:
            strategy_name = optimization_result.strategy_name
            optimized_config = optimization_result.optimized_config
            
            # Aggiorna configurazione in memoria
            self.strategy_configs[strategy_name] = optimized_config
            
            # Salva configurazione ottimizzata
            config_file = f'logs/optimization/optimized_{strategy_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            
            optimization_data = {
                'strategy_name': strategy_name,
                'optimization_date': datetime.now().isoformat(),
                'original_config': optimization_result.original_config,
                'optimized_config': optimized_config,
                'performance_improvement': optimization_result.performance_improvement,
                'confidence_score': optimization_result.confidence_score,
                'recommendations': optimization_result.recommendations
            }
            
            with open(config_file, 'w') as f:
                json.dump(optimization_data, f, indent=2)
            
            self.logger.info(f"💾 Configurazione salvata: {config_file}")
            
            # Aggiorna file di configurazione principale se esiste
            main_config_file = f'utils/strategies/{strategy_name}_config.json'
            if Path(main_config_file).parent.exists():
                with open(main_config_file, 'w') as f:
                    json.dump(optimized_config, f, indent=2)
                self.logger.info(f"🔄 Aggiornata configurazione principale: {main_config_file}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Errore applicazione ottimizzazione: {e}")
            return False
    
    def create_optimization_report(self, results: List[OptimizationResult]) -> str:
        """Crea report di ottimizzazione"""
        try:
            report_file = f'logs/optimization/optimization_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
            
            with open(report_file, 'w') as f:
                f.write("# AurumBotX Strategy Optimization Report\\n\\n")
                f.write(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
                
                for result in results:
                    f.write(f"## Strategia: {result.strategy_name}\\n\\n")
                    f.write(f"**Miglioramento Performance:** {result.performance_improvement:.2f}%\\n")
                    f.write(f"**Confidence Score:** {result.confidence_score:.1f}%\\n\\n")
                    
                    f.write("### Configurazione Originale\\n")
                    for param, value in result.original_config.items():
                        f.write(f"- {param}: {value}\\n")
                    
                    f.write("\\n### Configurazione Ottimizzata\\n")
                    for param, value in result.optimized_config.items():
                        f.write(f"- {param}: {value}\\n")
                    
                    f.write("\\n### Raccomandazioni\\n")
                    for rec in result.recommendations:
                        f.write(f"- {rec}\\n")
                    
                    f.write("\\n---\\n\\n")
            
            return report_file
            
        except Exception as e:
            self.logger.error(f"Errore creazione report: {e}")
            return ""
    
    def print_optimization_results(self, results: List[OptimizationResult]):
        """Stampa risultati ottimizzazione"""
        self.print_header("RISULTATI OTTIMIZZAZIONE STRATEGIE")
        
        for result in results:
            self.print_section(f"STRATEGIA: {result.strategy_name.upper()}")
            
            print(f"  📈 Miglioramento: {result.performance_improvement:+.2f}%")
            print(f"  🎯 Confidence: {result.confidence_score:.1f}%")
            
            print(f"\\n  📊 CONFIGURAZIONE ORIGINALE:")
            for param, value in result.original_config.items():
                print(f"    {param}: {value}")
            
            print(f"\\n  🎯 CONFIGURAZIONE OTTIMIZZATA:")
            for param, value in result.optimized_config.items():
                old_value = result.original_config.get(param, value)
                change = "📈" if value > old_value else "📉" if value < old_value else "➡️"
                print(f"    {param}: {value} {change}")
            
            print(f"\\n  💡 RACCOMANDAZIONI:")
            for i, rec in enumerate(result.recommendations, 1):
                print(f"    {i}. {rec}")
    
    async def run_strategy_optimization(self):
        """Esegue ottimizzazione completa delle strategie"""
        self.print_header("AVVIO OTTIMIZZAZIONE STRATEGIE")
        
        try:
            # 1. Carica dati di performance
            self.logger.info("📊 Caricamento dati di performance...")
            performance_data = self.load_performance_data()
            
            if not performance_data:
                self.logger.warning("⚠️ Nessun dato di performance trovato")
                return
            
            # 2. Ottimizza ogni strategia
            optimization_results = []
            
            for strategy_name in self.strategy_configs.keys():
                self.logger.info(f"🔧 Ottimizzazione {strategy_name}...")
                result = self.optimize_strategy(strategy_name, performance_data)
                optimization_results.append(result)
                
                # Applica ottimizzazione se miglioramento significativo
                if result.performance_improvement > 5:
                    self.logger.info(f"✅ Applicazione ottimizzazione {strategy_name}...")
                    self.apply_optimization_to_system(result)
            
            # 3. Genera report
            self.logger.info("📄 Generazione report...")
            report_file = self.create_optimization_report(optimization_results)
            
            # 4. Stampa risultati
            self.print_optimization_results(optimization_results)
            
            # 5. Summary
            self.print_section("SUMMARY OTTIMIZZAZIONE")
            total_strategies = len(optimization_results)
            improved_strategies = len([r for r in optimization_results if r.performance_improvement > 0])
            significant_improvements = len([r for r in optimization_results if r.performance_improvement > 5])
            
            print(f"  📊 Strategie analizzate: {total_strategies}")
            print(f"  📈 Strategie migliorate: {improved_strategies}")
            print(f"  🎯 Miglioramenti significativi: {significant_improvements}")
            
            if report_file:
                print(f"  📄 Report salvato: {report_file}")
            
            avg_improvement = np.mean([r.performance_improvement for r in optimization_results])
            print(f"  📊 Miglioramento medio: {avg_improvement:+.2f}%")
            
            self.logger.info("✅ Ottimizzazione strategie completata")
            
        except Exception as e:
            self.logger.error(f"❌ Errore durante ottimizzazione: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Main dell'ottimizzazione strategie"""
    optimizer = StrategyOptimizer()
    await optimizer.run_strategy_optimization()

if __name__ == "__main__":
    asyncio.run(main())

