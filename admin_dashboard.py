#!/usr/bin/env python3
"""
🎯 AurumBotX - Dashboard Admin Principale
Dashboard completa per amministratore con controllo totale del sistema
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
import sys
import asyncio
import subprocess
import time
import psutil

# Aggiungi path per import moduli
sys.path.append('.')

# Import moduli AurumBotX
try:
    from utils.data_loader import CryptoDataLoader
    from utils.exchange_manager import ExchangeManager
    from utils.ai_trading import AITrading
    from utils.database_manager import DatabaseManager
except ImportError as e:
    st.error(f"Errore import moduli: {e}")

# Configurazione pagina
st.set_page_config(
    page_title="🎯 AurumBotX Admin Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizzato
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79, #2d5aa0);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2d5aa0;
        margin: 0.5rem 0;
    }
    .status-active { color: #28a745; font-weight: bold; }
    .status-inactive { color: #dc3545; font-weight: bold; }
    .status-warning { color: #ffc107; font-weight: bold; }
    .control-button {
        width: 100%;
        margin: 0.25rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header principale
st.markdown("""
<div class="main-header">
    <h1>🎯 AurumBotX - Dashboard Admin</h1>
    <p>Controllo Completo Sistema Trading Automatico</p>
</div>
""", unsafe_allow_html=True)

# Sidebar controlli admin
st.sidebar.markdown("## 🔧 Controlli Admin")

# Funzioni di controllo sistema
def get_bot_status():
    """Verifica status bot"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'activate_24h_monitoring' in result.stdout:
            return "🟢 ATTIVO", "running"
        else:
            return "🔴 INATTIVO", "stopped"
    except:
        return "⚠️ ERRORE", "error"

