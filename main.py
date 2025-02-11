import os
from datetime import datetime, timedelta
import logging

# Data processing and visualization
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Local imports
from utils.data_loader import CryptoDataLoader
from utils.indicators import TechnicalIndicators
from utils.notifications import TradingNotifier
from utils.auto_trader import AutoTrader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'app_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configurazione pagina
st.set_page_config(
    page_title="AurumBot Trading Platform",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'trading_active' not in st.session_state:
    st.session_state.trading_active = False
if 'selected_strategy' not in st.session_state:
    st.session_state.selected_strategy = None
if 'balance' not in st.session_state:
    st.session_state.balance = 10000.0
if 'positions' not in st.session_state:
    st.session_state.positions = []

def show_dashboard():
    """Display the main dashboard"""
    try:
        st.title("🌟 AurumBot Trading Platform")

        # Initialize components
        data_loader = CryptoDataLoader()
        indicators = TechnicalIndicators()
        notifier = TradingNotifier()

        # Sidebar Navigation
        page = st.sidebar.radio(
            "Navigation",
            ["Dashboard", "Trade", "History", "Settings"]
        )

        if page == "Dashboard":
            st.header("Trading Dashboard")

            # Portfolio Overview
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Portfolio Value", f"${st.session_state.balance:,.2f}", "+5.2%")
            with col2:
                st.metric("24h Change", "+$521.43", "+5.21%")
            with col3:
                st.metric("Active Positions", len(st.session_state.positions))

            # Market Analysis Section
            st.subheader("Market Analysis")
            coins = data_loader.get_available_coins()
            if not coins:
                st.error("Unable to load available trading pairs")
                return

            selected_pair = st.selectbox(
                "Select Trading Pair",
                coins.keys()
            )

            risk_level = st.select_slider(
                "Risk Level",
                options=["Low", "Medium", "High"],
                value="Medium"
            )

            # Trading Controls
            trading_col1, trading_col2 = st.columns([2, 1])
            with trading_col1:
                if st.button("🟢 Start Trading" if not st.session_state.trading_active else "🔴 Stop Trading"):
                    st.session_state.trading_active = not st.session_state.trading_active

            with trading_col2:
                timeframe = st.selectbox(
                    "Timeframe",
                    ["1h", "4h", "1d", "1w"],
                    index=2
                )

            # Get and display market data
            with st.spinner('Loading market data...'):
                df = data_loader.get_historical_data(selected_pair, period=timeframe)

                if df is not None and not df.empty:
                    # Add technical indicators
                    df = indicators.add_rsi(df)
                    df = indicators.add_macd(df)

                    # Create main chart
                    fig = go.Figure(data=[go.Candlestick(
                        x=df.index,
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close']
                    )])

                    fig.update_layout(
                        title=f"{selected_pair} Price Chart",
                        yaxis_title="Price (USD)",
                        template="plotly_dark",
                        height=600
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Technical Indicators
                    indicator_col1, indicator_col2 = st.columns(2)
                    with indicator_col1:
                        st.metric("RSI", f"{df['RSI'].iloc[-1]:.2f}")
                    with indicator_col2:
                        st.metric("MACD", f"{df['MACD'].iloc[-1]:.2f}")

                    # Trading Stats
                    st.subheader("📊 Statistics")
                    if st.session_state.trading_active:
                        stats_col1, stats_col2, stats_col3 = st.columns(3)
                        with stats_col1:
                            st.metric("Win Rate", "65%")
                        with stats_col2:
                            st.metric("Total Trades", "24")
                        with stats_col3:
                            st.metric("Profit/Loss", "+$1,234.56")
                    else:
                        st.info("Start trading to see statistics")
                else:
                    st.error("Failed to load market data")

        elif page == "Trade":
            st.title("Manual Trading")
            st.info("Trading interface coming soon...")

        elif page == "History":
            st.title("Trading History")
            st.info("Trading history coming soon...")

        elif page == "Settings":
            st.title("Settings")
            st.info("Settings panel coming soon...")

    except Exception as e:
        logger.error(f"Error in dashboard: {str(e)}")
        st.error("Si è verificato un errore nel caricamento della dashboard")

def main():
    """Main application function"""
    try:
        show_dashboard()
    except Exception as e:
        logger.error(f"Critical error in main: {e}")
        st.error("Si è verificato un errore critico. Riprova più tardi.")

if __name__ == "__main__":
    main()