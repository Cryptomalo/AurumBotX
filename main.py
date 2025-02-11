import os
import logging
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

from utils.data_loader import CryptoDataLoader
from utils.indicators import TechnicalIndicators
from utils.wallet_manager import WalletManager
from utils.auto_trader import AutoTrader
from utils.notifications import TradingNotifier

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger(__name__)

logger.info("Starting AurumBot Trading Platform...")

try:
    logger.info("Setting up page configuration...")
    # Set page configuration
    st.set_page_config(
        page_title="AurumBot",
        page_icon="🌟",
        layout="wide"
    )

    # Initialize components
    logger.info("Initializing components...")
    data_loader = CryptoDataLoader()
    indicators = TechnicalIndicators()
    notifier = TradingNotifier()

    logger.info("Setting up sidebar...")
    # Sidebar configuration
    st.sidebar.title("🛠️ Trading Controls")

    # Select cryptocurrency
    selected_coin = st.sidebar.selectbox(
        "Select Cryptocurrency",
        options=list(data_loader.supported_coins.keys()),
        format_func=lambda x: f"{data_loader.supported_coins[x]} ({x})"
    )

    # Time period selector
    timeframe = st.sidebar.selectbox(
        "Select Timeframe",
        options=['1d', '7d', '30d', '90d'],
        format_func=lambda x: {
            '1d': '1 Day',
            '7d': '1 Week',
            '30d': '1 Month',
            '90d': '3 Months'
        }[x]
    )

    logger.info("Setting up main content...")
    # Main content
    st.title("🌟 AurumBot Trading Platform")

    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Market Analysis",
        "🤖 Auto Trading",
        "💼 Portfolio",
        "⚙️ Settings"
    ])

    with tab1:
        try:
            logger.info("Loading Market Analysis tab...")
            # Market Analysis Tab
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("Price Chart")
                # Get historical data
                logger.info(f"Fetching historical data for {selected_coin}")
                df = data_loader.get_historical_data(selected_coin, period=timeframe)

                if df is not None and not df.empty:
                    logger.info("Creating price chart...")
                    # Create candlestick chart
                    fig = go.Figure(data=[go.Candlestick(
                        x=df.index,
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close']
                    )])

                    fig.update_layout(
                        title=f"{data_loader.supported_coins[selected_coin]} Price Chart",
                        xaxis_title="Date",
                        yaxis_title="Price (USD)",
                        template="plotly_dark"
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Display technical indicators
                    st.subheader("Technical Indicators")
                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        if 'RSI' in df.columns:
                            st.metric(
                                "RSI",
                                f"{df['RSI'].iloc[-1]:.2f}",
                                f"{df['RSI'].iloc[-1] - df['RSI'].iloc[-2]:.2f}"
                            )

                    with col_b:
                        if 'MACD' in df.columns:
                            st.metric(
                                "MACD",
                                f"{df['MACD'].iloc[-1]:.2f}",
                                f"{df['MACD'].iloc[-1] - df['MACD'].iloc[-2]:.2f}"
                            )

                    with col_c:
                        if 'Volume' in df.columns:
                            st.metric(
                                "Volume",
                                f"{df['Volume'].iloc[-1]:,.0f}",
                                f"{((df['Volume'].iloc[-1] / df['Volume'].iloc[-2]) - 1) * 100:.1f}%"
                            )

            with col2:
                st.subheader("Market Overview")
                current_price = data_loader.get_current_price(selected_coin)

                if current_price and df is not None and not df.empty:
                    st.metric(
                        "Current Price",
                        f"${current_price:,.2f}",
                        f"{((df['Close'].iloc[-1] / df['Close'].iloc[-2]) - 1) * 100:.2f}%"
                    )

        except Exception as e:
            logger.error(f"Error in Market Analysis tab: {str(e)}")
            st.error("Error loading market data. Please try again later.")

    with tab2:
        try:
            logger.info("Loading Auto Trading tab...")
            # Auto Trading Tab
            st.subheader("Automated Trading Settings")

            col1, col2 = st.columns(2)

            with col1:
                risk_per_trade = st.slider(
                    "Risk per Trade (%)",
                    min_value=0.1,
                    max_value=5.0,
                    value=2.0,
                    step=0.1
                )

                initial_balance = st.number_input(
                    "Initial Balance (USD)",
                    min_value=100,
                    value=10000,
                    step=100
                )

            with col2:
                strategy = st.selectbox(
                    "Trading Strategy",
                    options=['Scalping', 'Swing Trading', 'Meme Coin Sniping']
                )

                test_mode = st.checkbox("Test Mode (Paper Trading)", value=True)

            if st.button("Start Auto Trading"):
                st.warning("Auto trading feature coming soon!")

        except Exception as e:
            logger.error(f"Error in Auto Trading tab: {str(e)}")
            st.error("Error loading trading settings. Please try again later.")

    with tab3:
        try:
            logger.info("Loading Portfolio tab...")
            # Portfolio Tab
            st.subheader("Portfolio Overview")
            # Placeholder for portfolio data
            st.info("Connect your wallet to view portfolio details")

            if st.button("Connect Wallet"):
                st.warning("Wallet connection feature coming soon!")

        except Exception as e:
            logger.error(f"Error in Portfolio tab: {str(e)}")
            st.error("Error loading portfolio. Please try again later.")

    with tab4:
        try:
            logger.info("Loading Settings tab...")
            # Settings Tab
            st.subheader("Platform Settings")

            # Notification settings
            st.write("📱 Notification Settings")
            enable_sms = st.checkbox("Enable SMS Notifications")
            if enable_sms:
                phone_number = st.text_input("Phone Number (with country code)")

                if st.button("Test Notifications"):
                    if notifier.setup(phone_number):
                        notifier.send_trade_notification(
                            "TEST",
                            selected_coin,
                            current_price,
                            0.0
                        )
                        st.success("Test notification sent!")
                    else:
                        st.error("Failed to setup notifications. Please check your phone number.")

        except Exception as e:
            logger.error(f"Error in Settings tab: {str(e)}")
            st.error("Error loading settings. Please try again later.")

    # Add version info
    st.sidebar.info("Version: 1.0.0")
    logger.info("Application setup completed successfully")

except Exception as e:
    logger.error(f"Critical error in main app: {str(e)}")
    st.error("An unexpected error occurred. Please try again later.")