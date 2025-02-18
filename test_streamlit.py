import streamlit as st
import logging
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils.data_loader import CryptoDataLoader
from utils.indicators import TechnicalIndicators
from utils.auto_trader import AutoTrader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('streamlit_app.log')
    ]
)
logger = logging.getLogger(__name__)

def initialize_components():
    """Initialize trading components"""
    if 'data_loader' not in st.session_state:
        st.session_state.data_loader = CryptoDataLoader()
    if 'indicators' not in st.session_state:
        st.session_state.indicators = TechnicalIndicators()
    if 'auto_trader' not in st.session_state:
        st.session_state.auto_trader = AutoTrader(
            symbol="BTC-USD",
            initial_balance=10000,
            risk_per_trade=0.02
        )

def main():
    logger.info("Starting AurumBot Trading Dashboard")

    try:
        # Page configuration
        st.set_page_config(
            page_title="AurumBot Trading Dashboard",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Initialize components
        initialize_components()

        # Sidebar
        st.sidebar.title("Trading Controls")

        # Trading pair selection
        selected_pair = st.sidebar.selectbox(
            "Select Trading Pair",
            ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"]
        )

        # Timeframe selection
        timeframe = st.sidebar.selectbox(
            "Select Timeframe",
            ["1d", "4h", "1h", "15m", "5m"]
        )

        # Risk management
        risk_per_trade = st.sidebar.slider(
            "Risk per Trade (%)",
            min_value=0.1,
            max_value=5.0,
            value=2.0,
            step=0.1
        )

        # Main content
        st.title("📊 AurumBot Trading Dashboard")

        # Create tabs
        tab1, tab2, tab3 = st.tabs([
            "Market Analysis",
            "Portfolio",
            "Trading Bot"
        ])

        with tab1:
            try:
                # Get market data
                df = st.session_state.data_loader.get_historical_data(
                    selected_pair,
                    period=timeframe
                )

                if df is not None and not df.empty:
                    # Price chart
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
                        height=500
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Technical indicators
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        rsi = st.session_state.indicators.calculate_rsi(df)
                        st.metric("RSI", f"{rsi[-1]:.2f}")

                    with col2:
                        macd = st.session_state.indicators.calculate_macd(df)
                        st.metric("MACD", f"{macd[-1]:.2f}")

                    with col3:
                        volatility = st.session_state.auto_trader.calculate_market_volatility(df)
                        st.metric("Volatility", f"{volatility:.2%}")
                else:
                    st.error("Unable to fetch market data")

            except Exception as e:
                logger.error(f"Error in Market Analysis tab: {str(e)}")
                st.error("Error loading market analysis")

        with tab2:
            # Portfolio Overview
            st.subheader("Portfolio Summary")
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Total Balance",
                    f"${st.session_state.auto_trader.balance:,.2f}",
                    f"{((st.session_state.auto_trader.balance - st.session_state.auto_trader.initial_balance) / st.session_state.auto_trader.initial_balance) * 100:+.2f}%"
                )

            with col2:
                if st.session_state.auto_trader.current_position:
                    st.metric(
                        "Current Position",
                        f"${st.session_state.auto_trader.current_position['size']:,.2f}",
                        st.session_state.auto_trader.current_position['strategy']
                    )
                else:
                    st.metric("Current Position", "No Open Position")

        with tab3:
            # Trading Bot Controls
            st.subheader("Trading Bot Control Panel")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Start Trading Bot"):
                    try:
                        st.session_state.auto_trader.run(interval=60)
                        st.success("Trading bot started successfully!")
                    except Exception as e:
                        logger.error(f"Error starting trading bot: {str(e)}")
                        st.error(f"Failed to start trading bot: {str(e)}")

            with col2:
                if st.button("Stop Trading Bot"):
                    try:
                        # Implement stop functionality
                        st.warning("Trading bot stopped")
                    except Exception as e:
                        logger.error(f"Error stopping trading bot: {str(e)}")
                        st.error(f"Failed to stop trading bot: {str(e)}")

        # Add version info
        st.sidebar.info("Version: 1.0.0")
        logger.info("Dashboard rendered successfully")

    except Exception as e:
        logger.error(f"Critical error in dashboard: {str(e)}")
        st.error("A critical error occurred. Please check the logs.")

if __name__ == "__main__":
    main()