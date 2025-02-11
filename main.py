import os
import logging
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_loader import CryptoDataLoader

# Setup logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

@st.cache_data(ttl=60)  # Cache per 60 secondi
def safe_metric_change(current, previous):
    """Calculate percentage change safely"""
    try:
        current = float(current.iloc[0]) if hasattr(current, 'iloc') else float(current)
        previous = float(previous.iloc[0]) if hasattr(previous, 'iloc') else float(previous)

        if pd.isna(current) or pd.isna(previous) or previous == 0:
            return 0.0
        return ((current / previous) - 1.0) * 100
    except Exception as e:
        logger.error(f"Error calculating metric: {e}")
        return 0.0

def format_volume(volume):
    """Format volume in readable format"""
    try:
        volume = float(volume.iloc[0]) if hasattr(volume, 'iloc') else float(volume)
        if pd.isna(volume):
            return "N/A"
        if volume >= 1e9:
            return f"{volume/1e9:.1f}B"
        if volume >= 1e6:
            return f"{volume/1e6:.1f}M"
        if volume >= 1e3:
            return f"{volume/1e3:.1f}K"
        return f"{volume:.0f}"
    except Exception as e:
        logger.error(f"Error formatting volume: {e}")
        return "N/A"

# Set page configuration
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

# Coin selection
selected_coin = st.sidebar.selectbox(
    "Select Trading Pair",
    options=list(data_loader.supported_coins.keys()),
    format_func=lambda x: f"{data_loader.supported_coins[x]} ({x})"
)

# Timeframe selection
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
    st.subheader("Market Overview")
    try:
        with st.spinner(f'Caricamento dati per {selected_coin}...'):
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

            #Retained from original - Market Overview section
            st.subheader("Market Overview")
            current_price = data_loader.get_current_price(selected_coin)
            if current_price is not None:
                price_change = 0.0
                if df is not None and not df.empty:
                    prev_price = df['Close'].iloc[-2]
                    price_change = safe_metric_change(current_price, prev_price)

                st.metric(
                    "Current Price",
                    f"${current_price:,.2f}",
                    f"{price_change:.2f}%"
                )
            else:
                st.error("Unable to fetch current price")

        else:
            st.error("Unable to load market data")
    except Exception as e:
        logger.error(f"Error in market analysis: {str(e)}")
        st.error("Error loading market data")

with tab2:
    st.subheader("Auto Trading")
    st.info("Auto trading features coming soon!")

with tab3:
    st.subheader("Portfolio")
    st.info("Portfolio tracking coming soon!")

with tab4:
    st.subheader("Settings")
    st.info("Settings configuration coming soon!")

st.sidebar.info("Version: 1.0.0")
logger.info("Application setup completed successfully")

except Exception as e:
    logger.error(f"Critical error in main app: {str(e)}", exc_info=True)
    st.error(f"Errore: {str(e)}")
    if st.checkbox("Mostra dettagli errore"):
        st.exception(e)