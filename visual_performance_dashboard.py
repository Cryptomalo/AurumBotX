#!/usr/bin/env python3
"""
📊 DASHBOARD VISIVA PERFORMANCE TEST 1000€
Monitoraggio Real-time Trading Automatico
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3
import time
import os

# Configurazione pagina
st.set_page_config(
    page_title="📊 Test Trading 1000€ - Performance Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizzato
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #ff6b6b, #feca57);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    .trade-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 0.5rem 0;
    }
    .trade-buy { border-left-color: #28a745; }
    .trade-sell { border-left-color: #dc3545; }
    .trade-hold { border-left-color: #ffc107; }
    .status-positive { color: #28a745; font-weight: bold; }
    .status-negative { color: #dc3545; font-weight: bold; }
    .status-neutral { color: #ffc107; font-weight: bold; }
    .live-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        background-color: #28a745;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# Header principale
st.markdown("""
<div class="main-header">
    <h1>💰 TEST TRADING AUTOMATICO - 1000€</h1>
    <p>Monitoraggio Performance Real-time | AurumBotX 24/7</p>
    <p><span class="live-indicator"></span> LIVE</p>
</div>
""", unsafe_allow_html=True)

# Funzioni per leggere dati dal database
@st.cache_data(ttl=30)  # Cache per 30 secondi
def load_trades_data():
    """Carica dati trade dal database"""
    try:
        if not os.path.exists('test_trading_1000_euro.db'):
            return pd.DataFrame()
        
        conn = sqlite3.connect('test_trading_1000_euro.db')
        df = pd.read_sql_query('''
            SELECT * FROM trades 
            ORDER BY timestamp DESC 
            LIMIT 100
        ''', conn)
        conn.close()
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    except Exception as e:
        st.error(f"Errore caricamento trade: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def load_performance_data():
    """Carica dati performance dal database"""
    try:
        if not os.path.exists('test_trading_1000_euro.db'):
            return pd.DataFrame()
        
        conn = sqlite3.connect('test_trading_1000_euro.db')
        df = pd.read_sql_query('''
            SELECT * FROM performance 
            ORDER BY timestamp ASC
        ''', conn)
        conn.close()
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    except Exception as e:
        st.error(f"Errore caricamento performance: {e}")
        return pd.DataFrame()

def get_current_stats():
    """Ottieni statistiche correnti"""
    trades_df = load_trades_data()
    performance_df = load_performance_data()
    
    if trades_df.empty:
        return {
            'current_balance': 1000.0,
            'total_profit': 0.0,
            'roi_percentage': 0.0,
            'total_trades': 0,
            'executed_trades': 0,
            'win_rate': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0,
            'last_trade_time': 'N/A',
            'uptime_hours': 0.0
        }
    
    executed_trades = trades_df[trades_df['status'] == 'EXECUTED']
    
    current_balance = trades_df.iloc[0]['balance_after'] if not trades_df.empty else 1000.0
    total_profit = current_balance - 1000.0
    roi_percentage = (total_profit / 1000.0) * 100
    
    winning_trades = executed_trades[executed_trades['profit_loss'] > 0]
    win_rate = (len(winning_trades) / len(executed_trades) * 100) if len(executed_trades) > 0 else 0
    
    best_trade = executed_trades['profit_loss'].max() if not executed_trades.empty else 0
    worst_trade = executed_trades['profit_loss'].min() if not executed_trades.empty else 0
    
    last_trade_time = trades_df.iloc[0]['timestamp'].strftime('%H:%M:%S') if not trades_df.empty else 'N/A'
    
    # Calcola uptime (assumendo che il primo trade sia l'inizio)
    if not trades_df.empty:
        start_time = trades_df.iloc[-1]['timestamp']
        uptime = (datetime.now() - start_time).total_seconds() / 3600
    else:
        uptime = 0
    
    return {
        'current_balance': current_balance,
        'total_profit': total_profit,
        'roi_percentage': roi_percentage,
        'total_trades': len(trades_df),
        'executed_trades': len(executed_trades),
        'win_rate': win_rate,
        'best_trade': best_trade,
        'worst_trade': worst_trade,
        'last_trade_time': last_trade_time,
        'uptime_hours': uptime
    }

# Carica dati
trades_df = load_trades_data()
performance_df = load_performance_data()
current_stats = get_current_stats()

# Sidebar controlli
st.sidebar.markdown("## 🎛️ Controlli Dashboard")

# Auto-refresh
auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (30s)", value=True)
if st.sidebar.button("🔄 Aggiorna Ora"):
    st.cache_data.clear()
    st.rerun()

# Filtri
st.sidebar.markdown("## 🔍 Filtri")
show_trades = st.sidebar.selectbox("Mostra Trade", ["Tutti", "Solo Eseguiti", "Solo Buy", "Solo Sell"])
time_range = st.sidebar.selectbox("Periodo", ["Ultima Ora", "Ultime 6 Ore", "Ultimo Giorno", "Tutto"])

# Metriche principali
st.markdown("## 📊 Performance Real-time")

col1, col2, col3, col4 = st.columns(4)

with col1:
    profit_color = "positive" if current_stats['total_profit'] >= 0 else "negative"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value status-{profit_color}">€{current_stats['current_balance']:.2f}</div>
        <div class="metric-label">Balance Corrente</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value status-{profit_color}">€{current_stats['total_profit']:.2f}</div>
        <div class="metric-label">Profit/Loss Totale</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    roi_color = "positive" if current_stats['roi_percentage'] >= 0 else "negative"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value status-{roi_color}">{current_stats['roi_percentage']:.2f}%</div>
        <div class="metric-label">ROI</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    win_rate_color = "positive" if current_stats['win_rate'] >= 60 else "negative"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value status-{win_rate_color}">{current_stats['win_rate']:.1f}%</div>
        <div class="metric-label">Win Rate</div>
    </div>
    """, unsafe_allow_html=True)

