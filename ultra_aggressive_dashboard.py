"""
🔥 DASHBOARD ULTRA-AGGRESSIVE TRADING
Monitoraggio Real-time Sistema Ultra-Aggressivo
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3
import time
import os
import numpy as np

# Configurazione pagina
st.set_page_config(
    page_title="🔥 Ultra-Aggressive Trading Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizzato
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #ff4757, #ff3838);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #ff4757 0%, #ff3838 100%);
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
    .success-card {
        background: linear-gradient(135deg, #2ed573 0%, #1e90ff 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .warning-card {
        background: linear-gradient(135deg, #ffa502 0%, #ff6348 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .trade-card {
        background: #f8f9fa;
        border-left: 4px solid #ff4757;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

def load_ultra_aggressive_data():
    """Carica dati dal database ultra-aggressivo"""
    try:
        if not os.path.exists('ultra_aggressive_trading.db'):
            return pd.DataFrame(), {}
        
        conn = sqlite3.connect('ultra_aggressive_trading.db')
        
        # Carica tutti i trade
        query = """
        SELECT * FROM ultra_trades 
        ORDER BY timestamp DESC
        """
        
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            conn.close()
            return df, {}
        
        # Calcola statistiche
        stats = {
            'total_trades': len(df),
            'winning_trades': len(df[df['profit_loss'] > 0]),
            'losing_trades': len(df[df['profit_loss'] < 0]),
            'total_pnl': df['profit_loss'].sum(),
            'total_fees': df['fee'].sum(),
            'avg_pnl': df['profit_loss'].mean(),
            'max_win': df['profit_loss'].max(),
            'max_loss': df['profit_loss'].min(),
            'current_balance': df['balance_after'].iloc[0] if len(df) > 0 else 1000,
            'initial_balance': 1000,
            'win_rate': (len(df[df['profit_loss'] > 0]) / len(df) * 100) if len(df) > 0 else 0,
            'avg_position_size': df['position_size_percent'].mean(),
            'avg_confidence': df['confidence'].mean(),
            'last_trade_time': df['timestamp'].iloc[0] if len(df) > 0 else None
        }
        
        stats['roi'] = ((stats['current_balance'] - stats['initial_balance']) / stats['initial_balance'] * 100)
        
        conn.close()
        return df, stats
        
    except Exception as e:
        st.error(f"Errore caricamento dati: {e}")
        return pd.DataFrame(), {}

def display_header():
    """Mostra header principale"""
    st.markdown("""
    <div class="main-header">
        <h1>🔥 ULTRA-AGGRESSIVE TRADING SYSTEM</h1>
        <h3>💰 Sistema di Trading Ultra-Aggressivo - Performance Real-time</h3>
        <p>Position Size: 5-12% | Confidence: 15%+ | Profit Target: 0.8-3%</p>
    </div>
    """, unsafe_allow_html=True)

def display_key_metrics(stats):
    """Mostra metriche chiave"""
    if not stats:
        st.warning("⚠️ Nessun dato disponibile")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${stats['current_balance']:.2f}</div>
            <div class="metric-label">💰 Balance Corrente</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        roi_color = "#2ed573" if stats['roi'] > 0 else "#ff4757"
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, {roi_color} 0%, {roi_color}aa 100%);">
            <div class="metric-value">{stats['roi']:.2f}%</div>
            <div class="metric-label">📈 ROI</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${stats['total_pnl']:.2f}</div>
            <div class="metric-label">💸 Profitto Totale</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{stats['total_trades']}</div>
            <div class="metric-label">🎯 Trade Totali</div>
        </div>
        """, unsafe_allow_html=True)

