#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX 2-Hour Monitor & Reporter
Sistema di monitoraggio ogni 2 ore con invio automatico dati
"""

import os
import sys
import json
import asyncio
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
# Email imports rimossi per compatibilità sandbox

# Aggiungi path del progetto
sys.path.append('/home/ubuntu/AurumBotX')

class TwoHourMonitorReporter:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('TwoHourReporter')
        self.start_time = datetime.now()
        
        # Configurazione monitoraggio
        self.config = {
            'monitoring_interval_hours': 2,
            'report_format': 'detailed',  # detailed, summary, json
            'auto_restart_bot': True,
            'max_downtime_minutes': 5,
            'alert_thresholds': {
                'min_signals_per_2h': 2,
                'min_confidence': 0.65,
                'max_error_rate': 10,
                'min_uptime_percent': 95
            }
        }
        
        # Metriche accumulate
        self.session_metrics = {
            'start_time': self.start_time.isoformat(),
            'total_reports': 0,
            'total_signals': 0,
            'total_cycles': 0,
            'avg_confidence': 0,
            'uptime_percent': 100,
            'last_signal_time': None,
            'performance_trend': [],
            'alerts_generated': []
        }
        
        # Configurazione notifiche (placeholder)
        self.notification_config = {
            'email_enabled': False,  # Disabilitato per sandbox
            'webhook_enabled': True,
            'console_enabled': True,
            'file_enabled': True
        }
        
    def setup_logging(self):
        """Setup logging per reporter"""
        Path('logs/2h_reports').mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/2h_reports/monitor_2h_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
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
    
    def check_bot_status(self) -> Dict[str, Any]:
        """Controlla stato del bot"""
        try:
            status = {
                'is_running': False,
                'pid': None,
                'uptime_hours': 0,
                'memory_mb': 0,
                'last_activity': None,
                'health_status': 'UNKNOWN'
            }
            
            # Controlla PID file
            pid_file = 'logs/monitor.pid'
            if os.path.exists(pid_file):
                try:
                    with open(pid_file, 'r') as f:
                        pid = int(f.read().strip())
                    
                    # Verifica se processo è attivo
                    import psutil
                    if psutil.pid_exists(pid):
                        process = psutil.Process(pid)
                        if process.is_running():
                            status['is_running'] = True
                            status['pid'] = pid
                            
                            # Calcola uptime
                            create_time = datetime.fromtimestamp(process.create_time())
                            uptime = datetime.now() - create_time
                            status['uptime_hours'] = uptime.total_seconds() / 3600
                            
                            # Memoria
                            status['memory_mb'] = process.memory_info().rss / 1024 / 1024
                            
                except Exception as e:
                    self.logger.warning(f"Errore lettura PID: {e}")
            
            # Controlla attività recente dai log
            try:
                log_files = list(Path('logs').glob('monitor_startup.log'))
                if log_files:
                    latest_log = max(log_files, key=os.path.getctime)
                    
                    # Leggi ultime righe
                    with open(latest_log, 'r') as f:
                        lines = f.readlines()
                    
                    if lines:
                        last_line = lines[-1]
                        if 'CICLO' in last_line or 'Segnale' in last_line:
                            # Estrai timestamp
                            try:
                                timestamp_str = last_line.split(' - ')[0]
                                status['last_activity'] = timestamp_str
                                
                                # Verifica se attività recente (< 5 minuti)
                                last_time = datetime.strptime(timestamp_str.split(',')[0], '%Y-%m-%d %H:%M:%S')
                                time_diff = datetime.now() - last_time
                                
                                if time_diff.total_seconds() < 300:  # 5 minuti
                                    status['health_status'] = 'HEALTHY'
                                elif time_diff.total_seconds() < 600:  # 10 minuti
                                    status['health_status'] = 'WARNING'
                                else:
                                    status['health_status'] = 'CRITICAL'
                                    
                            except:
                                pass
            except Exception as e:
                self.logger.warning(f"Errore controllo attività: {e}")
            
            return status
            
        except Exception as e:
            self.logger.error(f"Errore controllo stato bot: {e}")
            return {'is_running': False, 'health_status': 'ERROR'}
    
    def collect_performance_data(self) -> Dict[str, Any]:
        """Raccoglie dati di performance delle ultime 2 ore"""
        try:
            performance_data = {
                'signals_generated': 0,
                'avg_confidence': 0,
                'signal_distribution': {'buy': 0, 'sell': 0},
                'price_range': {'min': 0, 'max': 0, 'current': 0},
                'cycle_performance': {'total': 0, 'avg_time': 0},
                'error_count': 0,
                'last_signals': []
            }
            
            # Periodo di analisi (ultime 2 ore)
            cutoff_time = datetime.now() - timedelta(hours=2)
            
            # Analizza log trading
            signals = []
            cycles = []
            errors = 0
            
            log_files = list(Path('logs').glob('*.log'))
            
            for log_file in log_files:
                try:
                    # Filtra per data se possibile
                    file_time = datetime.fromtimestamp(os.path.getctime(log_file))
                    if file_time < cutoff_time:
                        continue
                    
                    with open(log_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            
                            # Parsing segnali
                            if 'SIGNAL|' in line:
                                try:
                                    parts = line.split('|')
                                    if len(parts) >= 5:
                                        signals.append({
                                            'timestamp': self.extract_timestamp(line),
                                            'pair': parts[1],
                                            'action': parts[2],
                                            'confidence': float(parts[3]),
                                            'price': float(parts[4])
                                        })
                                except:
                                    continue
                            
                            # Parsing cicli
                            elif 'Ciclo completato' in line:
                                try:
                                    if 'in ' in line and 's' in line:
                                        time_part = line.split('in ')[1].split('s')[0]
                                        cycle_time = float(time_part)
                                        cycles.append(cycle_time)
                                except:
                                    continue
                            
                            # Conteggio errori
                            elif 'ERROR' in line:
                                errors += 1
                                
                except Exception as e:
                    continue
            
            # Elabora dati raccolti
            if signals:
                performance_data['signals_generated'] = len(signals)
                performance_data['avg_confidence'] = np.mean([s['confidence'] for s in signals])
                
                # Distribuzione azioni
                actions = [s['action'] for s in signals]
                performance_data['signal_distribution']['buy'] = actions.count('buy')
                performance_data['signal_distribution']['sell'] = actions.count('sell')
                
                # Range prezzi
                prices = [s['price'] for s in signals]
                performance_data['price_range'] = {
                    'min': min(prices),
                    'max': max(prices),
                    'current': prices[-1] if prices else 0
                }
                
                # Ultimi 5 segnali
                performance_data['last_signals'] = signals[-5:]
            
            if cycles:
                performance_data['cycle_performance'] = {
                    'total': len(cycles),
                    'avg_time': np.mean(cycles)
                }
            
            performance_data['error_count'] = errors
            
            return performance_data
            
        except Exception as e:
            self.logger.error(f"Errore raccolta performance: {e}")
            return {}
    
    def extract_timestamp(self, log_line: str) -> Optional[str]:
        """Estrae timestamp da riga di log"""
        try:
            if log_line.startswith('20'):
                return log_line.split(' - ')[0].replace(',', '.')
            return None
        except:
            return None
    
    def generate_alerts(self, bot_status: Dict, performance_data: Dict) -> List[str]:
        """Genera alert basati su soglie"""
        alerts = []
        
        try:
            # Alert bot non attivo
            if not bot_status.get('is_running', False):
                alerts.append("🚨 CRITICO: Bot non in esecuzione")
            
            # Alert salute bot
            health = bot_status.get('health_status', 'UNKNOWN')
            if health == 'CRITICAL':
                alerts.append("🚨 CRITICO: Bot non risponde da oltre 10 minuti")
            elif health == 'WARNING':
                alerts.append("⚠️ WARNING: Bot non risponde da oltre 5 minuti")
            
            # Alert performance
            signals_2h = performance_data.get('signals_generated', 0)
            if signals_2h < self.config['alert_thresholds']['min_signals_per_2h']:
                alerts.append(f"⚠️ WARNING: Pochi segnali nelle ultime 2h ({signals_2h})")
            
            avg_confidence = performance_data.get('avg_confidence', 0)
            if avg_confidence < self.config['alert_thresholds']['min_confidence']:
                alerts.append(f"⚠️ WARNING: Confidenza bassa ({avg_confidence:.1%})")
            
            error_count = performance_data.get('error_count', 0)
            if error_count > 5:
                alerts.append(f"⚠️ WARNING: Molti errori nelle ultime 2h ({error_count})")
            
            # Alert memoria
            memory_mb = bot_status.get('memory_mb', 0)
            if memory_mb > 100:
                alerts.append(f"⚠️ WARNING: Uso memoria elevato ({memory_mb:.1f}MB)")
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Errore generazione alert: {e}")
            return ["❌ Errore generazione alert"]
    
    def create_2h_report(self, bot_status: Dict, performance_data: Dict, alerts: List[str]) -> Dict[str, Any]:
        """Crea report completo 2 ore"""
        try:
            report = {
                'report_timestamp': datetime.now().isoformat(),
                'report_period_hours': 2,
                'session_info': {
                    'session_start': self.session_metrics['start_time'],
                    'total_reports_generated': self.session_metrics['total_reports'] + 1,
                    'monitoring_uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600
                },
                'bot_status': bot_status,
                'performance_2h': performance_data,
                'alerts': alerts,
                'summary': {
                    'overall_health': 'HEALTHY' if not alerts else 'WARNING' if len(alerts) < 3 else 'CRITICAL',
                    'signals_per_hour': performance_data.get('signals_generated', 0) / 2,
                    'avg_confidence_percent': performance_data.get('avg_confidence', 0) * 100,
                    'bot_uptime_hours': bot_status.get('uptime_hours', 0),
                    'memory_usage_mb': bot_status.get('memory_mb', 0)
                },
                'recommendations': []
            }
            
            # Genera raccomandazioni
            if not bot_status.get('is_running'):
                report['recommendations'].append("🔧 Riavviare il bot immediatamente")
            
            if performance_data.get('signals_generated', 0) == 0:
                report['recommendations'].append("📊 Verificare connessione dati di mercato")
            
            if performance_data.get('avg_confidence', 0) < 0.7:
                report['recommendations'].append("🧠 Considerare re-training del modello AI")
            
            if not report['recommendations']:
                report['recommendations'].append("✅ Sistema operativo - Continua monitoraggio")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Errore creazione report: {e}")
            return {}
    
    def save_report(self, report: Dict) -> str:
        """Salva report su file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Salva JSON completo
            json_file = f'logs/2h_reports/report_2h_{timestamp}.json'
            with open(json_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            # Salva summary leggibile
            summary_file = f'logs/2h_reports/summary_2h_{timestamp}.txt'
            with open(summary_file, 'w') as f:
                f.write(f"AurumBotX 2-Hour Report\\n")
                f.write(f"Generated: {report['report_timestamp']}\\n")
                f.write(f"{'='*50}\\n\\n")
                
                f.write(f"BOT STATUS:\\n")
                f.write(f"  Running: {'Yes' if report['bot_status']['is_running'] else 'No'}\\n")
                f.write(f"  Health: {report['bot_status']['health_status']}\\n")
                f.write(f"  Uptime: {report['bot_status']['uptime_hours']:.1f}h\\n")
                f.write(f"  Memory: {report['bot_status']['memory_mb']:.1f}MB\\n\\n")
                
                f.write(f"PERFORMANCE (2h):\\n")
                f.write(f"  Signals: {report['performance_2h']['signals_generated']}\\n")
                f.write(f"  Avg Confidence: {report['performance_2h']['avg_confidence']:.1%}\\n")
                f.write(f"  Cycles: {report['performance_2h']['cycle_performance']['total']}\\n")
                f.write(f"  Errors: {report['performance_2h']['error_count']}\\n\\n")
                
                if report['alerts']:
                    f.write(f"ALERTS:\\n")
                    for alert in report['alerts']:
                        f.write(f"  - {alert}\\n")
                    f.write("\\n")
                
                f.write(f"RECOMMENDATIONS:\\n")
                for rec in report['recommendations']:
                    f.write(f"  - {rec}\\n")
            
            return json_file
            
        except Exception as e:
            self.logger.error(f"Errore salvataggio report: {e}")
            return ""
    
    def print_report(self, report: Dict):
        """Stampa report su console"""
        self.print_header(f"AURUMBOTX 2-HOUR REPORT #{self.session_metrics['total_reports'] + 1}")
        
        print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Periodo: Ultime 2 ore")
        print(f"⏱️ Session uptime: {(datetime.now() - self.start_time).total_seconds() / 3600:.1f}h")
        
        # Stato bot
        self.print_section("STATO BOT")
        bot_status = report['bot_status']
        status_emoji = "✅" if bot_status['is_running'] else "❌"
        health_emoji = {"HEALTHY": "🟢", "WARNING": "🟡", "CRITICAL": "🔴", "ERROR": "💥"}.get(bot_status['health_status'], "❓")
        
        print(f"  {status_emoji} Running: {'Sì' if bot_status['is_running'] else 'No'}")
        print(f"  {health_emoji} Health: {bot_status['health_status']}")
        print(f"  ⏰ Uptime: {bot_status['uptime_hours']:.1f} ore")
        print(f"  💾 Memoria: {bot_status['memory_mb']:.1f} MB")
        if bot_status['last_activity']:
            print(f"  🕐 Ultima attività: {bot_status['last_activity']}")
        
        # Performance
        self.print_section("PERFORMANCE ULTIME 2H")
        perf = report['performance_2h']
        print(f"  🎯 Segnali generati: {perf['signals_generated']}")
        print(f"  📊 Confidenza media: {perf['avg_confidence']:.1%}")
        print(f"  📈 BUY signals: {perf['signal_distribution']['buy']}")
        print(f"  📉 SELL signals: {perf['signal_distribution']['sell']}")
        print(f"  🔄 Cicli completati: {perf['cycle_performance']['total']}")
        print(f"  ⏱️ Tempo medio ciclo: {perf['cycle_performance']['avg_time']:.2f}s")
        print(f"  ❌ Errori: {perf['error_count']}")
        
        if perf['price_range']['current']:
            print(f"  💰 Prezzo corrente: ${perf['price_range']['current']:,.2f}")
            print(f"  📊 Range 2h: ${perf['price_range']['min']:,.2f} - ${perf['price_range']['max']:,.2f}")
        
        # Alert
        alerts = report['alerts']
        if alerts:
            self.print_section("🚨 ALERT ATTIVI")
            for alert in alerts:
                print(f"  {alert}")
        else:
            print(f"\n✅ Nessun alert attivo")
        
        # Summary
        self.print_section("SUMMARY")
        summary = report['summary']
        overall_emoji = {"HEALTHY": "🟢", "WARNING": "🟡", "CRITICAL": "🔴"}.get(summary['overall_health'], "❓")
        print(f"  {overall_emoji} Salute generale: {summary['overall_health']}")
        print(f"  📊 Segnali/ora: {summary['signals_per_hour']:.1f}")
        print(f"  🎯 Confidenza: {summary['avg_confidence_percent']:.1f}%")
        
        # Raccomandazioni
        self.print_section("RACCOMANDAZIONI")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    def restart_bot_if_needed(self, bot_status: Dict) -> bool:
        """Riavvia bot se necessario"""
        try:
            if not self.config['auto_restart_bot']:
                return False
            
            if not bot_status.get('is_running', False):
                self.logger.info("🔄 Tentativo riavvio bot...")
                
                # Comando riavvio
                import subprocess
                result = subprocess.run(
                    ['./start_monitor_24_7.sh', 'restart'],
                    cwd='/home/ubuntu/AurumBotX',
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    self.logger.info("✅ Bot riavviato con successo")
                    return True
                else:
                    self.logger.error(f"❌ Errore riavvio bot: {result.stderr}")
                    return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Errore riavvio bot: {e}")
            return False
    
    async def monitoring_cycle(self):
        """Ciclo di monitoraggio ogni 2 ore"""
        try:
            self.logger.info(f"📊 Avvio ciclo monitoraggio 2h #{self.session_metrics['total_reports'] + 1}")
            
            # 1. Controlla stato bot
            bot_status = self.check_bot_status()
            
            # 2. Raccoglie dati performance
            performance_data = self.collect_performance_data()
            
            # 3. Genera alert
            alerts = self.generate_alerts(bot_status, performance_data)
            
            # 4. Riavvia bot se necessario
            if alerts and self.config['auto_restart_bot']:
                restarted = self.restart_bot_if_needed(bot_status)
                if restarted:
                    alerts.append("🔄 Bot riavviato automaticamente")
                    # Re-check status dopo riavvio
                    await asyncio.sleep(10)
                    bot_status = self.check_bot_status()
            
            # 5. Crea report
            report = self.create_2h_report(bot_status, performance_data, alerts)
            
            # 6. Salva report
            report_file = self.save_report(report)
            
            # 7. Stampa report
            self.print_report(report)
            
            # 8. Aggiorna metriche sessione
            self.session_metrics['total_reports'] += 1
            self.session_metrics['total_signals'] += performance_data.get('signals_generated', 0)
            self.session_metrics['total_cycles'] += performance_data.get('cycle_performance', {}).get('total', 0)
            
            if performance_data.get('avg_confidence'):
                self.session_metrics['avg_confidence'] = (
                    self.session_metrics['avg_confidence'] + performance_data['avg_confidence']
                ) / 2
            
            if alerts:
                self.session_metrics['alerts_generated'].extend(alerts)
            
            # 9. Log risultati
            self.logger.info(f"✅ Report 2h completato - File: {report_file}")
            self.logger.info(f"📊 Segnali: {performance_data.get('signals_generated', 0)} | "
                           f"Confidenza: {performance_data.get('avg_confidence', 0):.1%} | "
                           f"Alert: {len(alerts)}")
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Errore ciclo monitoraggio: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    async def run_2h_monitoring(self):
        """Esegue monitoraggio continuo ogni 2 ore"""
        self.print_header("AVVIO MONITORAGGIO 2H AURUMBOTX")
        
        print(f"🕐 Inizio: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️ Intervallo: {self.config['monitoring_interval_hours']} ore")
        print(f"🔄 Auto-restart: {'Abilitato' if self.config['auto_restart_bot'] else 'Disabilitato'}")
        print(f"📊 Formato report: {self.config['report_format']}")
        
        try:
            # Primo report immediato
            self.logger.info("📊 Generazione report iniziale...")
            await self.monitoring_cycle()
            
            # Loop principale
            while True:
                # Attesa 2 ore
                wait_seconds = self.config['monitoring_interval_hours'] * 3600
                self.logger.info(f"⏳ Attesa {self.config['monitoring_interval_hours']}h per prossimo report...")
                
                await asyncio.sleep(wait_seconds)
                
                # Nuovo ciclo
                await self.monitoring_cycle()
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Monitoraggio interrotto dall'utente")
        except Exception as e:
            self.logger.error(f"❌ Errore nel monitoraggio: {e}")
            import traceback
            traceback.print_exc()
        
        # Report finale sessione
        self.print_section("REPORT FINALE SESSIONE")
        session_duration = (datetime.now() - self.start_time).total_seconds() / 3600
        print(f"  ⏱️ Durata sessione: {session_duration:.1f} ore")
        print(f"  📊 Report generati: {self.session_metrics['total_reports']}")
        print(f"  🎯 Segnali totali: {self.session_metrics['total_signals']}")
        print(f"  🔄 Cicli totali: {self.session_metrics['total_cycles']}")
        print(f"  📈 Confidenza media: {self.session_metrics['avg_confidence']:.1%}")
        print(f"  🚨 Alert generati: {len(self.session_metrics['alerts_generated'])}")

async def main():
    """Main del monitoraggio 2h"""
    reporter = TwoHourMonitorReporter()
    await reporter.run_2h_monitoring()

if __name__ == "__main__":
    asyncio.run(main())

