#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX Multi-Pair Scaler
Sistema di scaling per multiple coppie di trading con gestione avanzata del rischio
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
import random

# Aggiungi path del progetto
sys.path.append('/home/ubuntu/AurumBotX')

@dataclass
class TradingPair:
    """Configurazione coppia di trading"""
    symbol: str
    base_asset: str
    quote_asset: str
    min_notional: float
    tick_size: float
    step_size: float
    is_active: bool
    risk_weight: float
    max_position_size: float

@dataclass
class PairPerformance:
    """Performance di una coppia"""
    symbol: str
    total_signals: int
    avg_confidence: float
    execution_rate: float
    profit_loss: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    last_signal_time: datetime

class MultiPairScaler:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('MultiPairScaler')
        self.scaling_date = datetime.now()
        
        # Configurazione coppie supportate
        self.supported_pairs = {
            'BTCUSDT': TradingPair('BTCUSDT', 'BTC', 'USDT', 10.0, 0.01, 0.00001, True, 1.0, 0.3),
            'ETHUSDT': TradingPair('ETHUSDT', 'ETH', 'USDT', 10.0, 0.01, 0.0001, True, 0.8, 0.25),
            'ADAUSDT': TradingPair('ADAUSDT', 'ADA', 'USDT', 10.0, 0.0001, 0.1, True, 0.6, 0.2),
            'DOTUSDT': TradingPair('DOTUSDT', 'DOT', 'USDT', 10.0, 0.001, 0.01, True, 0.7, 0.2),
            'LINKUSDT': TradingPair('LINKUSDT', 'LINK', 'USDT', 10.0, 0.001, 0.01, True, 0.7, 0.2),
            'BNBUSDT': TradingPair('BNBUSDT', 'BNB', 'USDT', 10.0, 0.01, 0.001, True, 0.8, 0.25),
            'SOLUSDT': TradingPair('SOLUSDT', 'SOL', 'USDT', 10.0, 0.01, 0.001, True, 0.7, 0.2),
            'MATICUSDT': TradingPair('MATICUSDT', 'MATIC', 'USDT', 10.0, 0.0001, 0.1, True, 0.6, 0.15),
            'AVAXUSDT': TradingPair('AVAXUSDT', 'AVAX', 'USDT', 10.0, 0.01, 0.001, True, 0.7, 0.2),
            'ATOMUSDT': TradingPair('ATOMUSDT', 'ATOM', 'USDT', 10.0, 0.001, 0.01, True, 0.6, 0.15)
        }
        
        # Configurazione scaling
        self.scaling_config = {
            'max_concurrent_pairs': 5,
            'min_confidence_threshold': 0.65,
            'max_total_exposure': 0.8,  # 80% del capitale
            'correlation_threshold': 0.7,  # Evita coppie troppo correlate
            'min_volume_24h': 1000000,  # Volume minimo 24h
            'rebalance_interval_hours': 6,
            'performance_lookback_days': 7
        }
        
        # Metriche di performance per coppia
        self.pair_performances = {}
        self.correlation_matrix = {}
        self.risk_metrics = {}
        
    def setup_logging(self):
        """Setup logging per scaling"""
        Path('logs/scaling').mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/scaling/multi_pair_scaling_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
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
    
    async def analyze_pair_performance(self, symbol: str) -> PairPerformance:
        """Analizza performance di una coppia specifica"""
        try:
            # Simula analisi performance (in produzione userebbe dati reali)
            
            # Genera metriche simulate basate su caratteristiche della coppia
            pair_config = self.supported_pairs.get(symbol)
            if not pair_config:
                raise ValueError(f"Coppia {symbol} non supportata")
            
            # Metriche simulate basate su risk_weight
            base_performance = pair_config.risk_weight
            
            # Simula variabilità
            np.random.seed(hash(symbol) % 2**32)  # Seed deterministico per coppia
            
            total_signals = int(np.random.normal(20, 5) * base_performance)
            total_signals = max(1, total_signals)
            
            avg_confidence = np.random.normal(0.7, 0.05) * base_performance
            avg_confidence = np.clip(avg_confidence, 0.5, 0.9)
            
            execution_rate = np.random.normal(0.8, 0.1) * base_performance
            execution_rate = np.clip(execution_rate, 0.3, 1.0)
            
            profit_loss = np.random.normal(0.02, 0.01) * base_performance
            sharpe_ratio = np.random.normal(1.5, 0.3) * base_performance
            max_drawdown = np.random.normal(0.05, 0.02) / base_performance
            volatility = np.random.normal(0.3, 0.1) / base_performance
            
            last_signal_time = datetime.now() - timedelta(hours=np.random.randint(1, 24))
            
            performance = PairPerformance(
                symbol=symbol,
                total_signals=total_signals,
                avg_confidence=avg_confidence,
                execution_rate=execution_rate,
                profit_loss=profit_loss,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                volatility=volatility,
                last_signal_time=last_signal_time
            )
            
            return performance
            
        except Exception as e:
            self.logger.error(f"Errore analisi performance {symbol}: {e}")
            return PairPerformance(
                symbol=symbol, total_signals=0, avg_confidence=0, execution_rate=0,
                profit_loss=0, sharpe_ratio=0, max_drawdown=1, volatility=1,
                last_signal_time=datetime.now()
            )
    
    def calculate_correlation_matrix(self) -> Dict[str, Dict[str, float]]:
        """Calcola matrice di correlazione tra coppie"""
        try:
            symbols = list(self.supported_pairs.keys())
            correlation_matrix = {}
            
            for symbol1 in symbols:
                correlation_matrix[symbol1] = {}
                for symbol2 in symbols:
                    if symbol1 == symbol2:
                        correlation_matrix[symbol1][symbol2] = 1.0
                    else:
                        # Simula correlazione basata su asset base
                        pair1 = self.supported_pairs[symbol1]
                        pair2 = self.supported_pairs[symbol2]
                        
                        # Correlazione alta se stesso asset base
                        if pair1.base_asset == pair2.base_asset:
                            correlation = 0.9
                        # Correlazione media per crypto simili
                        elif pair1.base_asset in ['BTC', 'ETH'] and pair2.base_asset in ['BTC', 'ETH']:
                            correlation = 0.7
                        # Correlazione bassa per asset diversi
                        else:
                            correlation = np.random.uniform(0.2, 0.5)
                        
                        correlation_matrix[symbol1][symbol2] = correlation
            
            return correlation_matrix
            
        except Exception as e:
            self.logger.error(f"Errore calcolo correlazioni: {e}")
            return {}
    
    def calculate_pair_score(self, performance: PairPerformance) -> float:
        """Calcola score complessivo per una coppia"""
        try:
            # Componenti del score (0-100)
            confidence_score = performance.avg_confidence * 100
            execution_score = performance.execution_rate * 100
            profit_score = max(0, performance.profit_loss * 1000)  # Scala per %
            sharpe_score = min(100, performance.sharpe_ratio * 30)
            drawdown_score = max(0, 100 - performance.max_drawdown * 1000)
            volatility_score = max(0, 100 - performance.volatility * 100)
            
            # Peso per ogni componente
            weights = {
                'confidence': 0.25,
                'execution': 0.20,
                'profit': 0.20,
                'sharpe': 0.15,
                'drawdown': 0.10,
                'volatility': 0.10
            }
            
            total_score = (
                confidence_score * weights['confidence'] +
                execution_score * weights['execution'] +
                profit_score * weights['profit'] +
                sharpe_score * weights['sharpe'] +
                drawdown_score * weights['drawdown'] +
                volatility_score * weights['volatility']
            )
            
            return min(100, max(0, total_score))
            
        except Exception as e:
            self.logger.error(f"Errore calcolo score {performance.symbol}: {e}")
            return 0.0
    
    def select_optimal_pairs(self) -> List[str]:
        """Seleziona coppie ottimali per trading"""
        try:
            # Calcola score per ogni coppia
            pair_scores = {}
            for symbol, performance in self.pair_performances.items():
                score = self.calculate_pair_score(performance)
                pair_scores[symbol] = score
            
            # Ordina per score
            sorted_pairs = sorted(pair_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Selezione con controllo correlazione
            selected_pairs = []
            max_pairs = self.scaling_config['max_concurrent_pairs']
            correlation_threshold = self.scaling_config['correlation_threshold']
            
            for symbol, score in sorted_pairs:
                if len(selected_pairs) >= max_pairs:
                    break
                
                # Controlla correlazione con coppie già selezionate
                can_add = True
                for selected_symbol in selected_pairs:
                    correlation = self.correlation_matrix.get(symbol, {}).get(selected_symbol, 0)
                    if correlation > correlation_threshold:
                        can_add = False
                        self.logger.info(f"⚠️ {symbol} escluso per alta correlazione con {selected_symbol} ({correlation:.2f})")
                        break
                
                if can_add:
                    selected_pairs.append(symbol)
                    self.logger.info(f"✅ {symbol} selezionato (score: {score:.1f})")
            
            return selected_pairs
            
        except Exception as e:
            self.logger.error(f"Errore selezione coppie: {e}")
            return ['BTCUSDT']  # Fallback
    
    def calculate_position_sizes(self, selected_pairs: List[str]) -> Dict[str, float]:
        """Calcola dimensioni posizioni per coppie selezionate"""
        try:
            position_sizes = {}
            total_exposure = self.scaling_config['max_total_exposure']
            
            # Calcola peso per ogni coppia basato su performance
            total_weight = 0
            pair_weights = {}
            
            for symbol in selected_pairs:
                performance = self.pair_performances[symbol]
                pair_config = self.supported_pairs[symbol]
                
                # Peso basato su score e risk_weight
                score = self.calculate_pair_score(performance)
                weight = score * pair_config.risk_weight
                pair_weights[symbol] = weight
                total_weight += weight
            
            # Normalizza e calcola position size
            for symbol in selected_pairs:
                if total_weight > 0:
                    normalized_weight = pair_weights[symbol] / total_weight
                    position_size = total_exposure * normalized_weight
                    
                    # Applica limiti massimi
                    max_size = self.supported_pairs[symbol].max_position_size
                    position_size = min(position_size, max_size)
                    
                    position_sizes[symbol] = position_size
                else:
                    position_sizes[symbol] = total_exposure / len(selected_pairs)
            
            return position_sizes
            
        except Exception as e:
            self.logger.error(f"Errore calcolo position sizes: {e}")
            return {symbol: 0.1 for symbol in selected_pairs}
    
    def generate_scaling_config(self, selected_pairs: List[str], 
                              position_sizes: Dict[str, float]) -> Dict[str, Any]:
        """Genera configurazione di scaling"""
        try:
            scaling_config = {
                'scaling_date': datetime.now().isoformat(),
                'selected_pairs': selected_pairs,
                'position_sizes': position_sizes,
                'total_exposure': sum(position_sizes.values()),
                'risk_metrics': {
                    'max_correlation': max([
                        max([self.correlation_matrix.get(p1, {}).get(p2, 0) 
                             for p2 in selected_pairs if p2 != p1])
                        for p1 in selected_pairs
                    ]) if len(selected_pairs) > 1 else 0,
                    'avg_confidence': np.mean([
                        self.pair_performances[symbol].avg_confidence 
                        for symbol in selected_pairs
                    ]),
                    'total_pairs': len(selected_pairs)
                },
                'pair_details': {}
            }
            
            # Dettagli per ogni coppia
            for symbol in selected_pairs:
                performance = self.pair_performances[symbol]
                pair_config = self.supported_pairs[symbol]
                
                scaling_config['pair_details'][symbol] = {
                    'position_size': position_sizes[symbol],
                    'risk_weight': pair_config.risk_weight,
                    'performance_score': self.calculate_pair_score(performance),
                    'avg_confidence': performance.avg_confidence,
                    'execution_rate': performance.execution_rate,
                    'sharpe_ratio': performance.sharpe_ratio,
                    'max_drawdown': performance.max_drawdown
                }
            
            return scaling_config
            
        except Exception as e:
            self.logger.error(f"Errore generazione config: {e}")
            return {}
    
    def create_deployment_files(self, scaling_config: Dict[str, Any]) -> List[str]:
        """Crea file di deployment per scaling"""
        try:
            files_created = []
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 1. File configurazione principale
            config_file = f'logs/scaling/multi_pair_config_{timestamp}.json'
            with open(config_file, 'w') as f:
                json.dump(scaling_config, f, indent=2)
            files_created.append(config_file)
            
            # 2. Script di avvio per ogni coppia
            for symbol in scaling_config['selected_pairs']:
                script_content = f"""#!/bin/bash
# AurumBotX Multi-Pair Trading Script - {symbol}
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

export TRADING_PAIR="{symbol}"
export POSITION_SIZE="{scaling_config['position_sizes'][symbol]}"
export RISK_WEIGHT="{self.supported_pairs[symbol].risk_weight}"

echo "🚀 Avvio trading {symbol}"
echo "💰 Position Size: $POSITION_SIZE"
echo "⚖️ Risk Weight: $RISK_WEIGHT"

# Avvia monitor specifico per coppia
python monitor_24_7.py --pair {symbol} --position-size $POSITION_SIZE &

echo "✅ {symbol} avviato (PID: $!)"
echo $! > logs/scaling/{symbol.lower()}_monitor.pid
"""
                
                script_file = f'logs/scaling/start_{symbol.lower()}_{timestamp}.sh'
                with open(script_file, 'w') as f:
                    f.write(script_content)
                
                # Rendi eseguibile
                os.chmod(script_file, 0o755)
                files_created.append(script_file)
            
            # 3. Script di controllo generale
            control_script = f"""#!/bin/bash
# AurumBotX Multi-Pair Control Script
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PAIRS=({' '.join(scaling_config['selected_pairs'])})

case "$1" in
    start)
        echo "🚀 Avvio trading multi-pair..."
        for pair in "${{PAIRS[@]}}"; do
            ./logs/scaling/start_${{pair,,}}_{timestamp}.sh
            sleep 2
        done
        echo "✅ Tutti i pair avviati"
        ;;
    stop)
        echo "🛑 Arresto trading multi-pair..."
        for pair in "${{PAIRS[@]}}"; do
            if [ -f "logs/scaling/${{pair,,}}_monitor.pid" ]; then
                pid=$(cat "logs/scaling/${{pair,,}}_monitor.pid")
                kill $pid 2>/dev/null && echo "✅ $pair arrestato"
                rm -f "logs/scaling/${{pair,,}}_monitor.pid"
            fi
        done
        ;;
    status)
        echo "📊 Status trading multi-pair:"
        for pair in "${{PAIRS[@]}}"; do
            if [ -f "logs/scaling/${{pair,,}}_monitor.pid" ]; then
                pid=$(cat "logs/scaling/${{pair,,}}_monitor.pid")
                if ps -p $pid > /dev/null; then
                    echo "  ✅ $pair: Running (PID: $pid)"
                else
                    echo "  ❌ $pair: Stopped"
                fi
            else
                echo "  ⚪ $pair: Not started"
            fi
        done
        ;;
    *)
        echo "Usage: $0 {{start|stop|status}}"
        exit 1
        ;;
esac
"""
            
            control_file = f'logs/scaling/multi_pair_control_{timestamp}.sh'
            with open(control_file, 'w') as f:
                f.write(control_script)
            
            os.chmod(control_file, 0o755)
            files_created.append(control_file)
            
            return files_created
            
        except Exception as e:
            self.logger.error(f"Errore creazione file deployment: {e}")
            return []
    
    def print_scaling_report(self, scaling_config: Dict[str, Any]):
        """Stampa report di scaling"""
        self.print_header("MULTI-PAIR SCALING REPORT")
        
        print(f"📅 Data scaling: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Coppie selezionate: {len(scaling_config['selected_pairs'])}")
        print(f"💰 Esposizione totale: {scaling_config['total_exposure']:.1%}")
        
        # Metriche di rischio
        self.print_section("METRICHE DI RISCHIO")
        risk_metrics = scaling_config['risk_metrics']
        print(f"  📊 Correlazione massima: {risk_metrics['max_correlation']:.2f}")
        print(f"  🎯 Confidenza media: {risk_metrics['avg_confidence']:.1%}")
        print(f"  📈 Numero coppie: {risk_metrics['total_pairs']}")
        
        # Dettagli coppie
        self.print_section("COPPIE SELEZIONATE")
        for symbol in scaling_config['selected_pairs']:
            details = scaling_config['pair_details'][symbol]
            print(f"  💹 {symbol}:")
            print(f"    💰 Position Size: {details['position_size']:.1%}")
            print(f"    📊 Performance Score: {details['performance_score']:.1f}")
            print(f"    🎯 Confidenza: {details['avg_confidence']:.1%}")
            print(f"    📈 Sharpe Ratio: {details['sharpe_ratio']:.2f}")
            print(f"    📉 Max Drawdown: {details['max_drawdown']:.1%}")
        
        # Raccomandazioni
        self.print_section("RACCOMANDAZIONI")
        total_exposure = scaling_config['total_exposure']
        max_correlation = risk_metrics['max_correlation']
        avg_confidence = risk_metrics['avg_confidence']
        
        if total_exposure > 0.7:
            print("  ⚠️ Esposizione alta - Monitorare attentamente il rischio")
        elif total_exposure < 0.3:
            print("  💡 Esposizione conservativa - Possibile aumento graduale")
        else:
            print("  ✅ Esposizione bilanciata - Configurazione ottimale")
        
        if max_correlation > 0.8:
            print("  🚨 Correlazione alta tra coppie - Rischio concentrato")
        elif max_correlation < 0.5:
            print("  ✅ Bassa correlazione - Diversificazione eccellente")
        else:
            print("  📊 Correlazione moderata - Diversificazione buona")
        
        if avg_confidence > 0.75:
            print("  🎯 Alta confidenza media - Sistema molto affidabile")
        elif avg_confidence > 0.65:
            print("  📊 Confidenza buona - Sistema affidabile")
        else:
            print("  ⚠️ Confidenza bassa - Necessario miglioramento modelli")
    
    async def run_multi_pair_scaling(self):
        """Esegue scaling completo per multiple coppie"""
        self.print_header("AVVIO MULTI-PAIR SCALING")
        
        try:
            # 1. Analizza performance di tutte le coppie
            self.logger.info("📊 Analisi performance coppie...")
            for symbol in self.supported_pairs.keys():
                self.logger.info(f"  📈 Analizzando {symbol}...")
                performance = await self.analyze_pair_performance(symbol)
                self.pair_performances[symbol] = performance
            
            # 2. Calcola matrice correlazioni
            self.logger.info("🔗 Calcolo correlazioni...")
            self.correlation_matrix = self.calculate_correlation_matrix()
            
            # 3. Seleziona coppie ottimali
            self.logger.info("🎯 Selezione coppie ottimali...")
            selected_pairs = self.select_optimal_pairs()
            
            # 4. Calcola position sizes
            self.logger.info("💰 Calcolo position sizes...")
            position_sizes = self.calculate_position_sizes(selected_pairs)
            
            # 5. Genera configurazione
            self.logger.info("⚙️ Generazione configurazione...")
            scaling_config = self.generate_scaling_config(selected_pairs, position_sizes)
            
            # 6. Crea file di deployment
            self.logger.info("📄 Creazione file deployment...")
            deployment_files = self.create_deployment_files(scaling_config)
            
            # 7. Report finale
            self.print_scaling_report(scaling_config)
            
            # 8. File generati
            self.print_section("FILE GENERATI")
            for file_path in deployment_files:
                print(f"  📄 {file_path}")
            
            self.logger.info("✅ Multi-pair scaling completato con successo")
            
            return scaling_config, deployment_files
            
        except Exception as e:
            self.logger.error(f"❌ Errore durante scaling: {e}")
            import traceback
            traceback.print_exc()
            return {}, []

async def main():
    """Main del multi-pair scaling"""
    scaler = MultiPairScaler()
    await scaler.run_multi_pair_scaling()

if __name__ == "__main__":
    asyncio.run(main())