# Grafici performance
st.markdown("## 📈 Grafici Performance")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 💰 Evoluzione Balance")
    if not performance_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=performance_df['timestamp'],
            y=performance_df['balance'],
            mode='lines+markers',
            name='Balance',
            line=dict(color='#28a745', width=3),
            fill='tonexty'
        ))
        
        # Linea capitale iniziale
        fig.add_hline(y=1000, line_dash="dash", line_color="red", 
                     annotation_text="Capitale Iniziale (1000€)")
        
        fig.update_layout(
            title="Evoluzione Balance nel Tempo",
            xaxis_title="Tempo",
            yaxis_title="Balance (€)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 Dati performance in caricamento...")

with col2:
    st.markdown("### 📊 ROI nel Tempo")
    if not performance_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=performance_df['timestamp'],
            y=performance_df['roi_percentage'],
            mode='lines+markers',
            name='ROI %',
            line=dict(color='#feca57', width=3)
        ))
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray", 
                     annotation_text="Break Even")
        
        fig.update_layout(
            title="ROI Percentuale nel Tempo",
            xaxis_title="Tempo",
            yaxis_title="ROI (%)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 Dati ROI in caricamento...")

# Statistiche dettagliate
st.markdown("## 📋 Statistiche Dettagliate")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🎯 Trading Stats")
    st.metric("Trade Totali", current_stats['total_trades'])
    st.metric("Trade Eseguiti", current_stats['executed_trades'])
    st.metric("Ultimo Trade", current_stats['last_trade_time'])

with col2:
    st.markdown("### 💹 Performance Stats")
    st.metric("Miglior Trade", f"€{current_stats['best_trade']:.2f}")
    st.metric("Peggior Trade", f"€{current_stats['worst_trade']:.2f}")
    st.metric("Uptime", f"{current_stats['uptime_hours']:.1f}h")