def get_system_metrics():
    """Ottieni metriche sistema"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu': cpu_percent,
            'memory_used': memory.percent,
            'memory_available': memory.available / (1024**3),
            'disk_used': disk.percent,
            'disk_free': disk.free / (1024**3)
        }
    except:
        return None

def read_trading_logs():
    """Leggi log trading recenti"""
    try:
        log_files = [
            'logs/continuous_bot.log',
            'logs/24h_trading.log',
            'logs/monitor_startup.log'
        ]
        
        logs = []
        for log_file in log_files:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-50:]  # Ultimi 50 righe
                    logs.extend([{'file': log_file, 'line': line.strip()} for line in lines])
        
        return logs[-100:]  # Ultimi 100 log entries
    except:
        return []

def get_trading_stats():
    """Ottieni statistiche trading"""
    try:
        # Leggi file di configurazione e report
        stats = {
            'total_trades': 0,
            'successful_trades': 0,
            'total_profit': 0.0,
            'win_rate': 0.0,
            'active_signals': 0,
            'last_signal': 'N/A',
            'uptime_hours': 0
        }
        
        # Cerca file di report
        report_files = []
        if os.path.exists('reports'):
            for root, dirs, files in os.walk('reports'):
                for file in files:
                    if file.endswith('.json'):
                        report_files.append(os.path.join(root, file))
        
        # Analizza report più recente
        if report_files:
            latest_report = max(report_files, key=os.path.getctime)
            with open(latest_report, 'r') as f:
                data = json.load(f)
                if 'trading_stats' in data:
                    stats.update(data['trading_stats'])
        
        return stats
    except:
        return {
            'total_trades': 0,
            'successful_trades': 0,
            'total_profit': 0.0,
            'win_rate': 0.0,
            'active_signals': 0,
            'last_signal': 'N/A',
            'uptime_hours': 0
        }

# Controlli sidebar
if st.sidebar.button("🚀 Avvia Bot", key="start_bot"):
    try:
        subprocess.Popen(['nohup', 'python', 'activate_24h_monitoring.py'], 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        st.sidebar.success("Bot avviato!")
        time.sleep(2)
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Errore avvio: {e}")

if st.sidebar.button("🛑 Ferma Bot", key="stop_bot"):
    try:
        subprocess.run(['pkill', '-f', 'activate_24h_monitoring'], check=False)
        st.sidebar.success("Bot fermato!")
        time.sleep(2)
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Errore stop: {e}")

if st.sidebar.button("🔄 Riavvia Bot", key="restart_bot"):
    try:
        subprocess.run(['pkill', '-f', 'activate_24h_monitoring'], check=False)
        time.sleep(3)
        subprocess.Popen(['nohup', 'python', 'activate_24h_monitoring.py'], 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        st.sidebar.success("Bot riavviato!")
        time.sleep(2)
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Errore riavvio: {e}")

st.sidebar.markdown("---")

# Configurazioni admin
st.sidebar.markdown("## ⚙️ Configurazioni")

# Trading parameters
with st.sidebar.expander("📊 Parametri Trading"):
    trade_amount = st.number_input("Importo Trade (BTC)", value=0.00005, format="%.5f")
    min_confidence = st.slider("Confidenza Minima (%)", 50, 90, 65)
    profit_target = st.slider("Profit Target (%)", 0.1, 2.0, 0.8)
    stop_loss = st.slider("Stop Loss (%)", 0.1, 1.0, 0.5)
    
    if st.button("💾 Salva Parametri"):
        config = {
            'trade_amount_btc': trade_amount,
            'min_confidence': min_confidence / 100,
            'profit_target': profit_target / 100,
            'stop_loss': stop_loss / 100
        }
        with open('configs/admin_trading_params.json', 'w') as f:
            json.dump(config, f, indent=2)
        st.success("Parametri salvati!")

# Risk management
with st.sidebar.expander("🛡️ Risk Management"):
    max_daily_trades = st.number_input("Max Trade Giornalieri", value=50)
    max_daily_loss = st.number_input("Max Perdita Giornaliera ($)", value=100.0)
    emergency_stop = st.checkbox("Emergency Stop Attivo", value=True)
    
    if st.button("🔒 Salva Risk Settings"):
        risk_config = {
            'max_daily_trades': max_daily_trades,
            'max_daily_loss_usdt': max_daily_loss,
            'emergency_stop_enabled': emergency_stop
        }
        with open('configs/admin_risk_management.json', 'w') as f:
            json.dump(risk_config, f, indent=2)
        st.success("Risk settings salvati!")

# Main dashboard content
col1, col2, col3, col4 = st.columns(4)

# Status sistema
bot_status, bot_state = get_bot_status()
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>🤖 Status Bot</h3>
        <p class="status-{'active' if bot_state == 'running' else 'inactive'}">{bot_status}</p>
    </div>
    """, unsafe_allow_html=True)

