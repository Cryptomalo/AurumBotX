import os
import sys
import logging
import traceback
from datetime import datetime
import time
import threading

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Import core dependencies
    import streamlit as st
    import pandas as pd
    import yfinance as yf
except ImportError as e:
    logger.error(f"Failed to import core dependencies: {e}")
    st.error("Failed to load core dependencies. Please check the installation.")
    sys.exit(1)


# Configurazione della pagina
try:
    st.set_page_config(
        page_title="AurumBot - Basic Test",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except Exception as e:
    logger.error(f"Failed to configure page: {e}")
    st.error("Failed to configure page. Please try refreshing.")

# Basic sidebar
st.sidebar.title("🤖 AurumBot")
crypto = st.sidebar.selectbox(
    "Select Cryptocurrency",
    ["BTC-USD", "ETH-USD", "SOL-USD"]
)


# Main content
st.title("Basic Crypto Dashboard")

try:
    data = yf.download(crypto, period="7d", interval="1h")
    if not data.empty:
        st.line_chart(data['Close'])
        st.dataframe(data.tail())
    else:
        st.error("No data available")
except Exception as e:
    st.error(f"Error: {str(e)}")