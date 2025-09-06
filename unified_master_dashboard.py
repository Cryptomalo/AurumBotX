#!/usr/bin/env python3
"""
AurumBotX - Dashboard Master Unificata
Sistema completo di controllo e monitoraggio con avvio bot integrato
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import subprocess
import psutil
import os
import json
import time
import threading
from pathlib import Path

# Configurazione pagina
st.set_page_config(
    page_title="🤖 AurumBotX Master Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizzato
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1a1a2e, #16213e, #0f3460);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .metric-card {
        background: linear-gradient(135deg, #16213e, #0f3460);
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e94560;
        margin: 0.5rem 0;
    }
    .bot-status-active {
        color: #00ff00;
        font-weight: bold;
    }
    .bot-status-inactive {
        color: #ff4444;
        font-weight: bold;
    }
    .control-button {
        width: 100%;
        margin: 0.2rem 0;
    }
    .success-metric {
        color: #00ff88;
        font-size: 1.5rem;
        font-weight: bold;
    }
    .warning-metric {
        color: #ffaa00;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .danger-metric {
        color: #ff4444;
        font-size: 1.2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class AurumBotXMaster:
    def __init__(self):
        self.base_dir = Path("/home/ubuntu/AurumBotX")
        self.databases = {
            "mega_aggressive": self.base_dir / "mega_aggressive_trading.db",
            "ultra_aggressive": self.base_dir / "ultra_aggressive_trading.db",
            "mainnet_250": self.base_dir / "mainnet_250_euro.db"
        }
        self.bot_scripts = {
            "mega_aggressive": "mega_aggressive_trading.py",
            "ultra_aggressive": "ultra_aggressive_trading.py", 
            "mainnet_250": "mainnet_250_euro_strategy.py"
        }
        
    def get_bot_status(self):
        """Verifica status di tutti i bot"""
        status = {}
        for bot_name in self.bot_scripts.keys():
            status[bot_name] = self.is_bot_running(bot_name)
        return status
    
    def is_bot_running(self, bot_name):
        """Verifica se un bot specifico è in esecuzione"""
        script_name = self.bot_scripts[bot_name]
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and any(script_name in cmd for cmd in proc.info['cmdline']):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def start_bot(self, bot_name):
        """Avvia un bot specifico"""
        if self.is_bot_running(bot_name):
            return False, f"Bot {bot_name} già in esecuzione"
        
        script_path = self.base_dir / self.bot_scripts[bot_name]
        if not script_path.exists():
            return False, f"Script {script_path} non trovato"
        
        try:
            # Avvia bot in background
            subprocess.Popen([
                "python3", str(script_path)
            ], cwd=str(self.base_dir), 
               stdout=subprocess.DEVNULL, 
               stderr=subprocess.DEVNULL)
            
            time.sleep(2)  # Attesa avvio
            
            if self.is_bot_running(bot_name):
                return True, f"Bot {bot_name} avviato con successo"
            else:
                return False, f"Errore avvio bot {bot_name}"
                
        except Exception as e:
            return False, f"Errore: {str(e)}"
    
    def stop_bot(self, bot_name):
        """Ferma un bot specifico"""
        script_name = self.bot_scripts[bot_name]
        killed = False
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and any(script_name in cmd for cmd in proc.info['cmdline']):
                    proc.terminate()
                    killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if killed:
            time.sleep(1)
            return True, f"Bot {bot_name} fermato"
        else:
            return False, f"Bot {bot_name} non trovato"
    
    def get_trading_data(self, bot_name):
        """Recupera dati trading da database"""
        db_path = self.databases.get(bot_name)
        if not db_path or not db_path.exists():
            return None
        
        try:
            conn = sqlite3.connect(str(db_path))
            
            # Determina nome tabella
            if bot_name == "mega_aggressive":
                table_name = "mega_trades"
            elif bot_name == "ultra_aggressive":
                table_name = "ultra_trades"
            else:
                table_name = "trades"
            
            # Query dati
            query = f"""
            SELECT 
                COUNT(*) as total_trades,
                COALESCE(SUM(profit_loss), 0) as total_profit,
                COALESCE(AVG(profit_loss), 0) as avg_profit,
                COALESCE(MAX(profit_loss), 0) as best_trade,
                COALESCE(MIN(profit_loss), 0) as worst_trade,
                COUNT(CASE WHEN profit_loss > 0 THEN 1 END) as winning_trades,
                COALESCE(MAX(balance_after), 0) as max_balance,
                MIN(timestamp) as first_trade,
                MAX(timestamp) as last_trade
            FROM {table_name}
            """
            
            result = pd.read_sql_query(query, conn)
            conn.close()
            
            if len(result) > 0:
                data = result.iloc[0].to_dict()
                if data['total_trades'] > 0:
                    data['win_rate'] = (data['winning_trades'] / data['total_trades']) * 100
                else:
                    data['win_rate'] = 0
                return data
            
        except Exception as e:
            st.error(f"Errore lettura database {bot_name}: {str(e)}")
        
        return None
    
    def get_recent_trades(self, bot_name, limit=10):
        """Recupera trade recenti"""
        db_path = self.databases.get(bot_name)
        if not db_path or not db_path.exists():
            return pd.DataFrame()
        
        try:
            conn = sqlite3.connect(str(db_path))
            
            if bot_name == "mega_aggressive":
                table_name = "mega_trades"
            elif bot_name == "ultra_aggressive":
                table_name = "ultra_trades"
            else:
                table_name = "trades"
            
            query = f"""
            SELECT timestamp, action, amount, price, profit_loss, balance_after
            FROM {table_name}
            ORDER BY timestamp DESC
            LIMIT {limit}
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
            
        except Exception as e:
            st.error(f"Errore lettura trade recenti {bot_name}: {str(e)}")
            return pd.DataFrame()