def display_performance_metrics(stats):
    """Mostra metriche di performance"""
    if not stats:
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        win_rate_color = "#2ed573" if stats['win_rate'] > 60 else "#ffa502" if stats['win_rate'] > 40 else "#ff4757"
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, {win_rate_color} 0%, {win_rate_color}aa 100%);">
            <div class="metric-value">{stats['win_rate']:.1f}%</div>
            <div class="metric-label">✅ Win Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${stats['avg_pnl']:.2f}</div>
            <div class="metric-label">📊 Avg P&L</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{stats['avg_position_size']:.1f}%</div>
            <div class="metric-label">💰 Avg Position</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{stats['avg_confidence']:.1%}</div>
            <div class="metric-label">🎯 Avg Confidence</div>
        </div>
        """, unsafe_allow_html=True)

def display_balance_chart(df):
    """Mostra grafico evoluzione balance"""
    if df.empty:
        return
    
    st.subheader("📈 Evoluzione Balance")
    
    # Prepara dati per il grafico
    df_chart = df.copy()
    df_chart['timestamp'] = pd.to_datetime(df_chart['timestamp'])
    df_chart = df_chart.sort_values('timestamp')
    
    # Crea grafico
    fig = go.Figure()
    
    # Linea balance
    fig.add_trace(go.Scatter(
        x=df_chart['timestamp'],
        y=df_chart['balance_after'],
        mode='lines+markers',
        name='Balance',
        line=dict(color='#ff4757', width=3),
        marker=dict(size=8, color='#ff4757'),
        hovertemplate='<b>%{y:.2f}$</b><br>%{x}<extra></extra>'
    ))
    
    # Linea balance iniziale
    fig.add_hline(y=1000, line_dash="dash", line_color="gray", 
                  annotation_text="Balance Iniziale ($1000)")
    
    fig.update_layout(
        title="💰 Evoluzione Balance Ultra-Aggressivo",
        xaxis_title="Tempo",
        yaxis_title="Balance ($)",
        template="plotly_white",
        height=400,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_pnl_chart(df):
    """Mostra grafico P&L per trade"""
    if df.empty:
        return
    
    st.subheader("💸 P&L per Trade")
    
    df_chart = df.copy()
    df_chart['timestamp'] = pd.to_datetime(df_chart['timestamp'])
    df_chart = df_chart.sort_values('timestamp')
    df_chart['trade_number'] = range(1, len(df_chart) + 1)
    
    # Colori per profit/loss
    colors = ['#2ed573' if pnl > 0 else '#ff4757' for pnl in df_chart['profit_loss']]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_chart['trade_number'],
        y=df_chart['profit_loss'],
        marker_color=colors,
        name='P&L',
        hovertemplate='<b>Trade #%{x}</b><br>P&L: $%{y:.2f}<extra></extra>'
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    fig.update_layout(
        title="📊 Profitto/Perdita per Trade",
        xaxis_title="Numero Trade",
        yaxis_title="P&L ($)",
        template="plotly_white",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_position_size_chart(df):
    """Mostra distribuzione position size"""
    if df.empty:
        return
    
    st.subheader("💰 Distribuzione Position Size")
    
    fig = px.histogram(
        df, 
        x='position_size_percent',
        nbins=20,
        title="Distribuzione Position Size (%)",
        color_discrete_sequence=['#ff4757']
    )
    
    fig.update_layout(
        xaxis_title="Position Size (%)",
        yaxis_title="Frequenza",
        template="plotly_white",
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_recent_trades(df):
    """Mostra trade recenti"""
    if df.empty:
        return
    
    st.subheader("🔥 Trade Recenti")
    
    # Ultimi 10 trade
    recent_trades = df.head(10).copy()
    recent_trades['timestamp'] = pd.to_datetime(recent_trades['timestamp'])
    
    for _, trade in recent_trades.iterrows():
        profit_color = "#2ed573" if trade['profit_loss'] > 0 else "#ff4757"
        profit_emoji = "💚" if trade['profit_loss'] > 0 else "❤️"
        
        st.markdown(f"""
        <div class="trade-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>{profit_emoji} {trade['action']} ${trade['amount']:.2f}</strong><br>
                    <small>📅 {trade['timestamp'].strftime('%d/%m/%Y %H:%M:%S')}</small>
                </div>
                <div style="text-align: right;">
                    <div style="color: {profit_color}; font-weight: bold; font-size: 1.2em;">
                        ${trade['profit_loss']:.2f}
                    </div>
                    <small>Pos: {trade['position_size_percent']:.1f}% | Conf: {trade['confidence']:.1%}</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_comparison_with_old_system():
    """Mostra confronto con sistema vecchio"""
    st.subheader("⚔️ Confronto con Sistema Precedente")
    
    try:
        # Dati sistema vecchio
        if os.path.exists('aggressive_trading.db'):
            conn_old = sqlite3.connect('aggressive_trading.db')
            old_stats = pd.read_sql_query("""
                SELECT 
                    COUNT(*) as trades,
                    SUM(profit_loss) as total_pnl,
                    AVG(profit_loss) as avg_pnl,
                    SUM(fee) as total_fees
                FROM aggressive_trades
            """, conn_old).iloc[0]
            conn_old.close()
        else:
            old_stats = {'trades': 0, 'total_pnl': 0, 'avg_pnl': 0, 'total_fees': 0}
        
        # Dati sistema ultra-aggressivo
        if os.path.exists('ultra_aggressive_trading.db'):
            conn_new = sqlite3.connect('ultra_aggressive_trading.db')
            new_stats = pd.read_sql_query("""
                SELECT 
                    COUNT(*) as trades,
                    SUM(profit_loss) as total_pnl,
                    AVG(profit_loss) as avg_pnl,
                    SUM(fee) as total_fees
                FROM ultra_trades
            """, conn_new).iloc[0]
            conn_new.close()
        else:
            new_stats = {'trades': 0, 'total_pnl': 0, 'avg_pnl': 0, 'total_fees': 0}
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="warning-card">
                <h4>📊 Sistema Precedente</h4>
                <p><strong>Trade:</strong> {}</p>
                <p><strong>Profitto Totale:</strong> ${:.2f}</p>
                <p><strong>Avg P&L:</strong> ${:.3f}</p>
                <p><strong>Fee:</strong> ${:.2f}</p>
            </div>
            """.format(
                old_stats['trades'],
                old_stats['total_pnl'],
                old_stats['avg_pnl'],
                old_stats['total_fees']
            ), unsafe_allow_html=True)
        
        with col2:
            improvement = (new_stats['avg_pnl'] / old_stats['avg_pnl'] * 100) if old_stats['avg_pnl'] > 0 else 0
            st.markdown("""
            <div class="success-card">
                <h4>🔥 Sistema Ultra-Aggressivo</h4>
                <p><strong>Trade:</strong> {}</p>
                <p><strong>Profitto Totale:</strong> ${:.2f}</p>
                <p><strong>Avg P&L:</strong> ${:.3f}</p>
                <p><strong>Fee:</strong> ${:.2f}</p>
                <p><strong>🚀 Miglioramento:</strong> {:.0f}x</p>
            </div>
            """.format(
                new_stats['trades'],
                new_stats['total_pnl'],
                new_stats['avg_pnl'],
                new_stats['total_fees'],
                improvement / 100 if improvement > 0 else 0
            ), unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Errore confronto: {e}")

def main():
    """Funzione principale"""
    # Header
    display_header()
    
    # Auto-refresh
    if st.sidebar.button("🔄 Aggiorna Dati"):
        st.experimental_rerun()
    
    # Carica dati
    df, stats = load_ultra_aggressive_data()
    
    if df.empty:
        st.warning("⚠️ Nessun trade ultra-aggressivo trovato. Il sistema potrebbe non essere ancora attivo.")
        st.info("💡 Assicurati che il sistema ultra-aggressivo sia in esecuzione.")
        return
    
    # Metriche principali
    display_key_metrics(stats)
    
    # Metriche performance
    display_performance_metrics(stats)
    
    # Grafici
    col1, col2 = st.columns(2)
    
    with col1:
        display_balance_chart(df)
    
    with col2:
        display_pnl_chart(df)
    
    # Position size distribution
    display_position_size_chart(df)
    
    # Trade recenti
    display_recent_trades(df)
    
    # Confronto sistemi
    display_comparison_with_old_system()
    
    # Info sistema
    st.sidebar.markdown("### 🔥 Sistema Ultra-Aggressivo")
    st.sidebar.markdown(f"**Database:** ultra_aggressive_trading.db")
    st.sidebar.markdown(f"**Ultimo aggiornamento:** {datetime.now().strftime('%H:%M:%S')}")
    
    if stats.get('last_trade_time'):
        last_trade = pd.to_datetime(stats['last_trade_time'])
        minutes_ago = (datetime.now() - last_trade.replace(tzinfo=None)).total_seconds() / 60
        st.sidebar.markdown(f"**Ultimo trade:** {minutes_ago:.0f} minuti fa")
    
    # Auto-refresh ogni 30 secondi
    time.sleep(30)
    st.experimental_rerun()

if __name__ == "__main__":
    main()

