#!/usr/bin/env python3
"""
AurumBotX Dashboard Sync Manager
Sincronizza tutte le dashboard con i dati ultra-aggressivi più recenti
"""

import os
import sys
import time
import sqlite3
import pandas as pd
import json
import subprocess
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dashboard_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DashboardSync')

class DashboardSyncManager:
    """Manager per sincronizzazione dashboard"""
    
    def __init__(self):
        self.logger = logging.getLogger('DashboardSyncManager')
        self.dashboard_ports = {
            'admin': 8501,
            'premium': 8502,
            'performance': 8503,
            'config': 8504,
            'mobile': 8505,
            'ultra_aggressive': 8506
        }
        
        # Database sources
        self.ultra_db = 'ultra_aggressive_trading.db'
        self.old_db = 'aggressive_trading.db'
        
    def update_dashboard_configs(self):
        """Aggiorna configurazioni dashboard per usare dati ultra-aggressivi"""
        try:
            self.logger.info("🔄 Aggiornamento configurazioni dashboard...")
            
            # Crea file di configurazione condiviso
            config = {
                'primary_database': self.ultra_db,
                'secondary_database': self.old_db,
                'last_update': datetime.now().isoformat(),
                'data_source': 'ultra_aggressive',
                'auto_refresh_seconds': 30,
                'show_comparison': True
            }
            
            with open('dashboard_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info("✅ Configurazione dashboard aggiornata")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Errore aggiornamento config: {e}")
            return False
    
    def get_latest_data_summary(self):
        """Ottieni riassunto dati più recenti"""
        try:
            summary = {
                'ultra_aggressive': {},
                'old_system': {},
                'comparison': {}
            }
            
            # Dati ultra-aggressivi
            if os.path.exists(self.ultra_db):
                conn = sqlite3.connect(self.ultra_db)
                ultra_stats = pd.read_sql_query("""
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(profit_loss) as total_pnl,
                        AVG(profit_loss) as avg_pnl,
                        MAX(balance_after) as current_balance,
                        MAX(timestamp) as last_trade,
                        COUNT(CASE WHEN profit_loss > 0 THEN 1 END) as winning_trades
                    FROM ultra_trades
                """, conn).iloc[0]
                conn.close()
                
                summary['ultra_aggressive'] = {
                    'total_trades': int(ultra_stats['total_trades']),
                    'total_pnl': float(ultra_stats['total_pnl']),
                    'avg_pnl': float(ultra_stats['avg_pnl']),
                    'current_balance': float(ultra_stats['current_balance']),
                    'last_trade': ultra_stats['last_trade'],
                    'win_rate': (ultra_stats['winning_trades'] / ultra_stats['total_trades'] * 100) if ultra_stats['total_trades'] > 0 else 0,
                    'roi': ((ultra_stats['current_balance'] - 1000) / 1000 * 100) if ultra_stats['current_balance'] else 0
                }
            
            # Dati sistema precedente
            if os.path.exists(self.old_db):
                conn = sqlite3.connect(self.old_db)
                old_stats = pd.read_sql_query("""
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(profit_loss) as total_pnl,
                        AVG(profit_loss) as avg_pnl,
                        MAX(balance_after) as current_balance,
                        COUNT(CASE WHEN profit_loss > 0 THEN 1 END) as winning_trades
                    FROM aggressive_trades
                """, conn).iloc[0]
                conn.close()
                
                summary['old_system'] = {
                    'total_trades': int(old_stats['total_trades']),
                    'total_pnl': float(old_stats['total_pnl']),
                    'avg_pnl': float(old_stats['avg_pnl']),
                    'current_balance': float(old_stats['current_balance']),
                    'win_rate': (old_stats['winning_trades'] / old_stats['total_trades'] * 100) if old_stats['total_trades'] > 0 else 0
                }
            
            # Confronto
            if summary['ultra_aggressive'] and summary['old_system']:
                ultra = summary['ultra_aggressive']
                old = summary['old_system']
                
                summary['comparison'] = {
                    'pnl_improvement': (ultra['avg_pnl'] / old['avg_pnl']) if old['avg_pnl'] > 0 else 0,
                    'efficiency_ratio': (ultra['total_pnl'] / ultra['total_trades']) / (old['total_pnl'] / old['total_trades']) if old['total_trades'] > 0 and ultra['total_trades'] > 0 else 0,
                    'win_rate_diff': ultra['win_rate'] - old['win_rate'],
                    'roi_ultra': ultra['roi']
                }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Errore recupero dati: {e}")
            return {}
    
    def check_dashboard_status(self):
        """Controlla stato di tutte le dashboard"""
        try:
            status = {}
            
            for name, port in self.dashboard_ports.items():
                try:
                    # Controlla processo
                    result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
                    is_running = f":{port} " in result.stdout
                    
                    status[name] = {
                        'port': port,
                        'running': is_running,
                        'url': f"http://localhost:{port}" if is_running else None
                    }
                    
                except Exception as e:
                    status[name] = {
                        'port': port,
                        'running': False,
                        'error': str(e)
                    }
            
            return status
            
        except Exception as e:
            self.logger.error(f"❌ Errore controllo dashboard: {e}")
            return {}
    
    def create_unified_access_page(self):
        """Crea pagina HTML unificata per accesso a tutte le dashboard"""
        try:
            data_summary = self.get_latest_data_summary()
            dashboard_status = self.check_dashboard_status()
            
            html_content = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔥 AurumBotX - Dashboard 24/7</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        .header h1 {{
            color: #ff4757;
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }}
        .header p {{
            color: #666;
            font-size: 1.2em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #ff4757 0%, #ff3838 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 20px rgba(255,71,87,0.3);
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .stat-label {{
            font-size: 1em;
            opacity: 0.9;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-top: 40px;
        }}
        .dashboard-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            transition: transform 0.3s ease;
            border: 2px solid transparent;
            position: relative;
        }}
        .dashboard-card:hover {{
            transform: translateY(-5px);
            border-color: #ff4757;
        }}
        .dashboard-card.featured {{
            background: linear-gradient(135deg, #ff4757 0%, #ff3838 100%);
            color: white;
            transform: scale(1.05);
        }}
        .dashboard-card.featured:hover {{
            transform: scale(1.08) translateY(-5px);
        }}
        .dashboard-card h3 {{
            margin-bottom: 15px;
            font-size: 1.4em;
        }}
        .dashboard-card p {{
            margin-bottom: 20px;
            opacity: 0.8;
        }}
        .dashboard-card a {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-weight: bold;
            transition: all 0.3s ease;
        }}
        .dashboard-card.featured a {{
            background: linear-gradient(135deg, #2ed573 0%, #17a2b8 100%);
        }}
        .dashboard-card a:hover {{
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        .status-indicator {{
            position: absolute;
            top: 15px;
            right: 15px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #2ed573;
        }}
        .status-indicator.offline {{
            background: #ff4757;
        }}
        .comparison {{
            background: #e8f4fd;
            border-left: 4px solid #2196F3;
            padding: 20px;
            margin: 30px 0;
            border-radius: 5px;
        }}
        .update-time {{
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 30px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
        .auto-refresh {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ff4757;
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 0.9em;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
    </style>
    <script>
        // Auto-refresh ogni 30 secondi
        setTimeout(function() {{
            location.reload();
        }}, 30000);
        
        // Countdown refresh
        let countdown = 30;
        setInterval(function() {{
            countdown--;
            if (countdown <= 0) countdown = 30;
            document.getElementById('countdown').textContent = countdown;
        }}, 1000);
    </script>
</head>
<body>
    <div class="auto-refresh">
        🔄 Auto-refresh: <span id="countdown">30</span>s
    </div>
    
    <div class="container">
        <div class="header">
            <h1>🔥 AurumBotX Dashboard 24/7</h1>
            <p>Sistema Ultra-Aggressivo - Monitoraggio Real-time</p>
        </div>
"""
            
            # Statistiche principali
            if data_summary.get('ultra_aggressive'):
                ultra = data_summary['ultra_aggressive']
                html_content += f"""
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">${ultra['current_balance']:.2f}</div>
                <div class="stat-label">💰 Balance Corrente</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{ultra['roi']:.2f}%</div>
                <div class="stat-label">📈 ROI</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${ultra['total_pnl']:.2f}</div>
                <div class="stat-label">💸 Profitto Totale</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{ultra['total_trades']}</div>
                <div class="stat-label">🎯 Trade Totali</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{ultra['win_rate']:.1f}%</div>
                <div class="stat-label">✅ Win Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${ultra['avg_pnl']:.2f}</div>
                <div class="stat-label">📊 Avg P&L</div>
            </div>
        </div>
"""
            
            # Confronto sistemi
            if data_summary.get('comparison'):
                comp = data_summary['comparison']
                html_content += f"""
        <div class="comparison">
            <h3>⚔️ Confronto con Sistema Precedente</h3>
            <p><strong>🚀 Miglioramento Profitto per Trade:</strong> {comp['pnl_improvement']:.1f}x superiore</p>
            <p><strong>📈 Efficienza:</strong> {comp['efficiency_ratio']:.1f}x più efficiente</p>
            <p><strong>✅ Win Rate:</strong> {comp['win_rate_diff']:+.1f}% di differenza</p>
            <p><strong>💰 ROI Ultra-Aggressivo:</strong> {comp['roi_ultra']:.2f}%</p>
        </div>
"""
            
            # Dashboard links
            html_content += """
        <div class="dashboard-grid">
"""
            
            # Dashboard ultra-aggressiva (featured)
            ultra_status = dashboard_status.get('ultra_aggressive', {})
            ultra_running = ultra_status.get('running', False)
            
            html_content += f"""
            <div class="dashboard-card featured">
                <div class="status-indicator {'offline' if not ultra_running else ''}"></div>
                <h3>🔥 Ultra-Aggressive Dashboard</h3>
                <p>Dashboard dedicata al sistema ultra-aggressivo con dati real-time</p>
                <a href="https://8506-idj9fj7n1r57vl3chzzan-09c1c4c4.manusvm.computer" target="_blank">Accedi Dashboard</a>
            </div>
"""
            
            # Altre dashboard
            dashboard_info = {
                'admin': {
                    'title': '🔧 Admin Dashboard', 
                    'desc': 'Controllo completo del sistema',
                    'url': 'https://8501-idj9fj7n1r57vl3chzzan-09c1c4c4.manusvm.computer'
                },
                'performance': {
                    'title': '📈 Performance Dashboard', 
                    'desc': 'Monitoraggio performance e metriche',
                    'url': 'https://8503-idj9fj7n1r57vl3chzzan-09c1c4c4.manusvm.computer'
                },
                'mobile': {
                    'title': '📱 Mobile Dashboard', 
                    'desc': 'Versione ottimizzata per smartphone',
                    'url': 'https://8505-idj9fj7n1r57vl3chzzan-09c1c4c4.manusvm.computer'
                },
                'premium': {
                    'title': '💎 Premium Dashboard', 
                    'desc': 'Interfaccia utenti premium',
                    'url': 'https://8502-idj9fj7n1r57vl3chzzan-09c1c4c4.manusvm.computer'
                },
                'config': {
                    'title': '⚙️ Config Dashboard', 
                    'desc': 'Configurazione avanzata sistema',
                    'url': 'https://8504-idj9fj7n1r57vl3chzzan-09c1c4c4.manusvm.computer'
                }
            }
            
            for name, info in dashboard_info.items():
                status = dashboard_status.get(name, {})
                running = status.get('running', False)
                
                html_content += f"""
            <div class="dashboard-card">
                <div class="status-indicator {'offline' if not running else ''}"></div>
                <h3>{info['title']}</h3>
                <p>{info['desc']}</p>
                <a href="{info['url']}" target="_blank">Accedi Dashboard</a>
            </div>
"""
            
            html_content += f"""
        </div>
        
        <div class="update-time">
            <strong>📊 Ultimo Aggiornamento:</strong> {datetime.now().strftime('%d/%m/%Y alle %H:%M:%S')}<br>
            <strong>🔄 Prossimo Refresh:</strong> Automatico ogni 30 secondi<br>
            <strong>📡 Stato Sistema:</strong> {'🟢 ATTIVO' if data_summary.get('ultra_aggressive') else '🔴 OFFLINE'}
        </div>
    </div>
</body>
</html>
"""
            
            # Salva pagina
            with open('aurumbotx_dashboard_24_7.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info("✅ Pagina unificata creata: aurumbotx_dashboard_24_7.html")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Errore creazione pagina: {e}")
            return False
    
    def run_continuous_sync(self):
        """Esegue sincronizzazione continua"""
        try:
            self.logger.info("🔄 Avvio sincronizzazione continua dashboard...")
            
            while True:
                # Aggiorna configurazioni
                self.update_dashboard_configs()
                
                # Crea pagina di accesso aggiornata
                self.create_unified_access_page()
                
                # Log status
                data_summary = self.get_latest_data_summary()
                if data_summary.get('ultra_aggressive'):
                    ultra = data_summary['ultra_aggressive']
                    self.logger.info(f"📊 Ultra-Aggressive: {ultra['total_trades']} trades, "
                                   f"${ultra['total_pnl']:.2f} profit, {ultra['win_rate']:.1f}% win rate")
                
                # Aspetta 30 secondi
                time.sleep(30)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Sincronizzazione fermata dall'utente")
        except Exception as e:
            self.logger.error(f"❌ Errore sincronizzazione: {e}")

def main():
    """Funzione principale"""
    print("🔄 AurumBotX Dashboard Sync Manager")
    print("=" * 50)
    print("🎯 OBIETTIVO: Sincronizzazione dashboard 24/7")
    print("📊 DATI: Sistema ultra-aggressivo real-time")
    print("🔗 OUTPUT: Link sempre attivi e aggiornati")
    print("=" * 50)
    
    # Setup
    os.makedirs('logs', exist_ok=True)
    
    # Inizializza manager
    manager = DashboardSyncManager()
    
    # Crea pagina iniziale
    print("🔄 Creazione pagina di accesso...")
    success = manager.create_unified_access_page()
    
    if success:
        print("✅ Pagina di accesso creata: aurumbotx_dashboard_24_7.html")
        print("🌐 Aprire il file HTML nel browser per accedere alle dashboard")
        
        # Avvia sincronizzazione continua
        print("🔄 Avvio sincronizzazione continua...")
        manager.run_continuous_sync()
    else:
        print("❌ Errore creazione pagina di accesso")

if __name__ == "__main__":
    main()

