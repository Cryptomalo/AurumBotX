#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX System Capacity Analyzer
Analizza capacità sistema per determinare numero massimo bot
"""

import psutil
import subprocess
import json
import time
from datetime import datetime

class SystemCapacityAnalyzer:
    """Analizzatore capacità sistema"""
    
    def __init__(self):
        self.current_processes = self.get_trading_processes()
        self.system_specs = self.get_system_specs()
        
    def get_system_specs(self):
        """Ottieni specifiche sistema"""
        return {
            'cpu_cores': psutil.cpu_count(logical=True),
            'cpu_physical': psutil.cpu_count(logical=False),
            'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'memory_available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
            'disk_total_gb': round(psutil.disk_usage('/').total / (1024**3), 2),
            'disk_free_gb': round(psutil.disk_usage('/').free / (1024**3), 2)
        }
    
    def get_trading_processes(self):
        """Identifica processi trading attivi"""
        trading_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                
                if any(keyword in cmdline for keyword in [
                    'mega_aggressive_trading.py',
                    'ultra_aggressive_trading.py', 
                    'mainnet_optimization_strategies.py'
                ]):
                    
                    # Calcola CPU usage
                    cpu_percent = proc.cpu_percent(interval=1)
                    
                    trading_processes.append({
                        'pid': proc.info['pid'],
                        'name': self.extract_bot_name(cmdline),
                        'memory_mb': round(proc.info['memory_info'].rss / (1024**2), 2),
                        'cpu_percent': cpu_percent,
                        'cmdline': cmdline
                    })
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return trading_processes
    
    def extract_bot_name(self, cmdline):
        """Estrai nome bot da command line"""
        if 'mega_aggressive' in cmdline:
            return 'mega_aggressive'
        elif 'ultra_aggressive' in cmdline:
            return 'ultra_aggressive'
        elif 'mainnet_optimization' in cmdline:
            return 'mainnet_optimization'
        else:
            return 'unknown'
    
    def calculate_resource_usage_per_bot(self):
        """Calcola uso risorse medio per bot"""
        if not self.current_processes:
            # Stima basata su osservazioni tipiche
            return {
                'memory_mb_avg': 100,  # ~100MB per bot trading
                'cpu_percent_avg': 2,   # ~2% CPU per bot
                'estimated': True
            }
        
        total_memory = sum(p['memory_mb'] for p in self.current_processes)
        total_cpu = sum(p['cpu_percent'] for p in self.current_processes)
        count = len(self.current_processes)
        
        return {
            'memory_mb_avg': round(total_memory / count, 2),
            'cpu_percent_avg': round(total_cpu / count, 2),
            'estimated': False,
            'sample_size': count
        }
    
    def calculate_dashboard_overhead(self):
        """Calcola overhead dashboard Streamlit"""
        dashboard_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                
                if 'streamlit run' in cmdline and any(keyword in cmdline for keyword in [
                    'dashboard', 'admin', 'mobile', 'premium', 'config'
                ]):
                    dashboard_processes.append({
                        'memory_mb': round(proc.info['memory_info'].rss / (1024**2), 2),
                        'cpu_percent': proc.cpu_percent(interval=0.1)
                    })
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if dashboard_processes:
            total_memory = sum(p['memory_mb'] for p in dashboard_processes)
            total_cpu = sum(p['cpu_percent'] for p in dashboard_processes)
            
            return {
                'total_memory_mb': total_memory,
                'total_cpu_percent': total_cpu,
                'count': len(dashboard_processes),
                'avg_memory_mb': round(total_memory / len(dashboard_processes), 2)
            }
        else:
            return {
                'total_memory_mb': 500,  # Stima 500MB per dashboard
                'total_cpu_percent': 5,   # Stima 5% CPU per dashboard
                'count': 0,
                'avg_memory_mb': 100
            }
    
    def calculate_max_bots(self):
        """Calcola numero massimo bot supportabili"""
        specs = self.system_specs
        bot_usage = self.calculate_resource_usage_per_bot()
        dashboard_overhead = self.calculate_dashboard_overhead()
        
        # Riserva risorse sistema (20% memoria, 30% CPU)
        memory_reserve_gb = specs['memory_total_gb'] * 0.2
        cpu_reserve_percent = 30
        
        # Memoria disponibile per bot
        available_memory_gb = specs['memory_available_gb'] - memory_reserve_gb - (dashboard_overhead['total_memory_mb'] / 1024)
        available_memory_mb = available_memory_gb * 1024
        
        # CPU disponibile per bot
        available_cpu_percent = 100 - cpu_reserve_percent - dashboard_overhead['total_cpu_percent']
        
        # Calcola limiti
        memory_limit = int(available_memory_mb / bot_usage['memory_mb_avg']) if bot_usage['memory_mb_avg'] > 0 else 0
        cpu_limit = int(available_cpu_percent / bot_usage['cpu_percent_avg']) if bot_usage['cpu_percent_avg'] > 0 else 0
        
        # Il limite è il minore tra memoria e CPU
        max_bots = min(memory_limit, cpu_limit)
        
        # Considera anche I/O e database locks (limite pratico)
        io_limit = 15  # Limite empirico per I/O database SQLite
        practical_limit = min(max_bots, io_limit)
        
        return {
            'theoretical_max': max_bots,
            'practical_max': practical_limit,
            'memory_limit': memory_limit,
            'cpu_limit': cpu_limit,
            'io_limit': io_limit,
            'current_bots': len(self.current_processes),
            'available_slots': max(0, practical_limit - len(self.current_processes))
        }
    
    def get_optimization_recommendations(self):
        """Genera raccomandazioni ottimizzazione"""
        specs = self.system_specs
        bot_usage = self.calculate_resource_usage_per_bot()
        max_bots = self.calculate_max_bots()
        
        recommendations = []
        
        # Raccomandazioni memoria
        if specs['memory_available_gb'] < 1:
            recommendations.append({
                'type': 'memory',
                'priority': 'high',
                'message': 'Memoria bassa (<1GB), considera upgrade RAM o riduzione bot',
                'action': 'Chiudi dashboard non essenziali o upgrade sistema'
            })
        elif specs['memory_available_gb'] < 2:
            recommendations.append({
                'type': 'memory',
                'priority': 'medium',
                'message': 'Memoria limitata (<2GB), monitoraggio necessario',
                'action': 'Ottimizza parametri bot per ridurre uso memoria'
            })
        
        # Raccomandazioni CPU
        cpu_usage = psutil.cpu_percent(interval=1)
        if cpu_usage > 80:
            recommendations.append({
                'type': 'cpu',
                'priority': 'high',
                'message': f'CPU usage alto ({cpu_usage:.1f}%), rischio degradazione',
                'action': 'Riduci frequenza trading o numero bot attivi'
            })
        
        # Raccomandazioni I/O
        if len(self.current_processes) > 10:
            recommendations.append({
                'type': 'io',
                'priority': 'medium',
                'message': 'Molti bot attivi, possibili conflitti database',
                'action': 'Considera database separati o connection pooling'
            })
        
        # Raccomandazioni ottimizzazione
        if bot_usage['memory_mb_avg'] > 150:
            recommendations.append({
                'type': 'optimization',
                'priority': 'low',
                'message': 'Uso memoria per bot elevato, ottimizzazione possibile',
                'action': 'Riduci cache, ottimizza data structures'
            })
        
        return recommendations
    
    def create_scaling_plan(self):
        """Crea piano di scaling"""
        max_bots = self.calculate_max_bots()
        current = len(self.current_processes)
        
        scaling_plan = {
            'current_capacity': {
                'bots_active': current,
                'bots_max_safe': max_bots['practical_max'],
                'utilization_percent': round((current / max_bots['practical_max'] * 100), 1) if max_bots['practical_max'] > 0 else 0
            },
            'scaling_phases': []
        }
        
        # Fase 1: Utilizzo attuale
        if current < max_bots['practical_max'] * 0.5:
            scaling_plan['scaling_phases'].append({
                'phase': 1,
                'target_bots': min(current + 3, int(max_bots['practical_max'] * 0.5)),
                'description': 'Scaling conservativo - fino al 50% capacità',
                'risk': 'low',
                'monitoring': 'standard'
            })
        
        # Fase 2: Utilizzo medio
        if max_bots['practical_max'] > 5:
            scaling_plan['scaling_phases'].append({
                'phase': 2,
                'target_bots': int(max_bots['practical_max'] * 0.75),
                'description': 'Scaling moderato - fino al 75% capacità',
                'risk': 'medium',
                'monitoring': 'enhanced'
            })
        
        # Fase 3: Utilizzo massimo
        if max_bots['practical_max'] > 8:
            scaling_plan['scaling_phases'].append({
                'phase': 3,
                'target_bots': max_bots['practical_max'],
                'description': 'Scaling massimo - 100% capacità',
                'risk': 'high',
                'monitoring': 'intensive'
            })
        
        return scaling_plan
    
    def generate_report(self):
        """Genera report completo capacità"""
        specs = self.system_specs
        bot_usage = self.calculate_resource_usage_per_bot()
        dashboard_overhead = self.calculate_dashboard_overhead()
        max_bots = self.calculate_max_bots()
        recommendations = self.get_optimization_recommendations()
        scaling_plan = self.create_scaling_plan()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_specs': specs,
            'current_usage': {
                'trading_bots': len(self.current_processes),
                'dashboard_processes': dashboard_overhead['count'],
                'total_memory_used_gb': round((specs['memory_total_gb'] - specs['memory_available_gb']), 2),
                'memory_utilization_percent': round(((specs['memory_total_gb'] - specs['memory_available_gb']) / specs['memory_total_gb'] * 100), 1)
            },
            'bot_resource_usage': bot_usage,
            'dashboard_overhead': dashboard_overhead,
            'capacity_analysis': max_bots,
            'recommendations': recommendations,
            'scaling_plan': scaling_plan,
            'current_processes': self.current_processes
        }
        
        return report

def main():
    """Funzione principale"""
    print("🔍 AurumBotX System Capacity Analyzer")
    print("=" * 50)
    
    analyzer = SystemCapacityAnalyzer()
    report = analyzer.generate_report()
    
    # Salva report
    with open('system_capacity_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Mostra risultati principali
    specs = report['system_specs']
    capacity = report['capacity_analysis']
    current = report['current_usage']
    
    print(f"🖥️  SPECIFICHE SISTEMA:")
    print(f"   CPU Cores: {specs['cpu_cores']} ({specs['cpu_physical']} fisici)")
    print(f"   RAM Totale: {specs['memory_total_gb']} GB")
    print(f"   RAM Disponibile: {specs['memory_available_gb']} GB")
    print(f"   Disk Libero: {specs['disk_free_gb']} GB")
    
    print(f"\\n🤖 CAPACITÀ BOT TRADING:")
    print(f"   Bot Attivi: {capacity['current_bots']}")
    print(f"   Massimo Teorico: {capacity['theoretical_max']} bot")
    print(f"   Massimo Pratico: {capacity['practical_max']} bot")
    print(f"   Slot Disponibili: {capacity['available_slots']} bot")
    
    print(f"\\n📊 UTILIZZO RISORSE:")
    print(f"   Memoria per Bot: {report['bot_resource_usage']['memory_mb_avg']} MB")
    print(f"   CPU per Bot: {report['bot_resource_usage']['cpu_percent_avg']}%")
    print(f"   Utilizzo Memoria: {current['memory_utilization_percent']}%")
    
    print(f"\\n🎯 RACCOMANDAZIONI:")
    for rec in report['recommendations']:
        priority_icon = "🚨" if rec['priority'] == 'high' else "⚠️" if rec['priority'] == 'medium' else "💡"
        print(f"   {priority_icon} {rec['message']}")
    
    print(f"\\n🚀 PIANO SCALING:")
    for phase in report['scaling_plan']['scaling_phases']:
        risk_icon = "🟢" if phase['risk'] == 'low' else "🟡" if phase['risk'] == 'medium' else "🔴"
        print(f"   {risk_icon} Fase {phase['phase']}: {phase['target_bots']} bot ({phase['description']})")
    
    print(f"\\n✅ Report salvato: system_capacity_report.json")
    
    return report

if __name__ == "__main__":
    main()

