#!/usr/bin/env python3
"""
AurumBotX Unified Real Dashboard
Dashboard unificata con tutti i dati reali aggiornati
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

# Configurazione pagina
st.set_page_config(
    page_title="AurumBotX - Dashboard Unificata",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizzato
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4, #FFEAA7);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 2rem;
        animation: gradient 3s ease infinite;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .profit-positive {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    
    .profit-negative {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
    }
    
    .system-active {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
</style>
""", unsafe_allow_html=True)

class UnifiedDashboard:
    """Dashboard unificata per tutti i sistemi"""
    
    def __init__(self):
        self.databases = {
            'mega_aggressive': 'mega_aggressive_trading.db',
            'ultra_aggressive': 'ultra_aggressive_trading.db',
            'mainnet_optimization': 'mainnet_optimization.db'
        }
        
    def get_database_data(self, db_name, table_name):
        """Ottieni dati da database specifico"""
        try:
            if not os.path.exists(db_name):
                return pd.DataFrame()
                
            conn = sqlite3.connect(db_name)
            
            # Query generica per trade
            query = f"""
                SELECT 
                    timestamp,
                    action,
                    amount,
                    price,
                    profit_loss,
                    balance_after,
                    CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END as is_win
                FROM {table_name}
                ORDER BY timestamp DESC
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['system'] = db_name.replace('_trading.db', '').replace('_', ' ').title()
            
            return df
            
        except Exception as e:
            st.error(f"Errore lettura database {db_name}: {e}")
            return pd.DataFrame()
    
    def get_all_trades(self):
        """Ottieni tutti i trade da tutti i sistemi"""
        all_trades = []
        
        # Mega Aggressive
        mega_trades = self.get_database_data('mega_aggressive_trading.db', 'mega_trades')
        if not mega_trades.empty:
            mega_trades['system'] = 'Mega Aggressive'
            all_trades.append(mega_trades)
        
        # Ultra Aggressive
        ultra_trades = self.get_database_data('ultra_aggressive_trading.db', 'ultra_trades')
        if not ultra_trades.empty:
            ultra_trades['system'] = 'Ultra Aggressive'
            all_trades.append(ultra_trades)
        
        # Mainnet Optimization
        mainnet_trades = self.get_database_data('mainnet_optimization.db', 'optimized_trades')
        if not mainnet_trades.empty:
            mainnet_trades['system'] = 'Mainnet Optimization'
            all_trades.append(mainnet_trades)
        
        if all_trades:
            combined_df = pd.concat(all_trades, ignore_index=True)
            return combined_df.sort_values('timestamp', ascending=False)
        else:
            return pd.DataFrame()
    
    def calculate_system_stats(self, df, system_name):
        """Calcola statistiche per sistema specifico"""
        if df.empty:
            return {
                'total_trades': 0,
                'total_profit': 0.0,
                'avg_profit': 0.0,
                'win_rate': 0.0,
                'current_balance': 1000.0,
                'roi': 0.0,
                'best_trade': 0.0,
                'worst_trade': 0.0
            }
        
        system_df = df[df['system'] == system_name]
        
        if system_df.empty:
            return {
                'total_trades': 0,
                'total_profit': 0.0,
                'avg_profit': 0.0,
                'win_rate': 0.0,
                'current_balance': 1000.0,
                'roi': 0.0,
                'best_trade': 0.0,
                'worst_trade': 0.0
            }
        
        total_trades = len(system_df)
        total_profit = system_df['profit_loss'].sum()
        avg_profit = system_df['profit_loss'].mean()
        win_rate = (system_df['is_win'].sum() / total_trades * 100) if total_trades > 0 else 0
        current_balance = system_df['balance_after'].iloc[0] if not system_df.empty else 1000.0
        roi = ((current_balance - 1000) / 1000 * 100) if current_balance > 0 else 0
        best_trade = system_df['profit_loss'].max() if not system_df.empty else 0
        worst_trade = system_df['profit_loss'].min() if not system_df.empty else 0
        
        return {
            'total_trades': total_trades,
            'total_profit': total_profit,
            'avg_profit': avg_profit,
            'win_rate': win_rate,
            'current_balance': current_balance,
            'roi': roi,
            'best_trade': best_trade,
            'worst_trade': worst_trade
        }
    
    def render_header(self):
        """Render header principale"""
        st.markdown("""
        <div class="main-header">
            🚀 AURUMBOTX - DASHBOARD UNIFICATA REAL-TIME 🚀
        </div>
        """, unsafe_allow_html=True)
        
        # Timestamp ultimo aggiornamento
        st.markdown(f"**📅 Ultimo aggiornamento**: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    def render_system_overview(self, all_trades):
        """Render overview generale sistemi"""
        st.header("📊 Overview Sistemi Trading")
        
        systems = ['Mega Aggressive', 'Ultra Aggressive', 'Mainnet Optimization']
        
        cols = st.columns(3)
        
        for i, system in enumerate(systems):
            stats = self.calculate_system_stats(all_trades, system)
            
            with cols[i]:
                # Determina colore basato su performance
                if stats['roi'] > 50:
                    card_class = "profit-positive"
                elif stats['roi'] > 0:
                    card_class = "system-active"
                else:
                    card_class = "profit-negative"
                
                st.markdown(f"""
                <div class="metric-card {card_class}">
                    <h3>{system}</h3>
                    <p><strong>Trade:</strong> {stats['total_trades']}</p>
                    <p><strong>Profitto:</strong> ${stats['total_profit']:.2f}</p>
                    <p><strong>ROI:</strong> {stats['roi']:.1f}%</p>
                    <p><strong>Win Rate:</strong> {stats['win_rate']:.1f}%</p>
                    <p><strong>Balance:</strong> ${stats['current_balance']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)
    
    def render_performance_charts(self, all_trades):
        """Render grafici performance"""
        st.header("📈 Grafici Performance")
        
        if all_trades.empty:
            st.warning("Nessun dato di trading disponibile")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Grafico evoluzione balance per sistema
            st.subheader("💰 Evoluzione Balance")
            
            fig_balance = go.Figure()
            
            for system in all_trades['system'].unique():
                system_data = all_trades[all_trades['system'] == system].sort_values('timestamp')
                
                if not system_data.empty:
                    fig_balance.add_trace(go.Scatter(
                        x=system_data['timestamp'],
                        y=system_data['balance_after'],
                        mode='lines+markers',
                        name=system,
                        line=dict(width=3)
                    ))
            
            fig_balance.update_layout(
                title="Evoluzione Balance per Sistema",
                xaxis_title="Tempo",
                yaxis_title="Balance ($)",
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig_balance, use_container_width=True)
        
        with col2:
            # Grafico P&L cumulativo
            st.subheader("📊 P&L Cumulativo")
            
            fig_pnl = go.Figure()
            
            for system in all_trades['system'].unique():
                system_data = all_trades[all_trades['system'] == system].sort_values('timestamp')
                
                if not system_data.empty:
                    system_data['cumulative_pnl'] = system_data['profit_loss'].cumsum()
                    
                    fig_pnl.add_trace(go.Scatter(
                        x=system_data['timestamp'],
                        y=system_data['cumulative_pnl'],
                        mode='lines+markers',
                        name=system,
                        line=dict(width=3)
                    ))
            
            fig_pnl.update_layout(
                title="P&L Cumulativo per Sistema",
                xaxis_title="Tempo",
                yaxis_title="P&L Cumulativo ($)",
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig_pnl, use_container_width=True)
    
    def render_trade_analysis(self, all_trades):
        """Render analisi trade"""
        st.header("🔍 Analisi Trade Dettagliata")
        
        if all_trades.empty:
            st.warning("Nessun dato di trading disponibile")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Distribuzione profitti
            st.subheader("💰 Distribuzione Profitti")
            
            fig_dist = px.histogram(
                all_trades, 
                x='profit_loss', 
                color='system',
                title="Distribuzione P&L per Trade",
                nbins=20
            )
            fig_dist.update_layout(height=300)
            st.plotly_chart(fig_dist, use_container_width=True)
        
        with col2:
            # Win rate per sistema
            st.subheader("🎯 Win Rate Sistemi")
            
            win_rates = []
            for system in all_trades['system'].unique():
                system_data = all_trades[all_trades['system'] == system]
                if not system_data.empty:
                    win_rate = (system_data['is_win'].sum() / len(system_data) * 100)
                    win_rates.append({'Sistema': system, 'Win Rate': win_rate})
            
            if win_rates:
                win_rate_df = pd.DataFrame(win_rates)
                fig_winrate = px.bar(
                    win_rate_df, 
                    x='Sistema', 
                    y='Win Rate',
                    title="Win Rate per Sistema (%)",
                    color='Win Rate',
                    color_continuous_scale='RdYlGn'
                )
                fig_winrate.update_layout(height=300)
                st.plotly_chart(fig_winrate, use_container_width=True)
        
        with col3:
            # Volume trade per sistema
            st.subheader("📊 Volume Trade")
            
            trade_counts = all_trades['system'].value_counts()
            
            fig_volume = px.pie(
                values=trade_counts.values,
                names=trade_counts.index,
                title="Distribuzione Trade per Sistema"
            )
            fig_volume.update_layout(height=300)
            st.plotly_chart(fig_volume, use_container_width=True)
    
    def render_recent_trades(self, all_trades):
        """Render trade recenti"""
        st.header("🕐 Trade Recenti")
        
        if all_trades.empty:
            st.warning("Nessun trade disponibile")
            return
        
        # Filtra ultimi 20 trade
        recent_trades = all_trades.head(20).copy()
        
        # Formatta dati per visualizzazione
        recent_trades['Timestamp'] = recent_trades['timestamp'].dt.strftime('%d/%m/%Y %H:%M:%S')
        recent_trades['Sistema'] = recent_trades['system']
        recent_trades['Azione'] = recent_trades['action']
        recent_trades['Importo'] = recent_trades['amount'].apply(lambda x: f"${x:.2f}")
        recent_trades['Prezzo'] = recent_trades['price'].apply(lambda x: f"${x:.0f}")
        recent_trades['P&L'] = recent_trades['profit_loss'].apply(
            lambda x: f"${x:.2f}" if x >= 0 else f"-${abs(x):.2f}"
        )
        recent_trades['Balance'] = recent_trades['balance_after'].apply(lambda x: f"${x:.2f}")
        recent_trades['Risultato'] = recent_trades['is_win'].apply(lambda x: "✅ WIN" if x else "❌ LOSS")
        
        # Mostra tabella
        display_df = recent_trades[[
            'Timestamp', 'Sistema', 'Azione', 'Importo', 
            'Prezzo', 'P&L', 'Balance', 'Risultato'
        ]]
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )
    
    def render_live_metrics(self, all_trades):
        """Render metriche live"""
        st.header("⚡ Metriche Live")
        
        # Calcola metriche aggregate
        if not all_trades.empty:
            total_trades = len(all_trades)
            total_profit = all_trades['profit_loss'].sum()
            total_wins = all_trades['is_win'].sum()
            overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
            
            # Balance totale (somma dei balance massimi per sistema)
            total_balance = 0
            for system in all_trades['system'].unique():
                system_data = all_trades[all_trades['system'] == system]
                if not system_data.empty:
                    max_balance = system_data['balance_after'].max()
                    total_balance += max_balance
            
            total_roi = ((total_balance - 3000) / 3000 * 100) if total_balance > 0 else 0  # 3 sistemi x $1000
            
            # Best e worst trade
            best_trade = all_trades['profit_loss'].max()
            worst_trade = all_trades['profit_loss'].min()
            
        else:
            total_trades = 0
            total_profit = 0
            overall_win_rate = 0
            total_balance = 3000
            total_roi = 0
            best_trade = 0
            worst_trade = 0
        
        # Mostra metriche in colonne
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="🎯 Trade Totali",
                value=f"{total_trades}",
                delta=f"+{total_trades} eseguiti"
            )
        
        with col2:
            st.metric(
                label="💰 Profitto Totale",
                value=f"${total_profit:.2f}",
                delta=f"${total_profit:.2f}" if total_profit >= 0 else f"-${abs(total_profit):.2f}"
            )
        
        with col3:
            st.metric(
                label="📊 Win Rate",
                value=f"{overall_win_rate:.1f}%",
                delta=f"{overall_win_rate:.1f}% successo"
            )
        
        with col4:
            st.metric(
                label="💎 Balance Totale",
                value=f"${total_balance:.2f}",
                delta=f"${total_balance - 3000:.2f} vs iniziale"
            )
        
        with col5:
            st.metric(
                label="🚀 ROI Totale",
                value=f"{total_roi:.1f}%",
                delta=f"+{total_roi:.1f}% crescita"
            )
        
        # Seconda riga metriche
        col6, col7, col8, col9, col10 = st.columns(5)
        
        with col6:
            st.metric(
                label="🏆 Miglior Trade",
                value=f"${best_trade:.2f}",
                delta="Record positivo"
            )
        
        with col7:
            st.metric(
                label="📉 Peggior Trade",
                value=f"${worst_trade:.2f}",
                delta="Perdita massima"
            )
        
        with col8:
            avg_profit = total_profit / total_trades if total_trades > 0 else 0
            st.metric(
                label="📊 Profitto Medio",
                value=f"${avg_profit:.2f}",
                delta="Per trade"
            )
        
        with col9:
            # Calcola trade oggi
            today = datetime.now().date()
            if not all_trades.empty:
                today_trades = len(all_trades[all_trades['timestamp'].dt.date == today])
            else:
                today_trades = 0
            
            st.metric(
                label="📅 Trade Oggi",
                value=f"{today_trades}",
                delta=f"+{today_trades} oggi"
            )
        
        with col10:
            # Status sistemi attivi
            active_systems = len(all_trades['system'].unique()) if not all_trades.empty else 0
            st.metric(
                label="🤖 Sistemi Attivi",
                value=f"{active_systems}/3",
                delta="Operativi"
            )

