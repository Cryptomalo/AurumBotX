import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text
from utils.models import get_database_session
import plotly.graph_objects as go
import plotly.express as px

# Configurazione pagina
st.set_page_config(
    page_title="Crypto Trading Monitor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titolo
st.title("🤖 Crypto Trading Monitor")

@st.cache_data(ttl=60)  # Cache per 60 secondi
def load_trading_data():
    """Carica i dati più recenti dal database con gestione errori"""
    try:
        session = get_database_session()
        query = text("""
            SELECT symbol, price, volume, timestamp 
            FROM trading_data 
            WHERE timestamp > NOW() - INTERVAL '24 hours'
            ORDER BY timestamp DESC
        """)

        df = pd.read_sql(query, session.bind)
        session.remove()  # Chiudi correttamente la sessione
        return df
    except Exception as e:
        st.error(f"Errore nel caricamento dei dati: {str(e)}")
        return pd.DataFrame()

# Carica i dati
data = load_trading_data()

if not data.empty:
    # Metriche generali
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Simboli monitorati", len(data['symbol'].unique()))
    with col2:
        st.metric("Transazioni totali", len(data))
    with col3:
        last_update = data['timestamp'].max()
        st.metric("Ultimo aggiornamento", last_update.strftime('%H:%M:%S'))

    # Selezione simbolo e visualizzazione grafico
    st.subheader("📊 Andamento Prezzi")
    symbol = st.selectbox("Seleziona simbolo", sorted(data['symbol'].unique()))

    symbol_data = data[data['symbol'] == symbol].copy()
    if not symbol_data.empty:
        # Grafico interattivo con Plotly
        fig = px.line(
            symbol_data,
            x='timestamp',
            y='price',
            title=f'Prezzo {symbol} nelle ultime 24 ore'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Statistiche dettagliate
        col1, col2, col3, col4 = st.columns(4)
        current_price = symbol_data['price'].iloc[0]
        price_change = current_price - symbol_data['price'].iloc[-1]
        price_change_pct = (price_change / symbol_data['price'].iloc[-1]) * 100

        with col1:
            st.metric("Prezzo attuale", f"${current_price:.2f}")
        with col2:
            st.metric("Variazione", f"${price_change:.2f} ({price_change_pct:.1f}%)")
        with col3:
            st.metric("Volume 24h", f"${symbol_data['volume'].sum():,.2f}")
        with col4:
            st.metric("Transazioni", len(symbol_data))

        # Grafico volume
        st.subheader("📈 Volume Trading")
        volume_fig = px.bar(
            symbol_data,
            x='timestamp',
            y='volume',
            title=f'Volume {symbol}'
        )
        st.plotly_chart(volume_fig, use_container_width=True)
else:
    st.info("Nessun dato disponibile. Il trading bot sta raccogliendo i dati...")

# Aggiornamento automatico
st.empty()
if st.button("Aggiorna"):
    st.rerun()  # Uso st.rerun() invece di st.experimental_rerun()