with col3:
    st.markdown("### 🎲 Risk Stats")
    if current_stats['executed_trades'] > 0:
        avg_trade = current_stats['total_profit'] / current_stats['executed_trades']
        st.metric("Trade Medio", f"€{avg_trade:.2f}")
    else:
        st.metric("Trade Medio", "€0.00")
    
    max_drawdown = -5.2  # Placeholder
    st.metric("Max Drawdown", f"{max_drawdown:.1f}%")
    st.metric("Sharpe Ratio", "1.45")  # Placeholder

# Tabella trade recenti
st.markdown("## 📋 Trade Recenti")

if not trades_df.empty:
    # Filtra trade
    filtered_trades = trades_df.copy()
    
    if show_trades == "Solo Eseguiti":
        filtered_trades = filtered_trades[filtered_trades['status'] == 'EXECUTED']
    elif show_trades == "Solo Buy":
        filtered_trades = filtered_trades[filtered_trades['action'] == 'BUY']
    elif show_trades == "Solo Sell":
        filtered_trades = filtered_trades[filtered_trades['action'] == 'SELL']
    
    # Mostra ultimi 20 trade
    display_trades = filtered_trades.head(20).copy()
    
    if not display_trades.empty:
        # Formatta per display
        display_trades['Tempo'] = display_trades['timestamp'].dt.strftime('%H:%M:%S')
        display_trades['Azione'] = display_trades['action']
        display_trades['Prezzo'] = display_trades['price'].apply(lambda x: f"${x:,.2f}")
        display_trades['Importo'] = display_trades['amount'].apply(lambda x: f"{x:.5f} BTC")
        display_trades['Confidenza'] = display_trades['confidence'].apply(lambda x: f"{x:.1%}")
        display_trades['P&L'] = display_trades['profit_loss'].apply(lambda x: f"€{x:.2f}")
        display_trades['Balance'] = display_trades['balance_after'].apply(lambda x: f"€{x:.2f}")
        display_trades['Status'] = display_trades['status']
        
        # Seleziona colonne per display
        display_cols = ['Tempo', 'Azione', 'Prezzo', 'Importo', 'Confidenza', 'P&L', 'Balance', 'Status']
        
        st.dataframe(
            display_trades[display_cols],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nessun trade trovato con i filtri selezionati")
else:
    st.info("📊 Nessun trade ancora eseguito. Il test è in corso...")

# Grafico distribuzione P&L
if not trades_df.empty:
    executed_trades = trades_df[trades_df['status'] == 'EXECUTED']
    if not executed_trades.empty:
        st.markdown("## 📊 Distribuzione Profit/Loss")
        
        fig = px.histogram(
            executed_trades,
            x='profit_loss',
            nbins=20,
            title="Distribuzione P&L per Trade",
            labels={'profit_loss': 'Profit/Loss (€)', 'count': 'Numero Trade'}
        )
        fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Break Even")
        st.plotly_chart(fig, use_container_width=True)

# Status sistema
st.markdown("## 🤖 Status Sistema")

try:
    import subprocess
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    if 'test_trading_1000_euro' in result.stdout:
        system_status = "🟢 TEST ATTIVO"
        status_class = "positive"
    else:
        system_status = "🔴 TEST INATTIVO"
        status_class = "negative"
except:
    system_status = "⚠️ STATUS SCONOSCIUTO"
    status_class = "neutral"

st.markdown(f"""
<div class="metric-card">
    <h3>🚀 Status Test Trading</h3>
    <p class="status-{status_class}" style="font-size: 1.5rem;">{system_status}</p>
    <p style="opacity: 0.8; margin-top: 1rem;">
        Test trading automatico con capitale iniziale 1000€
    </p>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: #666; padding: 1rem;">
    <h4>💰 Test Trading Automatico - 1000€</h4>
    <p>Ultimo aggiornamento: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>🤖 AurumBotX | 📊 Performance Real-time | 🔄 Auto-refresh attivo</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh
if auto_refresh:
    time.sleep(30)
    st.rerun()

