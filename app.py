import streamlit as st
import pandas as pd
from datetime import datetime
import logging
import sys
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_option_menu import option_menu
from streamlit_autorefresh import st_autorefresh

from utils.data_loader import CryptoDataLoader
from utils.auto_trader import AutoTrader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('streamlit_app.log')
    ]
)
logger = logging.getLogger(__name__)

# Page config must be first Streamlit command
st.set_page_config(
    page_title="AurumBot Trading",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto refresh
st_autorefresh(interval=5000, key="datarefresh")

# Initialize session state
if 'bot_running' not in st.session_state:
    st.session_state.bot_running = False
if 'selected_strategy' not in st.session_state:
    st.session_state.selected_strategy = 'scalping'
if 'auto_trader' not in st.session_state:
    st.session_state.auto_trader = None

try:
    # Sidebar
    with st.sidebar:
        st.title("🤖 AurumBot")

        selected = option_menu(
            menu_title=None,
            options=["Dashboard", "Strategy Config", "Performance", "Settings"],
            icons=['house', 'gear', 'graph-up', 'sliders'],
            menu_icon="cast",
            default_index=0,
        )

        st.subheader("Trading Settings")
        initial_balance = st.number_input("Initial Balance (USDT)", value=1000.0, step=100.0)
        risk_per_trade = st.slider("Risk per Trade (%)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)

        strategy = st.selectbox(
            "Trading Strategy",
            ['Scalping', 'DEX Sniping', 'Meme Coin']
        )

        # Testnet indicator
        st.markdown("---")
        st.info("🔒 Running in Testnet Mode")

    # Main content
    if selected == "Dashboard":
        st.title("Trading Dashboard")

        # Market selection
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            symbol = st.selectbox("Trading Pair", ["BTC-USDT", "ETH-USDT", "SOL-USDT"])
        with col2:
            timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"])
        with col3:
            if st.button("Start Bot" if not st.session_state.bot_running else "Stop Bot"):
                try:
                    if not st.session_state.bot_running:
                        # Initialize bot with testnet mode
                        st.session_state.auto_trader = AutoTrader(
                            symbol=symbol,
                            initial_balance=initial_balance,
                            risk_per_trade=risk_per_trade/100,
                            testnet=True
                        )
                        st.session_state.bot_running = True
                        st.success("Bot started in testnet mode")
                        logger.info("Trading bot initialized in testnet mode")
                    else:
                        st.session_state.bot_running = False
                        st.session_state.auto_trader = None
                        st.info("Bot stopped")
                        logger.info("Trading bot stopped")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    logger.error(f"Bot initialization error: {str(e)}")
                    st.session_state.bot_running = False
                    st.session_state.auto_trader = None

        try:
            # Market data visualization
            data_loader = CryptoDataLoader(testnet=True)
            df = data_loader.get_historical_data(symbol, period='1d', interval=timeframe)

            if df is not None and not df.empty:
                # Create subplot with secondary y-axis
                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.03,
                    row_heights=[0.7, 0.3]
                )

                # Candlestick chart
                fig.add_trace(
                    go.Candlestick(
                        x=df.index,
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        name="OHLC"
                    ),
                    row=1, col=1
                )

                # Volume bars
                colors = ['red' if row['Open'] > row['Close'] else 'green' for index, row in df.iterrows()]
                fig.add_trace(
                    go.Bar(
                        x=df.index,
                        y=df['Volume'],
                        name="Volume",
                        marker_color=colors,
                        opacity=0.5
                    ),
                    row=2, col=1
                )

                fig.update_layout(
                    height=600,
                    template='plotly_dark',
                    xaxis_rangeslider_visible=False,
                    title=f"{symbol} - {timeframe}"
                )

                st.plotly_chart(fig, use_container_width=True)

                # Trading metrics
                col1, col2, col3, col4 = st.columns(4)
                current_price = df['Close'].iloc[-1]
                price_change = ((current_price - df['Open'].iloc[-1]) / df['Open'].iloc[-1] * 100)

                col1.metric("Current Price", f"${current_price:,.2f}", f"{price_change:.2f}%")
                col2.metric("24h Volume", f"${df['Volume'].sum():,.0f}")
                col3.metric("Open Positions", "0" if not st.session_state.bot_running else "Active")
                col4.metric("P/L", "+$0.00", "0.00%")

            else:
                st.warning("No data available for the selected trading pair")

        except Exception as e:
            st.error(f"Error loading market data: {str(e)}")
            logger.error(f"Market data error: {str(e)}")

    elif selected == "Strategy Config":
        st.title("Strategy Configuration")

        # Strategy specific parameters
        if strategy == "Scalping":
            col1, col2 = st.columns(2)
            with col1:
                st.number_input("Volume Threshold", value=1000000)
                st.number_input("Min Volatility", value=0.002, format="%.4f")
            with col2:
                st.number_input("Profit Target", value=0.005, format="%.4f")
                st.number_input("Stop Loss", value=0.003, format="%.4f")

        elif strategy == "DEX Sniping":
            col1, col2 = st.columns(2)
            with col1:
                st.number_input("Min Liquidity (ETH)", value=5)
                st.number_input("Max Buy Tax (%)", value=10)
            with col2:
                st.number_input("Min Holders", value=50)
                st.text_input("RPC URL", value="https://data-seed-prebsc-1-s1.binance.org:8545/")

        elif strategy == "Meme Coin":
            col1, col2 = st.columns(2)
            with col1:
                st.number_input("Sentiment Threshold", value=0.75, format="%.2f")
                st.number_input("Volume Increase (%)", value=200)
            with col2:
                st.number_input("Max Entry Price", value=0.01, format="%.4f")
                st.number_input("Min Social Score", value=7.5, format="%.1f")

    elif selected == "Performance":
        st.title("Performance Analytics")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Profit/Loss", "$0.00")
        col2.metric("Win Rate", "0%")
        col3.metric("Total Trades", "0")
        col4.metric("Avg. Trade Duration", "0m")

        st.line_chart(pd.DataFrame({'balance': [initial_balance]*10}))

    elif selected == "Settings":
        st.title("Bot Settings")

        api_col1, api_col2 = st.columns(2)
        with api_col1:
            st.text_input("API Key (Testnet)", type="password")
        with api_col2:
            st.text_input("API Secret (Testnet)", type="password")

        st.subheader("Notifications")
        notify_trades = st.checkbox("Trade Notifications", value=True)
        notify_errors = st.checkbox("Error Notifications", value=True)

        st.subheader("Risk Management")
        max_trades = st.slider("Max Concurrent Trades", 1, 10, 3)
        max_daily_trades = st.slider("Max Daily Trades", 5, 50, 20)

except Exception as e:
    st.error(f"Application error: {str(e)}")
    logger.error(f"Critical error: {str(e)}")

# Custom styling
st.markdown("""
    <style>
    .reportview-container {
        background: #0E1117
    }
    .sidebar .sidebar-content {
        background: #262730
    }
    .stApp {
        background: #0E1117
    }
    </style>
    """, unsafe_allow_html=True)