def main():
    master = AurumBotXMaster()
    
    # Header principale
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AurumBotX Master Dashboard</h1>
        <p>Sistema Unificato di Controllo e Monitoraggio Trading</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar controlli
    st.sidebar.title("🎛️ Controlli Sistema")
    
    # Status bot
    bot_status = master.get_bot_status()
    
    st.sidebar.subheader("📊 Status Bot")
    for bot_name, is_running in bot_status.items():
        status_class = "bot-status-active" if is_running else "bot-status-inactive"
        status_text = "🟢 ATTIVO" if is_running else "🔴 FERMO"
        st.sidebar.markdown(f"**{bot_name.replace('_', ' ').title()}**: <span class='{status_class}'>{status_text}</span>", 
                           unsafe_allow_html=True)
    
    # Controlli bot
    st.sidebar.subheader("🎮 Controlli Bot")
    
    selected_bot = st.sidebar.selectbox(
        "Seleziona Bot",
        options=list(master.bot_scripts.keys()),
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("▶️ START", key=f"start_{selected_bot}", help="Avvia bot selezionato"):
            success, message = master.start_bot(selected_bot)
            if success:
                st.success(message)
                time.sleep(1)
                st.rerun()
            else:
                st.error(message)
    
    with col2:
        if st.button("⏹️ STOP", key=f"stop_{selected_bot}", help="Ferma bot selezionato"):
            success, message = master.stop_bot(selected_bot)
            if success:
                st.success(message)
                time.sleep(1)
                st.rerun()
            else:
                st.error(message)
    
    # Controlli globali
    st.sidebar.subheader("🌐 Controlli Globali")
    
    if st.sidebar.button("🚀 START ALL", help="Avvia tutti i bot"):
        results = []
        for bot_name in master.bot_scripts.keys():
            success, message = master.start_bot(bot_name)
            results.append((bot_name, success, message))
        
        for bot_name, success, message in results:
            if success:
                st.sidebar.success(f"{bot_name}: {message}")
            else:
                st.sidebar.error(f"{bot_name}: {message}")
        
        time.sleep(2)
        st.rerun()
    
    if st.sidebar.button("⛔ STOP ALL", help="Ferma tutti i bot"):
        results = []
        for bot_name in master.bot_scripts.keys():
            success, message = master.stop_bot(bot_name)
            results.append((bot_name, success, message))
        
        for bot_name, success, message in results:
            if success:
                st.sidebar.success(f"{bot_name}: {message}")
            else:
                st.sidebar.warning(f"{bot_name}: {message}")
        
        time.sleep(2)
        st.rerun()
    
    # Dashboard principale
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔥 Mega Aggressive", "⚡ Ultra Aggressive", "💰 Mainnet €250"])
    
    with tab1:
        st.subheader("📊 Panoramica Generale")
        
        # Metriche aggregate
        col1, col2, col3, col4 = st.columns(4)
        
        total_trades = 0
        total_profit = 0
        active_bots = sum(bot_status.values())
        
        for bot_name in master.bot_scripts.keys():
            data = master.get_trading_data(bot_name)
            if data:
                total_trades += data.get('total_trades', 0)
                total_profit += data.get('total_profit', 0)
        
        with col1:
            st.metric("🤖 Bot Attivi", f"{active_bots}/3", 
                     delta=f"{active_bots-1} vs target" if active_bots < 3 else "Tutti attivi")
        
        with col2:
            st.metric("🎯 Trade Totali", f"{total_trades:,}")
        
        with col3:
            st.metric("💰 Profitto Totale", f"€{total_profit:,.2f}")
        
        with col4:
            avg_profit = total_profit / total_trades if total_trades > 0 else 0
            st.metric("📈 Profitto Medio", f"€{avg_profit:,.2f}")
        
        # Grafici comparativi
        st.subheader("📈 Performance Comparative")
        
        comparison_data = []
        for bot_name in master.bot_scripts.keys():
            data = master.get_trading_data(bot_name)
            if data and data.get('total_trades', 0) > 0:
                comparison_data.append({
                    'Bot': bot_name.replace('_', ' ').title(),
                    'Trade': data['total_trades'],
                    'Profitto': data['total_profit'],
                    'Win Rate': data['win_rate'],
                    'Status': '🟢 Attivo' if bot_status[bot_name] else '🔴 Fermo'
                })
        
        if comparison_data:
            df_comparison = pd.DataFrame(comparison_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_trades = px.bar(df_comparison, x='Bot', y='Trade', 
                                  title="Trade per Bot", color='Bot')
                fig_trades.update_layout(showlegend=False)
                st.plotly_chart(fig_trades, use_container_width=True)
            
            with col2:
                fig_profit = px.bar(df_comparison, x='Bot', y='Profitto', 
                                  title="Profitto per Bot", color='Bot')
                fig_profit.update_layout(showlegend=False)
                st.plotly_chart(fig_profit, use_container_width=True)
            
            # Tabella riepilogativa
            st.subheader("📋 Riepilogo Dettagliato")
            st.dataframe(df_comparison, use_container_width=True)
    
    # Tab specifici per ogni bot
    for tab, bot_name in zip([tab2, tab3, tab4], ["mega_aggressive", "ultra_aggressive", "mainnet_250"]):
        with tab:
            bot_display_name = bot_name.replace('_', ' ').title()
            st.subheader(f"📊 {bot_display_name}")
            
            # Status e controlli
            is_running = bot_status[bot_name]
            status_color = "🟢" if is_running else "🔴"
            status_text = "ATTIVO" if is_running else "FERMO"
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**Status**: {status_color} {status_text}")
            
            with col2:
                if st.button(f"▶️ Avvia", key=f"start_tab_{bot_name}"):
                    success, message = master.start_bot(bot_name)
                    if success:
                        st.success(message)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)
            
            with col3:
                if st.button(f"⏹️ Ferma", key=f"stop_tab_{bot_name}"):
                    success, message = master.stop_bot(bot_name)
                    if success:
                        st.success(message)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)
            
            # Dati trading
            data = master.get_trading_data(bot_name)
            
            if data and data.get('total_trades', 0) > 0:
                # Metriche principali
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("🎯 Trade", f"{data['total_trades']:,}")
                
                with col2:
                    st.metric("💰 Profitto", f"€{data['total_profit']:,.2f}")
                
                with col3:
                    st.metric("✅ Win Rate", f"{data['win_rate']:.1f}%")
                
                with col4:
                    st.metric("📈 Balance Max", f"€{data['max_balance']:,.2f}")
                
                # Trade recenti
                st.subheader("📋 Trade Recenti")
                recent_trades = master.get_recent_trades(bot_name)
                
                if not recent_trades.empty:
                    # Formatta i dati per visualizzazione
                    recent_trades['timestamp'] = pd.to_datetime(recent_trades['timestamp']).dt.strftime('%d/%m %H:%M')
                    recent_trades['profit_loss'] = recent_trades['profit_loss'].apply(lambda x: f"€{x:.2f}")
                    recent_trades['balance_after'] = recent_trades['balance_after'].apply(lambda x: f"€{x:,.2f}")
                    recent_trades['amount'] = recent_trades['amount'].apply(lambda x: f"€{x:.2f}")
                    
                    st.dataframe(recent_trades, use_container_width=True)
                else:
                    st.info("Nessun trade recente disponibile")
            else:
                st.info(f"Nessun dato disponibile per {bot_display_name}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; opacity: 0.7;'>
        🤖 AurumBotX Master Dashboard v2.0 | Sistema Unificato di Trading Automatico
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh ogni 30 secondi
    time.sleep(30)
    st.rerun()

if __name__ == "__main__":
    main()

