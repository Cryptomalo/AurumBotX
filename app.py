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
import json
from pathlib import Path

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('streamlit_app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Inizializzazione stato sessione
def init_session_state():
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

def render_backup_controls():
    """Visualizza i controlli per la gestione dei backup"""
    try:
        if not st.session_state.bot:
            st.info("Avvia il trading bot per gestire i backup")
            return

        st.subheader("Gestione Backup")

        # Lista dei backup disponibili
        try:
            backups = st.session_state.bot.backup_manager.list_backups()
        except Exception as e:
            st.error(f"Errore nel caricamento dei backup: {str(e)}")
            return

        if backups:
            # Mostra i backup disponibili
            selected_backup = st.selectbox(
                "Backup Disponibili",
                options=[b['timestamp'] for b in backups],
                format_func=lambda x: f"Backup del {datetime.strptime(x, '%Y%m%d_%H%M%S').strftime('%d/%m/%Y %H:%M:%S')}"
            )

            # Mostra dettagli del backup selezionato
            if selected_backup:
                try:
                    backup_path = Path("backup") / selected_backup
                    log_file = backup_path / "BACKUP_LOG.md"
                    if log_file.exists():
                        with open(log_file, "r") as f:
                            st.markdown(f.read())

                    # Pulsante di ripristino
                    if st.button("🔄 Ripristina Configurazione"):
                        with st.spinner("Ripristino configurazione in corso..."):
                            if st.session_state.bot.restore_config(selected_backup):
                                st.success("Configurazione ripristinata con successo!")
                            else:
                                st.error("Errore durante il ripristino della configurazione")
                except Exception as e:
                    st.error(f"Errore nel caricamento dei dettagli del backup: {str(e)}")

            # Pulizia backup
            st.markdown("---")
            max_backups = st.slider(
                "Numero massimo di backup da mantenere",
                min_value=1,
                max_value=50,
                value=10
            )
            if st.button("🧹 Pulisci Backup Vecchi"):
                with st.spinner("Pulizia backup in corso..."):
                    try:
                        st.session_state.bot.backup_manager.cleanup_old_backups(max_backups)
                        st.success(f"Mantenuti gli ultimi {max_backups} backup")
                    except Exception as e:
                        st.error(f"Errore durante la pulizia dei backup: {str(e)}")
        else:
            st.info("Nessun backup disponibile")

    except Exception as e:
        st.error(f"Errore nella gestione dei backup: {str(e)}")
        logger.error(f"Errore backup: {str(e)}")

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

        # Titolo e descrizione
        st.title("🤖 AurumBot Trading Platform")
        st.markdown("""
        Piattaforma avanzata di trading crypto con automazione intelligente e backtesting sofisticato.
        """)

        # Sidebar
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

            # Pulsanti Start/Stop
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ Avvia"):
                    try:
                        st.session_state.bot = AutoTrader(
                            symbol=trading_pair,
                            initial_balance=initial_balance,
                            risk_per_trade=risk_per_trade/100,
                            testnet=True
                        )
                        st.session_state.data_loader = CryptoDataLoader(testnet=True)
                        st.session_state.bot.backup_manager = BackupManager() # Assuming this is how BackupManager is initialized
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

        # Tab contenuto principale
        tab1, tab2, tab3 = st.tabs(["Analisi Mercato", "Performance", "Backup"])

        # Tab Analisi Mercato
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

        # Tab Performance
        with tab2:
            if st.session_state.bot:
                render_portfolio_status()
            else:
                st.info("Avvia il trading per vedere le metriche di performance")

        # Backup Tab
        with tab3:
            render_backup_controls()

    except Exception as e:
        st.error("Si è verificato un errore imprevisto. Ricarica la pagina.")
        logger.error(f"Errore applicazione: {str(e)}")

if __name__ == "__main__":
    main()