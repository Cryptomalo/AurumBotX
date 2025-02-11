import streamlit as st
import yfinance as yf
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Verifica connessione
try:
    yf.download("BTC-USD", period="1d")
    logger.info("Connessione al server dati OK")
except Exception as e:
    st.error("Errore di connessione al server dati")
    logger.error(f"Errore: {str(e)}")

# Basic configuration
st.set_page_config(page_title="AurumBot - Basic Test", layout="wide")

# Sidebar
st.sidebar.title("🤖 AurumBot")
crypto = st.sidebar.selectbox("Select Cryptocurrency", ["BTC-USD", "ETH-USD", "SOL-USD"])

# Main content
st.title("Basic Crypto Dashboard")

try:
    data = yf.download(crypto, period="1d", interval="1h")
    if not data.empty:
        st.line_chart(data['Close'])
        st.dataframe(data.tail())
    else:
        st.error("No data available")
except Exception as e:
    st.error(f"Error: {str(e)}")