def main():
    """Funzione principale dashboard"""
    
    # Inizializza dashboard
    dashboard = UnifiedDashboard()
    
    # Auto-refresh ogni 30 secondi
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    # Sidebar controlli
    st.sidebar.header("🎛️ Controlli Dashboard")
    
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (30s)", value=True)
    
    if auto_refresh:
        # Placeholder per countdown
        countdown_placeholder = st.sidebar.empty()
        
        # Calcola secondi rimanenti
        elapsed = time.time() - st.session_state.last_refresh
        remaining = max(0, 30 - elapsed)
        
        countdown_placeholder.write(f"⏰ Prossimo refresh: {remaining:.0f}s")
        
        # Refresh automatico
        if elapsed >= 30:
            st.session_state.last_refresh = time.time()
            st.experimental_rerun()
    
    # Pulsante refresh manuale
    if st.sidebar.button("🔄 Refresh Manuale"):
        st.session_state.last_refresh = time.time()
        st.experimental_rerun()
    
    # Filtri
    st.sidebar.header("🔍 Filtri")
    
    # Selezione sistemi
    available_systems = ['Mega Aggressive', 'Ultra Aggressive', 'Mainnet Optimization']
    selected_systems = st.sidebar.multiselect(
        "Sistemi da visualizzare",
        available_systems,
        default=available_systems
    )
    
    # Range date
    date_range = st.sidebar.selectbox(
        "Periodo",
        ["Ultimo giorno", "Ultimi 3 giorni", "Ultima settimana", "Tutto"]
    )
    
    # Carica dati
    with st.spinner("📊 Caricamento dati real-time..."):
        all_trades = dashboard.get_all_trades()
        
        # Applica filtri
        if not all_trades.empty and selected_systems:
            all_trades = all_trades[all_trades['system'].isin(selected_systems)]
        
        # Filtro date
        if not all_trades.empty and date_range != "Tutto":
            now = datetime.now()
            if date_range == "Ultimo giorno":
                cutoff = now - timedelta(days=1)
            elif date_range == "Ultimi 3 giorni":
                cutoff = now - timedelta(days=3)
            elif date_range == "Ultima settimana":
                cutoff = now - timedelta(days=7)
            
            all_trades = all_trades[all_trades['timestamp'] >= cutoff]
    
    # Render dashboard
    dashboard.render_header()
    dashboard.render_live_metrics(all_trades)
    dashboard.render_system_overview(all_trades)
    dashboard.render_performance_charts(all_trades)
    dashboard.render_trade_analysis(all_trades)
    dashboard.render_recent_trades(all_trades)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        🚀 AurumBotX Dashboard Unificata - Dati Real-Time Aggiornati<br>
        💎 Sistema di Trading Automatico Avanzato
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

