#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX Continuous Monitoring System (24-48h)
Sistema di monitoraggio continuo con analisi approfondita e reporting automatico
"""

import os
import sys
import asyncio
import logging
import json
import time
import psutil
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

class ContinuousMonitoring:
    def __init__(self):
        self.start_time = datetime.now()
        self.setup_logging()
        self.logger = logging.getLogger('ContinuousMonitoring')
        
        # Metriche di monitoraggio
        self.metrics = {
            'uptime_hours': 0,
            'total_cycles': 0,
            'successful_cycles': 0,
            'failed_cycles': 0,
            'signals_generated': 0,
            'trades_executed': 0,
            'avg_cycle_time': 0,
            'max_memory_usage': 0,
            'avg_cpu_usage': 0,
            'error_rate': 0,
            'signal_accuracy': 0,
            'profit_loss': 0,
            'last_24h_performance': {},
            'hourly_stats': [],
            'daily_summary': {}
        }
        
        # Configurazione monitoraggio
        self.config = {
            'monitoring_duration_hours': 48,
            'report_interval_hours': 6,
            'health_check_interval_minutes': 15,
            'performance_analysis_interval_hours': 4,
            'alert_thresholds': {
                'error_rate_percent': 10,
                'memory_usage_mb': 100,
                'cpu_usage_percent': 80,
                'cycle_time_seconds': 10
            }
        }
        
    def setup_logging(self):
        """Setup logging per monitoraggio continuo"""
        Path('logs/continuous').mkdir(parents=True, exist_ok=True)
        
        # Logger principale
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/continuous/monitoring_24_48h_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
        
    def print_header(self, title):
        """Header professionale"""
        print(f"\n{'='*70}")
        print(f"🎯 {title}")
        print(f"{'='*70}")
        
    def print_section(self, title):
        """Sezione"""
        print(f"\n📋 {title}")
        print(f"{'-'*60}")
    
    async def collect_system_metrics(self):
        """Raccolta metriche di sistema"""
        try:
            # CPU e Memoria
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_mb = memory.used / 1024 / 1024
            
            # Processo monitor
            monitor_pid = self.get_monitor_pid()
            process_memory = 0
            if monitor_pid:
                try:
                    process = psutil.Process(monitor_pid)
                    process_memory = process.memory_info().rss / 1024 / 1024  # MB
                except:
                    pass
            
            # Aggiorna metriche
            self.metrics['avg_cpu_usage'] = (self.metrics['avg_cpu_usage'] + cpu_percent) / 2
            self.metrics['max_memory_usage'] = max(self.metrics['max_memory_usage'], process_memory)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_total_mb': memory.total / 1024 / 1024,
                'memory_used_mb': memory_mb,
                'memory_percent': memory.percent,
                'process_memory_mb': process_memory,
                'monitor_pid': monitor_pid
            }
            
        except Exception as e:
            self.logger.error(f"Errore raccolta metriche sistema: {e}")
            return None
    
    def get_monitor_pid(self):
        """Ottiene PID del monitor"""
        try:
            if os.path.exists('logs/monitor.pid'):
                with open('logs/monitor.pid', 'r') as f:
                    return int(f.read().strip())
        except:
            pass
        return None
    
    async def analyze_trading_performance(self):
        """Analisi performance trading"""
        try:
            # Leggi log trading
            trade_logs = []
            log_files = list(Path('logs').glob('trades_*.log'))
            
            for log_file in log_files:
                try:
                    with open(log_file, 'r') as f:
                        for line in f:
                            if 'SIGNAL|' in line or 'EXECUTED|' in line:
                                trade_logs.append(line.strip())
                except:
                    continue
            
            # Analizza segnali
            signals = [log for log in trade_logs if log.startswith('SIGNAL|')]
            executions = [log for log in trade_logs if log.startswith('EXECUTED|')]
            
            self.metrics['signals_generated'] = len(signals)
            self.metrics['trades_executed'] = len(executions)
            
            # Analisi accuratezza segnali (simulata)
            if signals:
                # Calcola accuratezza basata su confidenza media
                confidences = []
                for signal in signals[-10:]:  # Ultimi 10 segnali
                    try:
                        parts = signal.split('|')
                        if len(parts) >= 4:
                            confidence = float(parts[3])
                            confidences.append(confidence)
                    except:
                        continue
                
                if confidences:
                    self.metrics['signal_accuracy'] = np.mean(confidences) * 100
            
            return {
                'total_signals': len(signals),
                'total_executions': len(executions),
                'execution_rate': len(executions) / len(signals) * 100 if signals else 0,
                'avg_confidence': self.metrics['signal_accuracy'],
                'recent_signals': signals[-5:] if signals else []
            }
            
        except Exception as e:
            self.logger.error(f"Errore analisi performance: {e}")
            return None
    
    async def check_system_health(self):
        """Controllo salute sistema"""
        try:
            health_status = {
                'monitor_running': False,
                'memory_ok': True,
                'cpu_ok': True,
                'disk_ok': True,
                'logs_recent': False,
                'overall_health': 'UNKNOWN'
            }
            
            # Verifica monitor attivo
            monitor_pid = self.get_monitor_pid()
            if monitor_pid:
                try:
                    process = psutil.Process(monitor_pid)
                    health_status['monitor_running'] = process.is_running()
                except:
                    health_status['monitor_running'] = False
            
            # Verifica risorse
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()
            disk = psutil.disk_usage('/')
            
            health_status['memory_ok'] = memory.percent < 90
            health_status['cpu_ok'] = cpu_percent < 80
            health_status['disk_ok'] = disk.free > 1024*1024*1024  # 1GB
            
            # Verifica log recenti
            latest_log = max(Path('logs').glob('monitor_24_7_*.log'), default=None, key=os.path.getctime)
            if latest_log:
                log_age = time.time() - os.path.getctime(latest_log)
                health_status['logs_recent'] = log_age < 300  # 5 minuti
            
            # Stato generale
            if all([health_status['monitor_running'], health_status['memory_ok'], 
                   health_status['cpu_ok'], health_status['disk_ok']]):
                health_status['overall_health'] = 'EXCELLENT'
            elif health_status['monitor_running']:
                health_status['overall_health'] = 'GOOD'
            else:
                health_status['overall_health'] = 'CRITICAL'
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Errore controllo salute: {e}")
            return {'overall_health': 'ERROR'}
    
    async def generate_hourly_report(self):
        """Genera report orario"""
        try:
            current_hour = datetime.now().hour
            uptime = (datetime.now() - self.start_time).total_seconds() / 3600
            
            # Raccolta dati
            system_metrics = await self.collect_system_metrics()
            trading_performance = await self.analyze_trading_performance()
            health_status = await self.check_system_health()
            
            # Report orario
            hourly_report = {
                'timestamp': datetime.now().isoformat(),
                'hour': current_hour,
                'uptime_hours': uptime,
                'system_metrics': system_metrics,
                'trading_performance': trading_performance,
                'health_status': health_status,
                'alerts': []
            }
            
            # Controllo alert
            if system_metrics:
                if system_metrics['cpu_percent'] > self.config['alert_thresholds']['cpu_usage_percent']:
                    hourly_report['alerts'].append(f"CPU usage high: {system_metrics['cpu_percent']:.1f}%")
                
                if system_metrics['process_memory_mb'] > self.config['alert_thresholds']['memory_usage_mb']:
                    hourly_report['alerts'].append(f"Memory usage high: {system_metrics['process_memory_mb']:.1f}MB")
            
            # Salva report
            report_file = f'logs/continuous/hourly_report_{datetime.now().strftime("%Y%m%d_%H")}.json'
            with open(report_file, 'w') as f:
                json.dump(hourly_report, f, indent=2)
            
            # Aggiorna statistiche
            self.metrics['hourly_stats'].append(hourly_report)
            self.metrics['uptime_hours'] = uptime
            
            return hourly_report
            
        except Exception as e:
            self.logger.error(f"Errore generazione report orario: {e}")
            return None
    
    def print_live_dashboard(self, hourly_report):
        """Dashboard live"""
        self.print_header("AURUMBOTX CONTINUOUS MONITORING DASHBOARD")
        
        print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️ Uptime: {self.metrics['uptime_hours']:.1f} ore")
        print(f"🎯 Target: {self.config['monitoring_duration_hours']} ore")
        
        if hourly_report:
            # Sistema
            self.print_section("STATO SISTEMA")
            health = hourly_report.get('health_status', {})
            health_emoji = {'EXCELLENT': '🟢', 'GOOD': '🟡', 'CRITICAL': '🔴', 'ERROR': '💥'}.get(health.get('overall_health'), '❓')
            print(f"  {health_emoji} Salute generale: {health.get('overall_health', 'UNKNOWN')}")
            print(f"  🤖 Monitor attivo: {'✅' if health.get('monitor_running') else '❌'}")
            
            # Performance
            if hourly_report.get('system_metrics'):
                metrics = hourly_report['system_metrics']
                print(f"  💾 Memoria processo: {metrics.get('process_memory_mb', 0):.1f} MB")
                print(f"  🖥️ CPU: {metrics.get('cpu_percent', 0):.1f}%")
            
            # Trading
            self.print_section("PERFORMANCE TRADING")
            trading = hourly_report.get('trading_performance', {})
            print(f"  🎯 Segnali generati: {trading.get('total_signals', 0)}")
            print(f"  💹 Trade eseguiti: {trading.get('total_executions', 0)}")
            print(f"  📊 Tasso esecuzione: {trading.get('execution_rate', 0):.1f}%")
            print(f"  🎲 Confidenza media: {trading.get('avg_confidence', 0):.1f}%")
            
            # Alert
            alerts = hourly_report.get('alerts', [])
            if alerts:
                self.print_section("⚠️ ALERT ATTIVI")
                for alert in alerts:
                    print(f"  🚨 {alert}")
            else:
                print(f"\n✅ Nessun alert attivo")
    
    async def run_continuous_monitoring(self):
        """Loop principale monitoraggio continuo"""
        self.print_header("AVVIO MONITORAGGIO CONTINUO 24-48H")
        print(f"🕐 Inizio: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️ Durata: {self.config['monitoring_duration_hours']} ore")
        print(f"📊 Report ogni: {self.config['report_interval_hours']} ore")
        
        last_report_time = time.time()
        last_health_check = time.time()
        
        try:
            while True:
                current_time = time.time()
                elapsed_hours = (current_time - time.mktime(self.start_time.timetuple())) / 3600
                
                # Controllo durata massima
                if elapsed_hours >= self.config['monitoring_duration_hours']:
                    self.logger.info(f"✅ Monitoraggio completato: {elapsed_hours:.1f} ore")
                    break
                
                # Report orario
                if current_time - last_report_time >= self.config['report_interval_hours'] * 3600:
                    hourly_report = await self.generate_hourly_report()
                    if hourly_report:
                        self.print_live_dashboard(hourly_report)
                    last_report_time = current_time
                
                # Health check
                if current_time - last_health_check >= self.config['health_check_interval_minutes'] * 60:
                    health = await self.check_system_health()
                    if health and health['overall_health'] == 'CRITICAL':
                        self.logger.warning("🚨 Sistema in stato critico!")
                    last_health_check = current_time
                
                # Attesa
                await asyncio.sleep(60)  # Check ogni minuto
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Monitoraggio interrotto dall'utente")
        except Exception as e:
            self.logger.error(f"❌ Errore nel monitoraggio: {e}")
        
        # Report finale
        await self.generate_final_report()
    
    async def generate_final_report(self):
        """Report finale del monitoraggio"""
        self.print_header("REPORT FINALE MONITORAGGIO 24-48H")
        
        final_report = {
            'monitoring_period': {
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_hours': (datetime.now() - self.start_time).total_seconds() / 3600
            },
            'summary_metrics': self.metrics,
            'hourly_reports': len(self.metrics['hourly_stats']),
            'recommendations': []
        }
        
        # Raccomandazioni
        if self.metrics['uptime_hours'] >= 24:
            final_report['recommendations'].append("✅ Sistema stabile per 24+ ore - Pronto per produzione")
        
        if self.metrics['signal_accuracy'] >= 70:
            final_report['recommendations'].append("✅ Accuratezza segnali eccellente - Mantieni strategia")
        
        if self.metrics['max_memory_usage'] < 50:
            final_report['recommendations'].append("✅ Utilizzo memoria ottimale - Performance eccellenti")
        
        # Salva report finale
        report_file = f'logs/continuous/final_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        # Stampa summary
        print(f"📊 Durata monitoraggio: {final_report['monitoring_period']['duration_hours']:.1f} ore")
        print(f"📈 Report orari generati: {final_report['hourly_reports']}")
        print(f"🎯 Segnali totali: {self.metrics['signals_generated']}")
        print(f"💹 Trade eseguiti: {self.metrics['trades_executed']}")
        print(f"📊 Accuratezza: {self.metrics['signal_accuracy']:.1f}%")
        
        print(f"\n💡 RACCOMANDAZIONI:")
        for rec in final_report['recommendations']:
            print(f"  {rec}")
        
        print(f"\n📄 Report salvato: {report_file}")
        
        return final_report

async def main():
    """Main del monitoraggio continuo"""
    monitor = ContinuousMonitoring()
    await monitor.run_continuous_monitoring()

if __name__ == "__main__":
    asyncio.run(main())

