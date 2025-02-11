import os
import sys
import logging
from datetime import datetime

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'app_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Cache for performance
@st.cache_data(ttl=300)
def load_market_data(symbol: str, period: str = '1d', interval: str = '1m'):
    """Load and cache market data"""
    try:
        logger.info(f"Fetching data for {symbol}")
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            logger.warning(f"No data received for {symbol}")
            return None

        return df
    except Exception as e:
        logger.error(f"Error loading market data: {e}", exc_info=True)
        return None

def main():
    try:
        st.set_page_config(
            page_title="AurumBot Beta",
            page_icon="🌟",
            layout="wide"
        )

        st.title("🌟 AurumBot Trading Platform (Beta)")

        # Sidebar controls
        st.sidebar.title("Trading Controls")

        selected_coin = st.sidebar.selectbox(
            "Select Trading Pair",
            ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"]
        )

        timeframe = st.sidebar.selectbox(
            "Select Timeframe",
            options=["1d", "4h", "1h", "15m", "5m"],
            format_func=lambda x: {
                "1d": "1 Day",
                "4h": "4 Hours",
                "1h": "1 Hour",
                "15m": "15 Minutes",
                "5m": "5 Minutes"
            }[x]
        )

        # Main content area
        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader("Price Chart")
            df = load_market_data(selected_coin, period=timeframe)

            if df is not None and not df.empty:
                # Create candlestick chart
                fig = go.Figure(data=[go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close']
                )])

                fig.update_layout(
                    title=f"{selected_coin} Price Chart",
                    yaxis_title="Price (USD)",
                    template="plotly_dark",
                    height=600
                )

                st.plotly_chart(fig, use_container_width=True)

                # Basic stats
                with st.expander("Market Statistics"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric(
                            "Current Price",
                            f"${df['Close'].iloc[-1]:,.2f}",
                            f"{((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100:,.2f}%"
                        )
                    with col_b:
                        st.metric(
                            "24h Volume",
                            f"${df['Volume'].sum():,.0f}"
                        )
            else:
                st.error("Unable to fetch market data. Please try again later.")

        with col2:
            st.subheader("Quick Actions")
            st.info("Trading features will be available soon!")

        # Version info
        st.sidebar.info("Version: 1.0.0 (Beta)")

    except Exception as e:
        logger.error(f"Critical error in main app: {e}", exc_info=True)
        st.error("An error occurred. Please check the logs.")

if __name__ == "__main__":
    main()