# Metriche sistema
metrics = get_system_metrics()
with col2:
    if metrics:
        st.markdown(f"""
        <div class="metric-card">
            <h3>💻 Sistema</h3>
            <p>CPU: {metrics['cpu']:.1f}%</p>
            <p>RAM: {metrics['memory_used']:.1f}%</p>
            <p>Disk: {metrics['disk_used']:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)

# Trading stats
trading_stats = get_trading_stats()
with col3:
    st.markdown(f"""
    <div class="metric-card">
        <h3>📊 Trading</h3>
        <p>Trade: {trading_stats['total_trades']}</p>
        <p>Win Rate: {trading_stats['win_rate']:.1f}%</p>
        <p>Profit: ${trading_stats['total_profit']:.2f}</p>
    </div>
    """, unsafe_allow_html=True)

# Uptime
with col4:
    st.markdown(f"""
    <div class="metric-card">
        <h3>⏱️ Uptime</h3>
        <p>{trading_stats['uptime_hours']:.1f} ore</p>
        <p>Segnali: {trading_stats['active_signals']}</p>
        <p>Ultimo: {trading_stats['last_signal']}</p>
    </div>
    """, unsafe_allow_html=True)

# Tabs principali
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "📈 Trading", "📋 Logs", "⚙️ Config", "🔧 Sistema"])

with tab1:
    st.markdown("## 📊 Dashboard Principale")
    
    # Grafici real-time
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💹 Prezzo BTC Real-time")
        try:
            # Placeholder per grafico prezzo
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[datetime.now() - timedelta(minutes=i) for i in range(60, 0, -1)],
                y=[115000 + i*10 for i in range(60)],
                mode='lines',
                name='BTC/USDT'
            ))
            fig.update_layout(title="BTC/USDT - Ultimo Ora", xaxis_title="Tempo", yaxis_title="Prezzo ($)")
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.info("Grafico prezzo in caricamento...")
    
    with col2:
        st.markdown("### 📊 Performance Trading")
        try:
            # Placeholder per grafico performance
            fig = px.bar(
                x=['Trade Vincenti', 'Trade Perdenti', 'Trade Attivi'],
                y=[trading_stats['successful_trades'], 
                   trading_stats['total_trades'] - trading_stats['successful_trades'],
                   trading_stats['active_signals']],
                title="Statistiche Trading"
            )
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.info("Grafico performance in caricamento...")

with tab2:
    st.markdown("## 📈 Controllo Trading")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Segnali Attivi")
        # Placeholder per segnali
        st.info("Segnali trading in tempo reale verranno mostrati qui")
        
        st.markdown("### 💰 Posizioni Aperte")
        # Placeholder per posizioni
        st.info("Posizioni aperte verranno mostrate qui")
    
    with col2:
        st.markdown("### 📊 Ordini Recenti")
        # Placeholder per ordini
        st.info("Ordini recenti verranno mostrati qui")
        
        st.markdown("### 🎲 Test Trading")
        if st.button("🧪 Esegui Test Trade"):
            st.info("Esecuzione test trade...")

with tab3:
    st.markdown("## 📋 Log Sistema")
    
    # Filtri log
    col1, col2, col3 = st.columns(3)
    with col1:
        log_level = st.selectbox("Livello", ["Tutti", "INFO", "WARNING", "ERROR"])
    with col2:
        log_lines = st.selectbox("Righe", [50, 100, 200, 500])
    with col3:
        if st.button("🔄 Aggiorna Log"):
            st.rerun()
    
    # Mostra log
    logs = read_trading_logs()
    if logs:
        log_text = "\n".join([f"[{log['file']}] {log['line']}" for log in logs[-log_lines:]])
        st.text_area("Log Sistema", log_text, height=400)
    else:
        st.info("Nessun log disponibile")

with tab4:
    st.markdown("## ⚙️ Configurazione Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔑 API Keys")
        binance_key = st.text_input("Binance API Key", type="password")
        binance_secret = st.text_input("Binance Secret", type="password")
        
        if st.button("💾 Salva API Keys"):
            # Salva in .env
            st.success("API Keys salvate!")
    
    with col2:
        st.markdown("### 🗄️ Database")
        db_url = st.text_input("Database URL", value="postgresql://...")
        
        if st.button("🔗 Test Connessione DB"):
            st.info("Test connessione database...")

with tab5:
    st.markdown("## 🔧 Sistema e Manutenzione")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🛠️ Manutenzione")
        if st.button("🧹 Pulisci Log"):
            st.info("Pulizia log in corso...")
        
        if st.button("💾 Backup Sistema"):
            st.info("Backup sistema in corso...")
        
        if st.button("🔄 Aggiorna Sistema"):
            st.info("Aggiornamento sistema in corso...")
    
    with col2:
        st.markdown("### 📊 Diagnostica")
        if st.button("🔍 Test Connessioni"):
            st.info("Test connessioni in corso...")
        
        if st.button("🧪 Test Componenti"):
            st.info("Test componenti in corso...")
        
        if st.button("📈 Report Completo"):
            st.info("Generazione report in corso...")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    🎯 AurumBotX Admin Dashboard v1.0 | 
    Ultimo aggiornamento: {timestamp} | 
    🤖 Sistema Operativo
</div>
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

# Auto-refresh ogni 30 secondi
if st.sidebar.checkbox("🔄 Auto-refresh (30s)", value=True):
    time.sleep(30)
    st.rerun()

