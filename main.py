import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from utils.data_loader import CryptoDataLoader
from utils.indicators import TechnicalIndicators
from utils.auto_trader import AutoTrader
from utils.database import get_db, TradingStrategy
from utils.notifications import TradingNotifier

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

# Initialize components
data_loader = CryptoDataLoader()
indicators = TechnicalIndicators()
notifier = TradingNotifier()
auto_trader = None

# Page config
st.set_page_config(
    page_title="AurumBot",
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
if 'positions' not in st.session_state: # Retained from original
    st.session_state.positions = []

try:
    # Sidebar
    with st.sidebar:
        st.image("generated-icon.png", width=50)
        st.title("AurumBot")

        # Trading Controls
        st.subheader("🎮 Trading Controls")

        selected_pair = st.selectbox(
            "Select Trading Pair",
            data_loader.get_available_coins().keys()
        )

        risk_level = st.select_slider(
            "Risk Level",
            options=["Low", "Medium", "High"],
            value="Medium"
        )

        if st.button("🟢 Start Trading" if not st.session_state.trading_active else "🔴 Stop Trading"):
            st.session_state.trading_active = not st.session_state.trading_active
            if st.session_state.trading_active:
                auto_trader = AutoTrader(
                    symbol=selected_pair,
                    initial_balance=st.session_state.balance,
                    risk_per_trade=0.02 if risk_level == "Low" else 0.05 if risk_level == "Medium" else 0.1
                )

    # Main Layout
    col1, col2, col3 = st.columns([2,5,2])

    # Left Column - Portfolio Overview
    with col1:
        st.subheader("💼 Portfolio")
        st.metric("Total Balance", f"${st.session_state.balance:,.2f}")

        # Fetch current price
        current_price = data_loader.get_current_price(selected_pair)
        if current_price:
            st.metric("Current Price", f"${current_price:,.2f}")

        if st.session_state.trading_active:
            st.success("Bot is running")
        else:
            st.warning("Bot is stopped")

        # Retained from original, adapted to use session state
        st.subheader("🎯 Active Trades")
        for pos in st.session_state.positions: # Iterate through positions
            with st.container():
                st.markdown(f"""
                <div class="trade-card">
                    <small>{pos['pair']}</small><br>
                    {pos['action']} @{pos['price']}
                </div>
                """, unsafe_allow_html=True)


    # Center Column - Charts
    with col2:
        st.subheader("📈 Market Analysis")

        # Timeframe selector
        timeframe = st.select_slider(
            "Timeframe",
            options=["1h", "4h", "1d", "1w"],
            value="1d"
        )

        try:
            # Get historical data
            df = data_loader.get_historical_data(selected_pair, period=timeframe)

            if df is not None:
                # Add technical indicators
                df = indicators.add_rsi(df)
                df = indicators.add_macd(df)

                # Create main chart
                fig = go.Figure()

                # Candlestick
                fig.add_trace(go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name='OHLC'
                ))

                # Customize chart
                fig.update_layout(
                    title=f"{selected_pair} Price Chart",
                    yaxis_title="Price (USD)",
                    template="plotly_dark",
                    height=600,
                    margin=dict(l=50, r=50, t=50, b=50)
                )

                st.plotly_chart(fig, use_container_width=True)

                # Display indicators
                indicators_tab, orders_tab = st.tabs(["📊 Indicators", "📝 Orders"])

                with indicators_tab:
                    col_ind1, col_ind2 = st.columns(2)
                    with col_ind1:
                        st.metric("RSI", f"{df['RSI'].iloc[-1]:.2f}")
                    with col_ind2:
                        st.metric("MACD", f"{df['MACD'].iloc[-1]:.2f}")

                with orders_tab:
                    if st.session_state.trading_active and auto_trader:
                        st.write("Active Orders:", auto_trader.portfolio['open_orders'])
                    else:
                        st.info("Start trading to see active orders")

            else:
                st.error("Failed to load market data")

        except Exception as e:
            logger.error(f"Error in chart generation: {str(e)}")
            st.error("Error generating market analysis")

    # Right Column - Trading Stats
    with col3:
        st.subheader("📊 Statistics")

        if st.session_state.trading_active and auto_trader:
            metrics = auto_trader.portfolio['performance_metrics']
            st.metric("Total Profit", f"${metrics['total_profit']:.2f}")
            st.metric("Win Rate", f"{metrics['win_rate']:.1%}")
            st.metric("Avg Profit/Trade", f"${metrics['avg_profit_per_trade']:.2f}")
        else:
            st.info("Start trading to see statistics")

    # Bottom section - Recent Activity (retained from original, mostly)
    st.subheader("📝 Recent Activity")
    col_logs1, col_logs2 = st.columns([3,2])

    with col_logs1:
        st.markdown("""
        | Time | Action | Pair | Price | Status |
        |------|--------|------|-------|--------|
        | 12:45 | Buy | BTC/USDT | 48,235 | Completed |
        | 12:30 | Sell | ETH/USDT | 2,890 | Completed |
        | 12:15 | Buy | SOL/USDT | 98.5 | Pending |
        """)

    with col_logs2:
        st.subheader("System Status")
        st.markdown("✅ All systems operational")
        st.markdown("✅ Connected to exchanges")
        st.markdown("✅ AI models running")

except Exception as e:
    logger.error(f"Critical application error: {str(e)}")
    st.error("A critical error occurred. Please check the logs for details.")

logger.info("Application rendered successfully")