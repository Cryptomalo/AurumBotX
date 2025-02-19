import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sqlalchemy import text
import logging
from utils.models import get_database_session
from utils.trading_bot import WebSocketHandler

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='streamlit_app.log'
)
logger = logging.getLogger(__name__)

# Configurazione pagina
st.set_page_config(
    page_title="AurumBot Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stile CSS personalizzato
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #1c1c1c;
        padding: 1rem;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Inizializza le variabili di stato della sessione"""
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()
    if 'selected_timeframe' not in st.session_state:
        st.session_state.selected_timeframe = '24h'

@st.cache_data(ttl=60)
def load_trading_data(timeframe='24h'):
    """Carica i dati dal database con gestione degli errori"""
    try:
        session = get_database_session()
        interval = {
            '1h': "INTERVAL '1 hour'",
            '24h': "INTERVAL '24 hours'",
            '7d': "INTERVAL '7 days'",
            '30d': "INTERVAL '30 days'"
        }

        query = text(f"""
            SELECT 
                symbol,
                price,
                volume,
                timestamp
            FROM trading_data 
            WHERE timestamp > NOW() - {interval[timeframe]}
            ORDER BY timestamp DESC
        """)

        df = pd.read_sql(query, session.bind)
        session.remove()
        return df
    except Exception as e:
        logger.error(f"Errore nel caricamento dei dati: {str(e)}")
        return pd.DataFrame()

def create_price_chart(data, symbol):
    """Crea grafico prezzi interattivo"""
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=data['timestamp'],
            open=data['price'],
            high=data['price'],
            low=data['price'],
            close=data['price'],
            name='Prezzo'
        )
    )
    fig.update_layout(
        title=f'Andamento Prezzo {symbol}',
        yaxis_title='Prezzo (USDT)',
        template='plotly_dark',
        height=500
    )
    return fig

def create_volume_chart(data, symbol):
    """Crea grafico volume interattivo"""
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=data['timestamp'],
            y=data['volume'],
            name='Volume'
        )
    )
    fig.update_layout(
        title=f'Volume Trading {symbol}',
        yaxis_title='Volume (USDT)',
        template='plotly_dark',
        height=300
    )
    return fig

def main():
    """Funzione principale dell'applicazione"""
    initialize_session_state()

    # Sidebar
    st.sidebar.title("🤖 AurumBot")
    timeframe = st.sidebar.selectbox(
        "Intervallo temporale",
        options=['1h', '24h', '7d', '30d'],
        index=1
    )

    # Header principale
    st.title("📊 Trading Dashboard")

    # Carica dati
    data = load_trading_data(timeframe)

    if not data.empty:
        # Metriche principali
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Simboli Monitorati", len(data['symbol'].unique()))
        with col2:
            st.metric("Transazioni", len(data))
        with col3:
            latest_price = data.iloc[0]['price'] if not data.empty else 0
            st.metric("Ultimo Prezzo", f"${latest_price:,.2f}")
        with col4:
            last_update = data['timestamp'].max()
            st.metric("Ultimo Aggiornamento", last_update.strftime('%H:%M:%S'))

        # Selezione simbolo
        symbol = st.selectbox("Seleziona Simbolo", sorted(data['symbol'].unique()))

        # Filtra dati per simbolo
        symbol_data = data[data['symbol'] == symbol].copy()

        if not symbol_data.empty:
            # Grafici
            st.plotly_chart(create_price_chart(symbol_data, symbol), use_container_width=True)
            st.plotly_chart(create_volume_chart(symbol_data, symbol), use_container_width=True)

            # Statistiche dettagliate
            with st.expander("📈 Statistiche Dettagliate"):
                stats_col1, stats_col2 = st.columns(2)
                with stats_col1:
                    price_change = symbol_data['price'].iloc[0] - symbol_data['price'].iloc[-1]
                    price_change_pct = (price_change / symbol_data['price'].iloc[-1]) * 100
                    st.metric(
                        "Variazione Prezzo",
                        f"${price_change:.2f}",
                        f"{price_change_pct:.1f}%"
                    )
                with stats_col2:
                    volume_total = symbol_data['volume'].sum()
                    st.metric("Volume Totale", f"${volume_total:,.2f}")
    else:
        st.info("📊 Raccolta dati in corso... Il trading bot sta inizializzando il monitoraggio del mercato.")

    # Aggiornamento automatico
    if (datetime.now() - st.session_state.last_update).seconds > 60:
        st.session_state.last_update = datetime.now()
        st.rerun()

if __name__ == "__main__":
    main()