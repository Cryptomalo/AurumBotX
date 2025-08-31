#!/usr/bin/env python3
"""
AurumBotX Updated Admin Dashboard
Dashboard amministratore aggiornata con dati reali
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import json
import os
import subprocess

# Configurazione pagina
st.set_page_config(
    page_title="AurumBotX - Admin Dashboard",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizzato
st.markdown("""
<style>
    .admin-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    
    .control-panel {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    
    .status-active {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 0.5rem;
        border-radius: 5px;
        color: white;
        text-align: center;
        margin: 0.2rem 0;
    }
    
    .status-inactive {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        padding: 0.5rem;
        border-radius: 5px;
        color: white;
        text-align: center;
        margin: 0.2rem 0;
    }
</style>
""", unsafe_allow_html=True)

class AdminDashboard:
    """Dashboard amministratore con controlli sistema"""
    
    def __init__(self):
        self.processes = {
            'mega_aggressive': 'mega_aggressive_trading.py',
            'ultra_aggressive': 'ultra_aggressive_trading.py',
            'mainnet_optimization': 'mainnet_optimization_strategies.py'
        }
        
        self.databases = {
            'mega_aggressive': 'mega_aggressive_trading.db',
            'ultra_aggressive': 'ultra_aggressive_trading.db',
            'mainnet_optimization': 'mainnet_optimization.db'
        }
    
    def check_process_status(self, process_name):
        """Controlla se un processo è attivo"""
        try:
            result = subprocess.run(
                ['pgrep', '-f', process_name],
                capture_output=True,
                text=True
            )
            return len(result.stdout.strip()) > 0
        except:
            return False
    
    def get_system_stats(self):
        """Ottieni statistiche sistema"""
        stats = {}
        
        for system, db_name in self.databases.items():
            try:
                if not os.path.exists(db_name):
                    stats[system] = {
                        'trades': 0,
                        'profit': 0.0,
                        'balance': 1000.0,
                        'roi': 0.0,
                        'win_rate': 0.0,
                        'active': False
                    }
                    continue
                
                conn = sqlite3.connect(db_name)
                
                # Determina nome tabella
                if system == 'mega_aggressive':
                    table_name = 'mega_trades'
                elif system == 'ultra_aggressive':
                    table_name = 'ultra_trades'
                else:
                    table_name = 'optimized_trades'
                
                # Query statistiche
                query = f"""
                    SELECT 
                        COUNT(*) as trades,
                        COALESCE(SUM(profit_loss), 0) as total_profit,
                        COALESCE(MAX(balance_after), 1000) as current_balance,
                        COALESCE(AVG(profit_loss), 0) as avg_profit,
                        COALESCE(SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 0) as win_rate
                    FROM {table_name}
                """
                
                result = conn.execute(query).fetchone()
                conn.close()
                
                if result:
                    trades, total_profit, current_balance, avg_profit, win_rate = result
                    roi = ((current_balance - 1000) / 1000 * 100) if current_balance > 0 else 0
                    
                    stats[system] = {
                        'trades': trades or 0,
                        'profit': total_profit or 0.0,
                        'balance': current_balance or 1000.0,
                        'roi': roi,
                        'win_rate': win_rate or 0.0,
                        'active': self.check_process_status(self.processes[system])
                    }
                else:
                    stats[system] = {
                        'trades': 0,
                        'profit': 0.0,
                        'balance': 1000.0,
                        'roi': 0.0,
                        'win_rate': 0.0,
                        'active': self.check_process_status(self.processes[system])
                    }
                    
            except Exception as e:
                st.error(f"Errore lettura stats {system}: {e}")
                stats[system] = {
                    'trades': 0,
                    'profit': 0.0,
                    'balance': 1000.0,
                    'roi': 0.0,
                    'win_rate': 0.0,
                    'active': False
                }
        
        return stats
    
    def render_header(self):
        """Render header admin"""
        st.markdown("""
        <div class="admin-header">
            🔧 AURUMBOTX - ADMIN DASHBOARD
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**👤 Admin Panel** | **📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}**")
    
    def render_system_controls(self, stats):
        """Render controlli sistema"""
        st.header("🎛️ Controlli Sistema")
        
        col1, col2, col3 = st.columns(3)
        
        systems = [
            ('mega_aggressive', 'Mega Aggressive', col1),
            ('ultra_aggressive', 'Ultra Aggressive', col2),
            ('mainnet_optimization', 'Mainnet Optimization', col3)
        ]
        
        for system_key, system_name, col in systems:
            with col:
                system_stats = stats[system_key]
                is_active = system_stats['active']
                
                # Status
                status_class = "status-active" if is_active else "status-inactive"
                status_text = "🟢 ATTIVO" if is_active else "🔴 INATTIVO"
                
                st.markdown(f"""
                <div class="control-panel">
                    <h4>{system_name}</h4>
                    <div class="{status_class}">
                        {status_text}
                    </div>
                    <p><strong>Trade:</strong> {system_stats['trades']}</p>
                    <p><strong>Profitto:</strong> ${system_stats['profit']:.2f}</p>
                    <p><strong>ROI:</strong> {system_stats['roi']:.1f}%</p>
                    <p><strong>Balance:</strong> ${system_stats['balance']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Controlli
                if is_active:
                    if st.button(f"🛑 Stop {system_name}", key=f"stop_{system_key}"):
                        self.stop_system(system_key)
                        st.success(f"{system_name} fermato!")
                        time.sleep(1)
                        st.experimental_rerun()
                else:
                    if st.button(f"▶️ Start {system_name}", key=f"start_{system_key}"):
                        self.start_system(system_key)
                        st.success(f"{system_name} avviato!")
                        time.sleep(1)
                        st.experimental_rerun()
                
                if st.button(f"🔄 Restart {system_name}", key=f"restart_{system_key}"):
                    self.restart_system(system_key)
                    st.success(f"{system_name} riavviato!")
                    time.sleep(1)
                    st.experimental_rerun()
    
    def start_system(self, system_key):
        """Avvia sistema"""
        try:
            process_file = self.processes[system_key]
            subprocess.Popen([
                'nohup', 'python3', process_file
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            st.error(f"Errore avvio {system_key}: {e}")
            return False
    
    def stop_system(self, system_key):
        """Ferma sistema"""
        try:
            process_file = self.processes[system_key]
            subprocess.run(['pkill', '-f', process_file])
            return True
        except Exception as e:
            st.error(f"Errore stop {system_key}: {e}")
            return False
    
    def restart_system(self, system_key):
        """Riavvia sistema"""
        self.stop_system(system_key)
        time.sleep(2)
        return self.start_system(system_key)
    
    def render_performance_overview(self, stats):
        """Render overview performance"""
        st.header("📊 Performance Overview")
        
        # Calcola totali
        total_trades = sum(s['trades'] for s in stats.values())
        total_profit = sum(s['profit'] for s in stats.values())
        total_balance = sum(s['balance'] for s in stats.values())
        avg_roi = sum(s['roi'] for s in stats.values()) / len(stats) if stats else 0
        
        # Metriche principali
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("🎯 Trade Totali", f"{total_trades}")
        
        with col2:
            st.metric("💰 Profitto Totale", f"${total_profit:.2f}")
        
        with col3:
            st.metric("💎 Balance Totale", f"${total_balance:.2f}")
        
        with col4:
            st.metric("📈 ROI Medio", f"{avg_roi:.1f}%")
        
        with col5:
            active_systems = sum(1 for s in stats.values() if s['active'])
            st.metric("🤖 Sistemi Attivi", f"{active_systems}/3")
        
        # Grafico comparativo
        st.subheader("📊 Confronto Sistemi")
        
        systems_data = []
        for system_key, system_stats in stats.items():
            systems_data.append({
                'Sistema': system_key.replace('_', ' ').title(),
                'Trade': system_stats['trades'],
                'Profitto': system_stats['profit'],
                'ROI': system_stats['roi'],
                'Win Rate': system_stats['win_rate']
            })
        
        if systems_data:
            df = pd.DataFrame(systems_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Grafico profitti
                fig_profit = px.bar(
                    df, 
                    x='Sistema', 
                    y='Profitto',
                    title="Profitto per Sistema",
                    color='Profitto',
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig_profit, use_container_width=True)
            
            with col2:
                # Grafico ROI
                fig_roi = px.bar(
                    df, 
                    x='Sistema', 
                    y='ROI',
                    title="ROI per Sistema (%)",
                    color='ROI',
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig_roi, use_container_width=True)
    
    def render_system_logs(self):
        """Render logs sistema"""
        st.header("📋 System Logs")
        
        log_files = {
            'Mega Aggressive': 'logs/mega_aggressive.log',
            'Ultra Aggressive': 'logs/ultra_aggressive.log',
            'Mainnet Optimization': 'logs/mainnet_optimization.log',
            'Unified Dashboard': 'logs/unified_dashboard.log'
        }
        
        selected_log = st.selectbox("Seleziona log", list(log_files.keys()))
        
        log_file = log_files[selected_log]
        
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    # Mostra ultime 50 righe
                    recent_lines = lines[-50:] if len(lines) > 50 else lines
                    log_content = ''.join(recent_lines)
                
                st.text_area(
                    f"📄 {selected_log} (ultime 50 righe)",
                    log_content,
                    height=300
                )
                
                if st.button("🔄 Refresh Log"):
                    st.experimental_rerun()
                    
            except Exception as e:
                st.error(f"Errore lettura log: {e}")
        else:
            st.warning(f"Log file {log_file} non trovato")
    
    def render_emergency_controls(self):
        """Render controlli emergenza"""
        st.header("🚨 Controlli Emergenza")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🛑 STOP ALL SYSTEMS", type="primary"):
                for system_key in self.processes.keys():
                    self.stop_system(system_key)
                st.error("🛑 TUTTI I SISTEMI FERMATI!")
                time.sleep(2)
                st.experimental_rerun()
        
        with col2:
            if st.button("🔄 RESTART ALL SYSTEMS"):
                for system_key in self.processes.keys():
                    self.restart_system(system_key)
                st.success("🔄 TUTTI I SISTEMI RIAVVIATI!")
                time.sleep(2)
                st.experimental_rerun()
        
        with col3:
            if st.button("📊 REFRESH STATUS"):
                st.experimental_rerun()

def main():
    """Funzione principale"""
    
    # Inizializza dashboard
    dashboard = AdminDashboard()
    
    # Auto-refresh
    if 'admin_last_refresh' not in st.session_state:
        st.session_state.admin_last_refresh = time.time()
    
    # Sidebar
    st.sidebar.header("🔧 Admin Controls")
    
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (15s)", value=True)
    
    if auto_refresh:
        elapsed = time.time() - st.session_state.admin_last_refresh
        remaining = max(0, 15 - elapsed)
        
        st.sidebar.write(f"⏰ Refresh: {remaining:.0f}s")
        
        if elapsed >= 15:
            st.session_state.admin_last_refresh = time.time()
            st.experimental_rerun()
    
    if st.sidebar.button("🔄 Manual Refresh"):
        st.session_state.admin_last_refresh = time.time()
        st.experimental_rerun()
    
    # Carica stats
    with st.spinner("📊 Caricamento status sistema..."):
        stats = dashboard.get_system_stats()
    
    # Render dashboard
    dashboard.render_header()
    dashboard.render_system_controls(stats)
    dashboard.render_performance_overview(stats)
    dashboard.render_system_logs()
    dashboard.render_emergency_controls()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        🔧 AurumBotX Admin Dashboard - Controllo Completo Sistema<br>
        ⚠️ Utilizzare con cautela - Controlli amministratore
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

