import os
import logging
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

from utils.data_loader import CryptoDataLoader
from utils.indicators import TechnicalIndicators

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        st.set_page_config(
            page_title="AurumBot Trading Platform",
            page_icon="🌟",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Initialize components
        data_loader = CryptoDataLoader()

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

        # Main content
        st.title("🌟 AurumBot Trading Platform")

        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Market Analysis",
            "🤖 Auto Trading",
            "💼 Portfolio",
            "⚙️ Settings"
        ])

        with tab1:
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("Price Chart")

                df = data_loader.get_historical_data(selected_coin, period=timeframe)

                if df is not None and not df.empty:
                    fig = go.Figure(data=[go.Candlestick(
                        x=df.index,
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close']
                    )])

                    fig.update_layout(
                        title=f"{data_loader.supported_coins[selected_coin]} Price Chart",
                        yaxis_title="Price (USD)",
                        xaxis_title="Date",
                        template="plotly_dark",
                        height=500
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Technical indicators
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
                        vol_change = (df['Volume'].iloc[-1] / df['Volume'].iloc[-2] - 1) * 100
                        st.metric(
                            "Volume",
                            f"{df['Volume'].iloc[-1]:,.0f}",
                            f"{vol_change:.1f}%"
                        )
                else:
                    st.error("Unable to load price data. Please try again later.")

            with col2:
                st.subheader("Market Overview")
                current_price = data_loader.get_current_price(selected_coin)

                if current_price:
                    price_change = 0
                    if df is not None and not df.empty:
                        price_change = ((current_price / df['Close'].iloc[-2] - 1) * 100)

                    st.metric(
                        "Current Price",
                        f"${current_price:,.2f}",
                        f"{price_change:.2f}%"
                    )
                else:
                    st.error("Unable to fetch current price")

        with tab2:
            st.subheader("Auto Trading Settings")
            col1, col2 = st.columns(2)

            with col1:
                risk_per_trade = st.slider(
                    "Risk per Trade (%)",
                    min_value=0.1,
                    max_value=5.0,
                    value=1.0,
                    step=0.1
                )

                strategy = st.selectbox(
                    "Trading Strategy",
                    ["Scalping", "Swing Trading", "Mean Reversion"]
                )

            with col2:
                take_profit = st.number_input(
                    "Take Profit (%)",
                    min_value=0.1,
                    max_value=100.0,
                    value=2.0
                )

                stop_loss = st.number_input(
                    "Stop Loss (%)",
                    min_value=0.1,
                    max_value=100.0,
                    value=1.0
                )

            if st.button("Start Auto Trading"):
                st.warning("Auto trading feature coming soon!")

        with tab3:
            st.subheader("Portfolio Overview")
            st.info("Connect your wallet to view portfolio details")

            if st.button("Connect Wallet"):
                st.warning("Wallet connection feature coming soon!")

        with tab4:
            st.subheader("Platform Settings")
            with st.expander("Notification Settings"):
                st.checkbox("Enable Email Notifications")
                st.checkbox("Enable Telegram Notifications")
                if st.button("Save Settings"):
                    st.success("Settings saved successfully!")

        st.sidebar.info("Version: 1.0.0")

    except Exception as e:
        logger.error(f"Critical error in main app: {str(e)}")
        st.error("An unexpected error occurred. Please try again later.")

if __name__ == "__main__":
    main()