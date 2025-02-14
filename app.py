import logging
import os
import sys
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.auto_trader import AutoTrader
from utils.data_loader import CryptoDataLoader
from utils.test_suite import AurumBotTester

# Basic logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Initialize session state
if 'bot' not in st.session_state:
    st.session_state.bot = None
if 'data_loader' not in st.session_state:
    st.session_state.data_loader = None
if 'start_time' not in st.session_state:
    st.session_state.start_time = datetime.now()
if 'error_count' not in st.session_state:
    st.session_state.error_count = 0

def create_candlestick_chart(df):
    """Create an interactive candlestick chart"""
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
            xaxis_rangeslider_visible=False
        )

        return fig
    except Exception as e:
        logger.error(f"Chart creation error: {str(e)}")
        return None

def main():
    # Page config
    st.set_page_config(
        page_title="AurumBot Trading Platform",
        page_icon="🤖",
        layout="wide"
    )

    # Title and description
    st.title("🤖 AurumBot Trading Platform")
    st.markdown("""
    Advanced crypto trading platform with intelligent automation and sophisticated backtesting capabilities.
    """)

    # Sidebar
    with st.sidebar:
        st.title("Trading Controls")

        # Trading pair selection
        trading_pair = st.selectbox(
            "Select Trading Pair",
            ["BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT", "SHIB/USDT"],
            index=0
        )

        # Strategy selection
        strategy = st.selectbox(
            "Trading Strategy",
            ["scalping", "swing", "meme_coin"],
            index=0
        )

        # Trading parameters
        initial_balance = st.number_input(
            "Initial Balance (USDT)",
            min_value=10.0,
            value=1000.0,
            step=10.0
        )

        risk_per_trade = st.slider(
            "Risk Per Trade (%)",
            min_value=0.1,
            max_value=5.0,
            value=2.0,
            step=0.1
        )

        # Start/Stop buttons
        if st.button("Start Trading"):
            try:
                st.session_state.bot = AutoTrader(
                    symbol=trading_pair,
                    initial_balance=initial_balance,
                    risk_per_trade=risk_per_trade/100,
                    testnet=True
                )
                st.session_state.data_loader = CryptoDataLoader(testnet=True)
                st.success(f"Bot initialized for {trading_pair}")
            except Exception as e:
                st.error(f"Failed to start trading: {str(e)}")
                st.session_state.error_count += 1
                logger.error(f"Bot initialization error: {str(e)}")

        if st.button("Stop Trading") and st.session_state.bot:
            st.session_state.bot = None
            st.session_state.data_loader = None
            st.info("Trading stopped")

    # Main content tabs
    tab1, tab2 = st.tabs(["Market Analysis", "Performance"])

    # Market Analysis Tab
    with tab1:
        if st.session_state.bot and st.session_state.data_loader:
            try:
                df = st.session_state.data_loader.get_historical_data(
                    st.session_state.bot.symbol,
                    period='1d'
                )

                if df is not None and not df.empty:
                    # Price chart
                    chart = create_candlestick_chart(df)
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)

                    # Market metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Current Price", f"${df['Close'].iloc[-1]:.2f}")
                    with col2:
                        price_change = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
                        st.metric("24h Change", f"{price_change:.2f}%")
                    with col3:
                        st.metric("24h Volume", f"${df['Volume'].sum():,.0f}")
                else:
                    st.warning("No market data available")
            except Exception as e:
                st.error("Failed to load market data")
                logger.error(f"Market data error: {str(e)}")
        else:
            st.info("Start trading to see market analysis")

    # Performance Tab
    with tab2:
        if st.session_state.bot:
            # Portfolio status
            st.subheader("Portfolio Status")
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Current Balance", f"${st.session_state.bot.balance:.2f}")
                profit_loss = st.session_state.bot.balance - st.session_state.bot.initial_balance
                st.metric("Total P/L", f"${profit_loss:.2f}")

            with col2:
                if st.session_state.bot.is_in_position:
                    st.info("Active Trade in Progress")
                    if st.session_state.bot.current_position:
                        st.json(st.session_state.bot.current_position)
        else:
            st.info("Start trading to see performance metrics")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("An unexpected error occurred. Please try refreshing the page.")
        logger.error(f"Application error: {str(e)}")