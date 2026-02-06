#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX Weekly Performance Analyzer
Sistema di analisi performance settimanale con metriche avanzate e reporting
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class WeeklyPerformanceAnalyzer:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('WeeklyPerformanceAnalyzer')
        self.analysis_date = datetime.now()
        
        # Metriche di performance
        self.performance_metrics = {
            'trading_performance': {},
            'system_performance': {},
            'ai_model_performance': {},
            'strategy_performance': {},
            'risk_metrics': {},
            'profitability_analysis': {},
            'recommendations': []
        }
        
        # Configurazione analisi
        self.config = {
            'analysis_period_days': 7,
            'benchmark_metrics': {
                'min_uptime_percent': 95,
                'min_signal_accuracy': 65,
                'max_avg_cycle_time': 5,
                'max_error_rate': 5,
                'min_profit_target': 2
            },
            'chart_style': 'seaborn-v0_8',
            'export_formats': ['json', 'csv', 'png']
        }
        
    def setup_logging(self):
        """Setup logging per analisi performance"""
        Path('logs/analysis').mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/analysis/weekly_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
    
    def print_header(self, title):
        """Header professionale"""
        print(f"\n{'='*80}")
        print(f"📊 {title}")
        print(f"{'='*80}")
        
    def print_section(self, title):
        """Sezione"""
        print(f"\n📋 {title}")
        print(f"{'-'*70}")
    
    def collect_log_data(self) -> Dict[str, List]:
        """Raccolta dati dai log"""
        try:
            log_data = {
                'trading_signals': [],
                'trade_executions': [],
                'system_metrics': [],
                'error_logs': [],
                'performance_logs': []
            }
            
            # Periodo di analisi
            end_date = self.analysis_date
            start_date = end_date - timedelta(days=self.config['analysis_period_days'])
            
            # Raccolta da file di log
            log_files = list(Path('logs').glob('*.log'))
            
            for log_file in log_files:
                try:
                    # Filtra per data se possibile
                    file_date = datetime.fromtimestamp(os.path.getctime(log_file))
                    if file_date < start_date:
                        continue
                    
                    with open(log_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            
                            # Parsing segnali trading
                            if 'SIGNAL|' in line:
                                try:
                                    parts = line.split('|')
                                    if len(parts) >= 5:
                                        log_data['trading_signals'].append({
                                            'timestamp': self.extract_timestamp(line),
                                            'pair': parts[1],
                                            'action': parts[2],
                                            'confidence': float(parts[3]),
                                            'price': float(parts[4])
                                        })
                                except:
                                    continue
                            
                            # Parsing esecuzioni
                            elif 'EXECUTED|' in line:
                                try:
                                    parts = line.split('|')
                                    if len(parts) >= 6:
                                        log_data['trade_executions'].append({
                                            'timestamp': self.extract_timestamp(line),
                                            'pair': parts[1],
                                            'action': parts[2],
                                            'quantity': float(parts[3]),
                                            'price': float(parts[4]),
                                            'order_id': parts[5]
                                        })
                                except:
                                    continue
                            
                            # Parsing errori
                            elif 'ERROR' in line:
                                log_data['error_logs'].append({
                                    'timestamp': self.extract_timestamp(line),
                                    'message': line
                                })
                            
                            # Parsing metriche performance
                            elif 'Ciclo completato' in line:
                                try:
                                    # Estrai tempo ciclo
                                    if 'in ' in line and 's' in line:
                                        time_part = line.split('in ')[1].split('s')[0]
                                        cycle_time = float(time_part)
                                        log_data['performance_logs'].append({
                                            'timestamp': self.extract_timestamp(line),
                                            'cycle_time': cycle_time
                                        })
                                except:
                                    continue
                                    
                except Exception as e:
                    self.logger.warning(f"Errore lettura {log_file}: {e}")
                    continue
            
            return log_data
            
        except Exception as e:
            self.logger.error(f"Errore raccolta dati log: {e}")
            return {}
    
    def extract_timestamp(self, log_line: str) -> Optional[str]:
        """Estrae timestamp da riga di log"""
        try:
            # Formato: 2025-08-13 08:17:34,552
            if log_line.startswith('20'):
                return log_line.split(' - ')[0].replace(',', '.')
            return None
        except:
            return None
    
    def analyze_trading_performance(self, log_data: Dict) -> Dict:
        """Analisi performance trading"""
        try:
            signals = log_data.get('trading_signals', [])
            executions = log_data.get('trade_executions', [])
            
            if not signals:
                return {'error': 'Nessun segnale trovato'}
            
            # Converti in DataFrame
            signals_df = pd.DataFrame(signals)
            executions_df = pd.DataFrame(executions) if executions else pd.DataFrame()
            
            # Metriche base
            total_signals = len(signals_df)
            total_executions = len(executions_df)
            execution_rate = (total_executions / total_signals * 100) if total_signals > 0 else 0
            
            # Analisi per azione
            buy_signals = signals_df[signals_df['action'] == 'buy']
            sell_signals = signals_df[signals_df['action'] == 'sell']
            
            # Analisi confidenza
            avg_confidence = signals_df['confidence'].mean() * 100
            high_confidence_signals = len(signals_df[signals_df['confidence'] >= 0.7])
            high_confidence_rate = (high_confidence_signals / total_signals * 100) if total_signals > 0 else 0
            
            # Analisi temporale
            if 'timestamp' in signals_df.columns:
                signals_df['timestamp'] = pd.to_datetime(signals_df['timestamp'])
                signals_per_day = signals_df.groupby(signals_df['timestamp'].dt.date).size()
                avg_signals_per_day = signals_per_day.mean()
            else:
                avg_signals_per_day = 0
            
            # Analisi prezzi
            price_analysis = {
                'min_price': signals_df['price'].min(),
                'max_price': signals_df['price'].max(),
                'avg_price': signals_df['price'].mean(),
                'price_volatility': signals_df['price'].std()
            }
            
            return {
                'total_signals': total_signals,
                'total_executions': total_executions,
                'execution_rate': execution_rate,
                'buy_signals': len(buy_signals),
                'sell_signals': len(sell_signals),
                'avg_confidence': avg_confidence,
                'high_confidence_signals': high_confidence_signals,
                'high_confidence_rate': high_confidence_rate,
                'avg_signals_per_day': avg_signals_per_day,
                'price_analysis': price_analysis,
                'signals_by_day': signals_per_day.to_dict() if 'timestamp' in signals_df.columns else {}
            }
            
        except Exception as e:
            self.logger.error(f"Errore analisi trading: {e}")
            return {'error': str(e)}
    
    def analyze_system_performance(self, log_data: Dict) -> Dict:
        """Analisi performance sistema"""
        try:
            performance_logs = log_data.get('performance_logs', [])
            error_logs = log_data.get('error_logs', [])
            
            if not performance_logs:
                return {'error': 'Nessun dato performance trovato'}
            
            # Converti in DataFrame
            perf_df = pd.DataFrame(performance_logs)
            
            # Metriche cicli
            total_cycles = len(perf_df)
            avg_cycle_time = perf_df['cycle_time'].mean()
            max_cycle_time = perf_df['cycle_time'].max()
            min_cycle_time = perf_df['cycle_time'].min()
            
            # Analisi errori
            total_errors = len(error_logs)
            error_rate = (total_errors / total_cycles * 100) if total_cycles > 0 else 0
            
            # Uptime calculation (simulato)
            analysis_hours = self.config['analysis_period_days'] * 24
            expected_cycles = analysis_hours * 60  # 1 ciclo al minuto
            uptime_percent = (total_cycles / expected_cycles * 100) if expected_cycles > 0 else 0
            uptime_percent = min(uptime_percent, 100)  # Cap al 100%
            
            # Performance trend
            if 'timestamp' in perf_df.columns:
                perf_df['timestamp'] = pd.to_datetime(perf_df['timestamp'])
                daily_performance = perf_df.groupby(perf_df['timestamp'].dt.date).agg({
                    'cycle_time': ['mean', 'count']
                }).round(2)
            else:
                daily_performance = {}
            
            return {
                'total_cycles': total_cycles,
                'avg_cycle_time': avg_cycle_time,
                'max_cycle_time': max_cycle_time,
                'min_cycle_time': min_cycle_time,
                'total_errors': total_errors,
                'error_rate': error_rate,
                'uptime_percent': uptime_percent,
                'daily_performance': daily_performance.to_dict() if hasattr(daily_performance, 'to_dict') else {}
            }
            
        except Exception as e:
            self.logger.error(f"Errore analisi sistema: {e}")
            return {'error': str(e)}
    
    def analyze_ai_model_performance(self, log_data: Dict) -> Dict:
        """Analisi performance modello AI"""
        try:
            signals = log_data.get('trading_signals', [])
            
            if not signals:
                return {'error': 'Nessun segnale per analisi AI'}
            
            signals_df = pd.DataFrame(signals)
            
            # Distribuzione confidenza
            confidence_bins = pd.cut(signals_df['confidence'], bins=[0, 0.5, 0.7, 0.8, 0.9, 1.0], 
                                   labels=['Bassa', 'Media', 'Alta', 'Molto Alta', 'Eccellente'])
            confidence_distribution = confidence_bins.value_counts().to_dict()
            
            # Metriche AI
            avg_confidence = signals_df['confidence'].mean()
            confidence_std = signals_df['confidence'].std()
            high_confidence_threshold = 0.7
            model_reliability = len(signals_df[signals_df['confidence'] >= high_confidence_threshold]) / len(signals_df)
            
            # Trend confidenza nel tempo
            if 'timestamp' in signals_df.columns:
                signals_df['timestamp'] = pd.to_datetime(signals_df['timestamp'])
                confidence_trend = signals_df.groupby(signals_df['timestamp'].dt.date)['confidence'].mean()
            else:
                confidence_trend = {}
            
            # Analisi per azione
            buy_confidence = signals_df[signals_df['action'] == 'buy']['confidence'].mean() if len(signals_df[signals_df['action'] == 'buy']) > 0 else 0
            sell_confidence = signals_df[signals_df['action'] == 'sell']['confidence'].mean() if len(signals_df[signals_df['action'] == 'sell']) > 0 else 0
            
            return {
                'avg_confidence': avg_confidence,
                'confidence_std': confidence_std,
                'model_reliability': model_reliability,
                'confidence_distribution': confidence_distribution,
                'confidence_trend': confidence_trend.to_dict() if hasattr(confidence_trend, 'to_dict') else {},
                'buy_confidence': buy_confidence,
                'sell_confidence': sell_confidence,
                'total_predictions': len(signals_df)
            }
            
        except Exception as e:
            self.logger.error(f"Errore analisi AI: {e}")
            return {'error': str(e)}
    
    def calculate_risk_metrics(self, log_data: Dict) -> Dict:
        """Calcolo metriche di rischio"""
        try:
            signals = log_data.get('trading_signals', [])
            
            if not signals:
                return {'error': 'Nessun dato per analisi rischio'}
            
            signals_df = pd.DataFrame(signals)
            
            # Volatilità prezzi
            price_volatility = signals_df['price'].std() / signals_df['price'].mean() if len(signals_df) > 0 else 0
            
            # Frequenza trading
            total_signals = len(signals_df)
            days_analyzed = self.config['analysis_period_days']
            trading_frequency = total_signals / days_analyzed
            
            # Risk score (simulato)
            risk_factors = {
                'price_volatility': min(price_volatility * 100, 100),
                'trading_frequency': min(trading_frequency * 10, 100),
                'low_confidence_signals': len(signals_df[signals_df['confidence'] < 0.6]) / len(signals_df) * 100 if len(signals_df) > 0 else 0
            }
            
            overall_risk_score = np.mean(list(risk_factors.values()))
            
            # Classificazione rischio
            if overall_risk_score < 30:
                risk_level = 'BASSO'
            elif overall_risk_score < 60:
                risk_level = 'MEDIO'
            else:
                risk_level = 'ALTO'
            
            return {
                'price_volatility': price_volatility,
                'trading_frequency': trading_frequency,
                'risk_factors': risk_factors,
                'overall_risk_score': overall_risk_score,
                'risk_level': risk_level,
                'max_drawdown': 0,  # Da implementare con dati reali
                'sharpe_ratio': 0   # Da implementare con dati reali
            }
            
        except Exception as e:
            self.logger.error(f"Errore calcolo rischio: {e}")
            return {'error': str(e)}
    
    def generate_recommendations(self) -> List[str]:
        """Genera raccomandazioni basate sull'analisi"""
        recommendations = []
        
        try:
            # Analisi trading performance
            trading_perf = self.performance_metrics.get('trading_performance', {})
            system_perf = self.performance_metrics.get('system_performance', {})
            ai_perf = self.performance_metrics.get('ai_model_performance', {})
            risk_metrics = self.performance_metrics.get('risk_metrics', {})
            
            # Raccomandazioni trading
            if trading_perf.get('execution_rate', 0) < 50:
                recommendations.append("⚠️ Basso tasso di esecuzione - Verificare logica di validazione trade")
            
            if trading_perf.get('avg_confidence', 0) < 65:
                recommendations.append("🔧 Confidenza media bassa - Considerare re-training del modello AI")
            
            if trading_perf.get('high_confidence_rate', 0) > 80:
                recommendations.append("✅ Eccellente tasso di segnali ad alta confidenza - Mantieni strategia")
            
            # Raccomandazioni sistema
            if system_perf.get('uptime_percent', 0) < 95:
                recommendations.append("🚨 Uptime sotto soglia - Migliorare stabilità sistema")
            
            if system_perf.get('avg_cycle_time', 0) > 5:
                recommendations.append("⚡ Cicli lenti - Ottimizzare performance")
            
            if system_perf.get('error_rate', 0) > 5:
                recommendations.append("🐛 Alto tasso di errori - Debug necessario")
            
            # Raccomandazioni AI
            if ai_perf.get('model_reliability', 0) > 0.8:
                recommendations.append("🧠 Modello AI molto affidabile - Considera aumento position size")
            
            if ai_perf.get('confidence_std', 0) > 0.2:
                recommendations.append("📊 Alta variabilità confidenza - Stabilizzare modello")
            
            # Raccomandazioni rischio
            risk_level = risk_metrics.get('risk_level', 'MEDIO')
            if risk_level == 'ALTO':
                recommendations.append("⚠️ Rischio elevato - Ridurre esposizione")
            elif risk_level == 'BASSO':
                recommendations.append("✅ Rischio controllato - Possibile aumento esposizione")
            
            # Raccomandazioni generali
            if len(recommendations) == 0:
                recommendations.append("✅ Sistema performante - Continua monitoraggio")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Errore generazione raccomandazioni: {e}")
            return ["❌ Errore generazione raccomandazioni"]
    
    def create_performance_charts(self) -> List[str]:
        """Crea grafici di performance"""
        try:
            chart_files = []
            
            # Setup matplotlib
            plt.style.use('default')
            sns.set_palette("husl")
            
            # Chart 1: Trading Performance
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('AurumBotX Weekly Performance Analysis', fontsize=16, fontweight='bold')
            
            # Segnali per azione
            trading_perf = self.performance_metrics.get('trading_performance', {})
            if trading_perf and not trading_perf.get('error'):
                buy_signals = trading_perf.get('buy_signals', 0)
                sell_signals = trading_perf.get('sell_signals', 0)
                
                ax1.pie([buy_signals, sell_signals], labels=['BUY', 'SELL'], autopct='%1.1f%%', startangle=90)
                ax1.set_title('Distribuzione Segnali Trading')
                
                # Confidenza nel tempo
                confidence_trend = self.performance_metrics.get('ai_model_performance', {}).get('confidence_trend', {})
                if confidence_trend:
                    dates = list(confidence_trend.keys())
                    confidences = [v * 100 for v in confidence_trend.values()]
                    ax2.plot(dates, confidences, marker='o')
                    ax2.set_title('Trend Confidenza AI')
                    ax2.set_ylabel('Confidenza (%)')
                    ax2.tick_params(axis='x', rotation=45)
                
                # Performance sistema
                system_perf = self.performance_metrics.get('system_performance', {})
                if system_perf and not system_perf.get('error'):
                    metrics = ['Uptime %', 'Execution Rate %', 'Avg Confidence %']
                    values = [
                        system_perf.get('uptime_percent', 0),
                        trading_perf.get('execution_rate', 0),
                        trading_perf.get('avg_confidence', 0)
                    ]
                    
                    bars = ax3.bar(metrics, values, color=['green', 'blue', 'orange'])
                    ax3.set_title('Metriche Chiave')
                    ax3.set_ylabel('Percentuale')
                    
                    # Aggiungi valori sulle barre
                    for bar, value in zip(bars, values):
                        height = bar.get_height()
                        ax3.text(bar.get_x() + bar.get_width()/2., height + 1,
                                f'{value:.1f}%', ha='center', va='bottom')
                
                # Distribuzione confidenza
                ai_perf = self.performance_metrics.get('ai_model_performance', {})
                confidence_dist = ai_perf.get('confidence_distribution', {})
                if confidence_dist:
                    labels = list(confidence_dist.keys())
                    values = list(confidence_dist.values())
                    ax4.bar(labels, values, color='skyblue')
                    ax4.set_title('Distribuzione Confidenza')
                    ax4.set_ylabel('Numero Segnali')
                    ax4.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            chart_file = f'logs/analysis/performance_charts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            chart_files.append(chart_file)
            
            return chart_files
            
        except Exception as e:
            self.logger.error(f"Errore creazione grafici: {e}")
            return []
    
    def export_analysis_results(self) -> Dict[str, str]:
        """Esporta risultati analisi"""
        try:
            export_files = {}
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Export JSON
            json_file = f'logs/analysis/weekly_analysis_{timestamp}.json'
            with open(json_file, 'w') as f:
                json.dump(self.performance_metrics, f, indent=2, default=str)
            export_files['json'] = json_file
            
            # Export CSV (summary)
            csv_data = []
            for category, metrics in self.performance_metrics.items():
                if isinstance(metrics, dict) and not metrics.get('error'):
                    for metric, value in metrics.items():
                        if isinstance(value, (int, float)):
                            csv_data.append({
                                'Category': category,
                                'Metric': metric,
                                'Value': value
                            })
            
            if csv_data:
                csv_file = f'logs/analysis/weekly_summary_{timestamp}.csv'
                pd.DataFrame(csv_data).to_csv(csv_file, index=False)
                export_files['csv'] = csv_file
            
            return export_files
            
        except Exception as e:
            self.logger.error(f"Errore export: {e}")
            return {}
    
    def print_analysis_report(self):
        """Stampa report di analisi"""
        self.print_header("WEEKLY PERFORMANCE ANALYSIS REPORT")
        
        print(f"📅 Periodo analisi: {self.config['analysis_period_days']} giorni")
        print(f"🕐 Data analisi: {self.analysis_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Trading Performance
        self.print_section("PERFORMANCE TRADING")
        trading_perf = self.performance_metrics.get('trading_performance', {})
        if trading_perf and not trading_perf.get('error'):
            print(f"  🎯 Segnali totali: {trading_perf.get('total_signals', 0)}")
            print(f"  💹 Trade eseguiti: {trading_perf.get('total_executions', 0)}")
            print(f"  📊 Tasso esecuzione: {trading_perf.get('execution_rate', 0):.1f}%")
            print(f"  🎲 Confidenza media: {trading_perf.get('avg_confidence', 0):.1f}%")
            print(f"  📈 Segnali alta confidenza: {trading_perf.get('high_confidence_rate', 0):.1f}%")
            print(f"  📅 Segnali/giorno: {trading_perf.get('avg_signals_per_day', 0):.1f}")
        else:
            print(f"  ❌ Errore analisi trading: {trading_perf.get('error', 'Dati non disponibili')}")
        
        # System Performance
        self.print_section("PERFORMANCE SISTEMA")
        system_perf = self.performance_metrics.get('system_performance', {})
        if system_perf and not system_perf.get('error'):
            print(f"  🔄 Cicli totali: {system_perf.get('total_cycles', 0)}")
            print(f"  ⏱️ Tempo medio ciclo: {system_perf.get('avg_cycle_time', 0):.2f}s")
            print(f"  ⏰ Uptime: {system_perf.get('uptime_percent', 0):.1f}%")
            print(f"  ❌ Tasso errori: {system_perf.get('error_rate', 0):.1f}%")
        else:
            print(f"  ❌ Errore analisi sistema: {system_perf.get('error', 'Dati non disponibili')}")
        
        # AI Model Performance
        self.print_section("PERFORMANCE MODELLO AI")
        ai_perf = self.performance_metrics.get('ai_model_performance', {})
        if ai_perf and not ai_perf.get('error'):
            print(f"  🧠 Affidabilità modello: {ai_perf.get('model_reliability', 0):.1%}")
            print(f"  📊 Confidenza media: {ai_perf.get('avg_confidence', 0):.1%}")
            print(f"  📈 Predizioni totali: {ai_perf.get('total_predictions', 0)}")
            print(f"  💰 Confidenza BUY: {ai_perf.get('buy_confidence', 0):.1%}")
            print(f"  💸 Confidenza SELL: {ai_perf.get('sell_confidence', 0):.1%}")
        else:
            print(f"  ❌ Errore analisi AI: {ai_perf.get('error', 'Dati non disponibili')}")
        
        # Risk Metrics
        self.print_section("METRICHE DI RISCHIO")
        risk_metrics = self.performance_metrics.get('risk_metrics', {})
        if risk_metrics and not risk_metrics.get('error'):
            print(f"  ⚠️ Livello rischio: {risk_metrics.get('risk_level', 'N/A')}")
            print(f"  📊 Score rischio: {risk_metrics.get('overall_risk_score', 0):.1f}/100")
            print(f"  📈 Volatilità prezzi: {risk_metrics.get('price_volatility', 0):.1%}")
            print(f"  🔄 Frequenza trading: {risk_metrics.get('trading_frequency', 0):.1f} segnali/giorno")
        else:
            print(f"  ❌ Errore analisi rischio: {risk_metrics.get('error', 'Dati non disponibili')}")
        
        # Recommendations
        self.print_section("RACCOMANDAZIONI")
        recommendations = self.performance_metrics.get('recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    
    async def run_weekly_analysis(self):
        """Esegue analisi performance settimanale completa"""
        self.print_header("AVVIO ANALISI PERFORMANCE SETTIMANALE")
        
        try:
            # 1. Raccolta dati
            self.logger.info("📊 Raccolta dati dai log...")
            log_data = self.collect_log_data()
            
            if not log_data:
                self.logger.error("❌ Nessun dato trovato per l'analisi")
                return
            
            # 2. Analisi performance trading
            self.logger.info("💹 Analisi performance trading...")
            self.performance_metrics['trading_performance'] = self.analyze_trading_performance(log_data)
            
            # 3. Analisi performance sistema
            self.logger.info("🖥️ Analisi performance sistema...")
            self.performance_metrics['system_performance'] = self.analyze_system_performance(log_data)
            
            # 4. Analisi performance AI
            self.logger.info("🧠 Analisi performance modello AI...")
            self.performance_metrics['ai_model_performance'] = self.analyze_ai_model_performance(log_data)
            
            # 5. Calcolo metriche rischio
            self.logger.info("⚠️ Calcolo metriche di rischio...")
            self.performance_metrics['risk_metrics'] = self.calculate_risk_metrics(log_data)
            
            # 6. Generazione raccomandazioni
            self.logger.info("💡 Generazione raccomandazioni...")
            self.performance_metrics['recommendations'] = self.generate_recommendations()
            
            # 7. Creazione grafici
            self.logger.info("📊 Creazione grafici performance...")
            chart_files = self.create_performance_charts()
            
            # 8. Export risultati
            self.logger.info("💾 Export risultati...")
            export_files = self.export_analysis_results()
            
            # 9. Report finale
            self.print_analysis_report()
            
            # 10. Summary files
            self.print_section("FILE GENERATI")
            for format_type, file_path in export_files.items():
                print(f"  📄 {format_type.upper()}: {file_path}")
            
            for chart_file in chart_files:
                print(f"  📊 CHART: {chart_file}")
            
            self.logger.info("✅ Analisi settimanale completata con successo")
            
        except Exception as e:
            self.logger.error(f"❌ Errore durante analisi: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Main dell'analisi settimanale"""
    analyzer = WeeklyPerformanceAnalyzer()
    await analyzer.run_weekly_analysis()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

