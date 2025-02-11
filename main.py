import streamlit as st
import yfinance as yf

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