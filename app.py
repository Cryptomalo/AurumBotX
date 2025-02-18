import logging
import os
import sys
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.auto_trader import AutoTrader
from utils.data_loader import CryptoDataLoader
from utils.backup_manager import BackupManager
from components.login import render_login_page
import json
from pathlib import Path

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system/app.log', mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('streamlit').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def init_session_state():
    """Inizializza lo stato della sessione"""
    if 'bot' not in st.session_state:
        st.session_state.bot = None
    if 'data_loader' not in st.session_state:
        st.session_state.data_loader = None
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()
    if 'error_count' not in st.session_state:
        st.session_state.error_count = 0
    if 'market_data' not in st.session_state:
        st.session_state.market_data = None
    if 'user' not in st.session_state:
        st.session_state.user = {'authenticated': False}


def show_main_app():
    """Mostra l'applicazione principale"""
    # Se l'utente non è autenticato con il wallet, mostra solo la pagina di login
    if 'user' not in st.session_state or not st.session_state['user'].get('authenticated'):
        render_login_page()
        return

    st.title("🌟 AurumBot Trading Platform")
    st.markdown("""
    Piattaforma avanzata di trading crypto con automazione intelligente e backtesting sofisticato.
    """)

    # Sidebar con controlli trading
    with st.sidebar:
        st.title("Controlli Trading")

        # Selezione coppia trading
        trading_pair = st.selectbox(
            "Seleziona Coppia Trading",
            ["BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT", "SHIB/USDT"],
            index=0
        )

        # Selezione strategia
        strategy = st.selectbox(
            "Strategia Trading",
            ["scalping", "swing", "meme_coin"],
            index=0
        )

        # Parametri trading
        initial_balance = st.number_input(
            "Bilancio Iniziale (USDT)",
            min_value=10.0,
            value=1000.0,
            step=10.0
        )

        risk_per_trade = st.slider(
            "Rischio per Trade (%)",
            min_value=0.1,
            max_value=5.0,
            value=2.0,
            step=0.1
        )

        testnet_mode = st.checkbox("Modalità Testnet", value=True)

        # Pulsanti Start/Stop
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Avvia"):
                try:
                    st.session_state.bot = AutoTrader(
                        symbol=trading_pair,
                        initial_balance=initial_balance,
                        risk_per_trade=risk_per_trade/100,
                        testnet=testnet_mode
                    )
                    st.session_state.data_loader = CryptoDataLoader(testnet=True)
                    st.session_state.bot.backup_manager = BackupManager()
                    st.success(f"Bot inizializzato per {trading_pair}")
                except Exception as e:
                    st.error(f"Errore avvio: {str(e)}")
                    st.session_state.error_count += 1
                    logger.error(f"Errore inizializzazione bot: {str(e)}")

        with col2:
            if st.button("⏹️ Ferma"):
                st.session_state.bot = None
                st.session_state.data_loader = None
                st.info("Trading fermato")

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Analisi Mercato",
        "🤖 Auto Trading", 
        "💼 Portfolio",
        "🔗 Social Connections"
    ])

    # Tab contenuti
    with tab1:
        if st.session_state.bot and st.session_state.data_loader:
            df = load_market_data(st.session_state.bot.symbol)
            if df is not None:
                chart = create_candlestick_chart(df)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
                render_market_metrics(df)
            else:
                st.warning("Dati di mercato non disponibili")
        else:
            st.info("Avvia il trading per vedere l'analisi di mercato")

    with tab2:
        if st.session_state.bot:
            render_portfolio_status()
        else:
            st.info("Avvia il trading per accedere al trading automatico")

    with tab3:
        if st.session_state.bot:
            render_portfolio_status()
        else:
            st.info("Avvia il trading per vedere il portfolio")

    with tab4:
        render_login_page()

def create_candlestick_chart(df):
    """Crea un grafico candlestick interattivo"""
    try:
        if df is None or df.empty:
            return None

        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close']
        )])

        fig.update_layout(
            title='Price Chart',
            yaxis_title='Price',
            template='plotly_dark',
            xaxis_rangeslider_visible=False,
            height=600
        )

        return fig
    except Exception as e:
        logger.error(f"Errore creazione grafico: {str(e)}")
        return None

def load_market_data(symbol, period='1d'):
    """Carica i dati di mercato in modo sicuro"""
    try:
        if not st.session_state.data_loader:
            return None

        df = st.session_state.data_loader.get_historical_data(symbol, period)
        if df is not None and not df.empty:
            st.session_state.market_data = df
            return df
        return None
    except Exception as e:
        logger.error(f"Errore caricamento dati: {str(e)}")
        return None

def render_market_metrics(df):
    """Visualizza le metriche di mercato"""
    try:
        if df is None or df.empty:
            st.warning("Dati di mercato non disponibili")
            return

        col1, col2, col3 = st.columns(3)
        with col1:
            current_price = df['Close'].iloc[-1]
            st.metric("Prezzo Attuale", f"${current_price:.2f}")

        with col2:
            price_change = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
            st.metric("Variazione 24h", f"{price_change:.2f}%")

        with col3:
            volume = df['Volume'].sum()
            st.metric("Volume 24h", f"${volume:,.0f}")

    except Exception as e:
        logger.error(f"Errore visualizzazione metriche: {str(e)}")
        st.error("Errore nel calcolo delle metriche")

def render_portfolio_status():
    """Visualizza lo stato del portfolio"""
    try:
        if not st.session_state.bot:
            return

        st.subheader("Stato Portfolio")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Bilancio Attuale", f"${st.session_state.bot.balance:.2f}")
            profit_loss = st.session_state.bot.balance - st.session_state.bot.initial_balance
            st.metric("P/L Totale", f"${profit_loss:.2f}")

        with col2:
            if st.session_state.bot.is_in_position:
                st.info("Trade Attivo")
                if st.session_state.bot.current_position:
                    position = st.session_state.bot.current_position
                    st.json({
                        "Prezzo Entrata": f"${position['entry_price']:.2f}",
                        "Dimensione": f"{position['size']:.6f}",
                        "Strategia": position['strategy'],
                        "Target": f"${position['target_price']:.2f}",
                        "Stop Loss": f"${position['stop_loss']:.2f}"
                    })
    except Exception as e:
        logger.error(f"Errore visualizzazione portfolio: {str(e)}")
        st.error("Errore nell'aggiornamento del portfolio")

def main():
    try:
        # Configurazione pagina
        st.set_page_config(
            page_title="AurumBot Trading Platform",
            page_icon="🤖",
            layout="wide"
        )

        # Inizializzazione stato
        init_session_state()

        # Mostra direttamente l'app principale
        show_main_app()

    except Exception as e:
        st.error("Si è verificato un errore imprevisto. Ricarica la pagina.")
        logger.error(f"Errore applicazione: {str(e)}")

if __name__ == "__main__":
    main()