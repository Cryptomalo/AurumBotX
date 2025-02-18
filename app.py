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
import asyncio
import nest_asyncio

# Enable nested event loops for Streamlit
nest_asyncio.apply()

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

async def initialize_bot_and_loader(trading_pair: str, initial_balance: float, risk_per_trade: float, testnet_mode: bool):
    """Inizializza il bot e il data loader in modo asincrono"""
    try:
        bot = AutoTrader(
            symbol=trading_pair,
            initial_balance=initial_balance,
            risk_per_trade=risk_per_trade/100,
            testnet=testnet_mode
        )
        data_loader = CryptoDataLoader(testnet=testnet_mode)
        await data_loader.initialize()
        bot.backup_manager = BackupManager()

        # Carica i dati iniziali
        df = await data_loader.get_historical_data(trading_pair, '1d')
        if df is not None and not df.empty:
            st.session_state.market_data = df
            st.session_state.bot = bot
            st.session_state.data_loader = data_loader
            return True
        else:
            st.warning("Impossibile caricare i dati iniziali. Riprova tra qualche secondo.")
            return False
    except Exception as e:
        logger.error(f"Errore inizializzazione: {str(e)}")
        st.error(f"Errore avvio: {str(e)}")
        return False

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
    if 'initialization_running' not in st.session_state:
        st.session_state.initialization_running = False

def show_main_app():
    """Mostra l'applicazione principale"""
    if 'user' not in st.session_state or not st.session_state['user'].get('authenticated'):
        render_login_page()
        return

    st.title("🌟 AurumBot Trading Platform")
    st.markdown("""
    Piattaforma avanzata di trading crypto con automazione intelligente e backtesting sofisticato.
    """)

    with st.sidebar:
        st.title("Controlli Trading")
        trading_pair = st.selectbox(
            "Seleziona Coppia Trading",
            ["BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT", "SHIB/USDT"],
            index=0
        )
        strategy = st.selectbox(
            "Strategia Trading",
            ["scalping", "swing", "meme_coin"],
            index=0
        )
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

        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Avvia"):
                if not st.session_state.initialization_running:
                    st.session_state.initialization_running = True
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        success = loop.run_until_complete(initialize_bot_and_loader(
                            trading_pair, initial_balance, risk_per_trade, testnet_mode
                        ))
                        loop.close()
                        if success:
                            st.success(f"Bot inizializzato per {trading_pair}")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Errore durante l'avvio: {str(e)}")
                        logger.error(f"Errore durante l'avvio: {str(e)}")
                    finally:
                        st.session_state.initialization_running = False

        with col2:
            if st.button("⏹️ Ferma"):
                st.session_state.bot = None
                st.session_state.data_loader = None
                st.info("Trading fermato")
                st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Analisi Mercato",
        "🤖 Auto Trading", 
        "💼 Portfolio",
        "🔗 Social Connections"
    ])

    with tab1:
        if st.session_state.bot and st.session_state.market_data is not None:
            df = st.session_state.market_data
            chart = create_candlestick_chart(df)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
            render_market_metrics(df)
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
        st.set_page_config(
            page_title="AurumBot Trading Platform",
            page_icon="🤖",
            layout="wide"
        )
        init_session_state()
        show_main_app()
    except Exception as e:
        logger.error(f"Errore applicazione: {str(e)}")
        st.error("Si è verificato un errore imprevisto. Ricarica la pagina.")

if __name__ == "__main__":
    main()