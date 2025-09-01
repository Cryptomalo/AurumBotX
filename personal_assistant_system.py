#!/usr/bin/env python3
"""
AurumBotX Personal Assistant System
Sistema di assistenza personale per monitoraggio continuo
"""

import sqlite3
import json
import time
import os
from datetime import datetime, timedelta
import requests
import subprocess

class PersonalAssistant:
    """Assistente personale per AurumBotX"""
    
    def __init__(self):
        self.databases = {
            'mega_aggressive': 'mega_aggressive_trading.db',
            'ultra_aggressive': 'ultra_aggressive_trading.db',
            'mainnet_optimization': 'mainnet_optimization.db'
        }
        
        self.monitoring_active = True
        self.last_check = datetime.now()
        self.alerts = []
        
    def check_system_health(self):
        """Controlla salute generale del sistema"""
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'systems': {},
            'alerts': [],
            'recommendations': []
        }
        
        # Controlla ogni sistema
        for system_name, db_path in self.databases.items():
            system_health = self.check_database_health(system_name, db_path)
            health_report['systems'][system_name] = system_health
            
            # Genera alert se necessario
            if system_health['status'] == 'warning':
                health_report['alerts'].append(f"⚠️ {system_name}: {system_health['message']}")
            elif system_health['status'] == 'error':
                health_report['alerts'].append(f"🚨 {system_name}: {system_health['message']}")
        
        return health_report
    
    def check_database_health(self, system_name, db_path):
        """Controlla salute database specifico"""
        try:
            if not os.path.exists(db_path):
                return {
                    'status': 'error',
                    'message': 'Database non trovato',
                    'trades': 0,
                    'last_trade': None,
                    'profit': 0.0
                }
            
            conn = sqlite3.connect(db_path)
            
            # Determina nome tabella
            if 'mega' in system_name:
                table_name = 'mega_trades'
            elif 'ultra' in system_name:
                table_name = 'ultra_trades'
            else:
                table_name = 'optimized_trades'
            
            # Query informazioni
            cursor = conn.cursor()
            
            # Conta trade
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            trade_count = cursor.fetchone()[0]
            
            # Ultimo trade
            cursor.execute(f"SELECT timestamp, profit_loss FROM {table_name} ORDER BY timestamp DESC LIMIT 1")
            last_trade_data = cursor.fetchone()
            
            # Profitto totale
            cursor.execute(f"SELECT SUM(profit_loss) FROM {table_name}")
            total_profit = cursor.fetchone()[0] or 0.0
            
            conn.close()
            
            # Determina status
            if last_trade_data:
                last_trade_time = datetime.fromisoformat(last_trade_data[0])
                time_since_last = datetime.now() - last_trade_time
                
                if time_since_last > timedelta(hours=2):
                    status = 'warning'
                    message = f'Nessun trade da {time_since_last.total_seconds()/3600:.1f} ore'
                else:
                    status = 'healthy'
                    message = f'Ultimo trade: {time_since_last.total_seconds()/60:.0f} minuti fa'
            else:
                status = 'warning'
                message = 'Nessun trade registrato'
                last_trade_time = None
            
            return {
                'status': status,
                'message': message,
                'trades': trade_count,
                'last_trade': last_trade_time.isoformat() if last_trade_time else None,
                'profit': total_profit
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Errore database: {str(e)}',
                'trades': 0,
                'last_trade': None,
                'profit': 0.0
            }
    
    def check_performance_trends(self):
        """Analizza trend performance"""
        trends = {}
        
        for system_name, db_path in self.databases.items():
            try:
                if not os.path.exists(db_path):
                    continue
                
                conn = sqlite3.connect(db_path)
                
                # Determina nome tabella
                if 'mega' in system_name:
                    table_name = 'mega_trades'
                elif 'ultra' in system_name:
                    table_name = 'ultra_trades'
                else:
                    table_name = 'optimized_trades'
                
                # Ultimi 10 trade
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT profit_loss, timestamp 
                    FROM {table_name} 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                """)
                
                recent_trades = cursor.fetchall()
                conn.close()
                
                if recent_trades:
                    profits = [trade[0] for trade in recent_trades]
                    avg_profit = sum(profits) / len(profits)
                    win_rate = sum(1 for p in profits if p > 0) / len(profits) * 100
                    
                    # Trend analysis
                    if len(profits) >= 5:
                        recent_avg = sum(profits[:5]) / 5
                        older_avg = sum(profits[5:]) / len(profits[5:])
                        
                        if recent_avg > older_avg * 1.1:
                            trend = 'improving'
                        elif recent_avg < older_avg * 0.9:
                            trend = 'declining'
                        else:
                            trend = 'stable'
                    else:
                        trend = 'insufficient_data'
                    
                    trends[system_name] = {
                        'avg_profit': avg_profit,
                        'win_rate': win_rate,
                        'trend': trend,
                        'recent_trades': len(recent_trades)
                    }
                
            except Exception as e:
                trends[system_name] = {
                    'error': str(e)
                }
        
        return trends
    
    def generate_recommendations(self, health_report, trends):
        """Genera raccomandazioni basate su analisi"""
        recommendations = []
        
        # Analizza salute sistemi
        healthy_systems = sum(1 for s in health_report['systems'].values() if s['status'] == 'healthy')
        total_systems = len(health_report['systems'])
        
        if healthy_systems < total_systems:
            recommendations.append(f"🔧 {total_systems - healthy_systems} sistemi necessitano attenzione")
        
        # Analizza performance
        for system_name, trend_data in trends.items():
            if 'error' in trend_data:
                continue
                
            if trend_data['trend'] == 'declining':
                recommendations.append(f"📉 {system_name}: Performance in calo, considera ottimizzazione parametri")
            elif trend_data['trend'] == 'improving':
                recommendations.append(f"📈 {system_name}: Performance in miglioramento, mantieni configurazione")
            
            if trend_data['win_rate'] < 50:
                recommendations.append(f"⚠️ {system_name}: Win rate basso ({trend_data['win_rate']:.1f}%), rivedi strategia")
        
        # Raccomandazioni generali
        total_profit = sum(s.get('profit', 0) for s in health_report['systems'].values())
        if total_profit > 1000:
            recommendations.append("💰 Profitti elevati raggiunti, considera prelievo parziale")
        
        return recommendations
    
    def create_daily_report(self):
        """Crea report giornaliero"""
        health_report = self.check_system_health()
        trends = self.check_performance_trends()
        recommendations = self.generate_recommendations(health_report, trends)
        
        daily_report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat(),
            'health': health_report,
            'trends': trends,
            'recommendations': recommendations,
            'summary': {
                'total_systems': len(health_report['systems']),
                'healthy_systems': sum(1 for s in health_report['systems'].values() if s['status'] == 'healthy'),
                'total_trades': sum(s.get('trades', 0) for s in health_report['systems'].values()),
                'total_profit': sum(s.get('profit', 0) for s in health_report['systems'].values()),
                'alerts_count': len(health_report['alerts'])
            }
        }
        
        # Salva report
        report_filename = f"daily_report_{datetime.now().strftime('%Y%m%d')}.json"
        os.makedirs('reports/daily', exist_ok=True)
        
        with open(f'reports/daily/{report_filename}', 'w') as f:
            json.dump(daily_report, f, indent=2)
        
        return daily_report
    
    def check_deployment_status(self):
        """Controlla status deployment"""
        deployment_status = {
            'local_dashboards': self.check_local_dashboards(),
            'github_status': self.check_github_status(),
            'deployment_ready': True
        }
        
        return deployment_status
    
    def check_local_dashboards(self):
        """Controlla dashboard locali"""
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            streamlit_processes = [line for line in result.stdout.split('\n') if 'streamlit' in line]
            
            return {
                'active_dashboards': len(streamlit_processes),
                'processes': streamlit_processes[:5]  # Prime 5 per brevità
            }
        except:
            return {'active_dashboards': 0, 'processes': []}
    
    def check_github_status(self):
        """Controlla status GitHub"""
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd='.')
            
            has_changes = len(result.stdout.strip()) > 0
            
            return {
                'has_uncommitted_changes': has_changes,
                'ready_for_push': not has_changes
            }
        except:
            return {'has_uncommitted_changes': True, 'ready_for_push': False}
    
    def run_continuous_monitoring(self, interval_minutes=30):
        """Esegue monitoraggio continuo"""
        print(f"🤖 Assistente Personale AurumBotX avviato")
        print(f"⏰ Monitoraggio ogni {interval_minutes} minuti")
        
        while self.monitoring_active:
            try:
                # Crea report
                daily_report = self.create_daily_report()
                
                # Log status
                print(f"\n📊 Report {datetime.now().strftime('%H:%M:%S')}")
                print(f"🎯 Sistemi attivi: {daily_report['summary']['healthy_systems']}/{daily_report['summary']['total_systems']}")
                print(f"💰 Profitto totale: ${daily_report['summary']['total_profit']:.2f}")
                print(f"📈 Trade totali: {daily_report['summary']['total_trades']}")
                
                if daily_report['summary']['alerts_count'] > 0:
                    print(f"⚠️ Alert: {daily_report['summary']['alerts_count']}")
                
                if daily_report['recommendations']:
                    print("💡 Raccomandazioni:")
                    for rec in daily_report['recommendations'][:3]:
                        print(f"   {rec}")
                
                # Attendi prossimo check
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\n🛑 Monitoraggio fermato dall'utente")
                break
            except Exception as e:
                print(f"❌ Errore monitoraggio: {e}")
                time.sleep(60)  # Attendi 1 minuto prima di riprovare

def main():
    """Funzione principale"""
    assistant = PersonalAssistant()
    
    print("🚀 AurumBotX Personal Assistant System")
    print("=" * 50)
    
    # Report iniziale
    print("📊 Generazione report iniziale...")
    daily_report = assistant.create_daily_report()
    
    print(f"\n✅ SISTEMA STATUS:")
    print(f"🎯 Sistemi monitorati: {daily_report['summary']['total_systems']}")
    print(f"💚 Sistemi healthy: {daily_report['summary']['healthy_systems']}")
    print(f"💰 Profitto totale: ${daily_report['summary']['total_profit']:.2f}")
    print(f"📈 Trade totali: {daily_report['summary']['total_trades']}")
    
    if daily_report['recommendations']:
        print(f"\n💡 RACCOMANDAZIONI:")
        for rec in daily_report['recommendations']:
            print(f"   {rec}")
    
    # Controlla deployment
    deployment = assistant.check_deployment_status()
    print(f"\n🌐 DEPLOYMENT STATUS:")
    print(f"📊 Dashboard attive: {deployment['local_dashboards']['active_dashboards']}")
    print(f"📦 GitHub ready: {deployment['github_status']['ready_for_push']}")
    
    print(f"\n🤖 ASSISTENTE PERSONALE ATTIVO")
    print(f"📋 Report salvato: reports/daily/daily_report_{datetime.now().strftime('%Y%m%d')}.json")
    print(f"⏰ Monitoraggio continuo disponibile")
    
    # Opzione monitoraggio continuo
    choice = input("\n🔄 Avviare monitoraggio continuo? (y/n): ").lower()
    if choice == 'y':
        assistant.run_continuous_monitoring()

if __name__ == "__main__":
    main()

