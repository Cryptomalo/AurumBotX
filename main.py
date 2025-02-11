
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import logging
from datetime import datetime
import requests
import ccxt
import time

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

# Inizializza stato sessione
if 'balance' not in st.session_state:
    st.session_state.balance = 10000
if 'positions' not in st.session_state:
    st.session_state.positions = []
if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []

# Streamlit Page Configuration
st.set_page_config(
    page_title="AurumBot Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_exchange():
    try:
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future'
            }
        })
        return exchange
    except Exception as e:
        logger.error(f"Error initializing exchange: {str(e)}")
        return None

def get_market_data(symbol, exchange):
    try:
        ticker = exchange.fetch_ticker(symbol)
        ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        return {
            'price': ticker['last'],
            'change_24h': ticker['percentage'],
            'volume': ticker['quoteVolume'],
            'high': ticker['high'],
            'low': ticker['low'],
            'ohlcv': df
        }
    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}")
        return None

# Sidebar
with st.sidebar:
    st.title("🤖 AurumBot Pro")
    
    # Navigation Menu
    selected_tab = st.radio("Navigation", ["Dashboard", "Trading", "Portfolio", "Settings"])
    
    # Crypto selection
    crypto = st.selectbox("Select Cryptocurrency", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
    
    # Account Info
    st.subheader("💰 Account")
    st.metric("Balance", f"${st.session_state.balance:.2f}")

# Initialize exchange
exchange = initialize_exchange()

if exchange is None:
    st.error("Failed to initialize exchange. Please check your connection.")
else:
    # Main content
    if selected_tab == "Dashboard":
        st.title(f"📊 Market Analysis - {crypto}")
        
        # Market Data
        market_data = get_market_data(crypto, exchange)
        if market_data:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Price", f"${market_data['price']:.2f}", f"{market_data['change_24h']:.2f}%")
            with col2:
                st.metric("24h High", f"${market_data['high']:.2f}")
            with col3:
                st.metric("24h Low", f"${market_data['low']:.2f}")
            
            # Candlestick Chart
            fig = go.Figure(data=[go.Candlestick(
                x=market_data['ohlcv']['timestamp'],
                open=market_data['ohlcv']['open'],
                high=market_data['ohlcv']['high'],
                low=market_data['ohlcv']['low'],
                close=market_data['ohlcv']['close']
            )])
            
            fig.update_layout(
                title=f"{crypto} Price Chart",
                yaxis_title="Price (USDT)",
                xaxis_title="Time"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Volume Chart
            volume_fig = go.Figure(data=[go.Bar(
                x=market_data['ohlcv']['timestamp'],
                y=market_data['ohlcv']['volume'],
                name="Volume"
            )])
            
            volume_fig.update_layout(
                title=f"{crypto} Volume",
                yaxis_title="Volume (USDT)",
                xaxis_title="Time"
            )
            
            st.plotly_chart(volume_fig, use_container_width=True)
        else:
            st.error("Error fetching market data")

    elif selected_tab == "Trading":
        st.subheader("🤖 Trading Interface")
        
        col1, col2 = st.columns(2)
        
        with col1:
            strategy = st.selectbox(
                "Trading Strategy",
                ["Scalping", "Trend Following", "Mean Reversion"]
            )
            
            risk_percent = st.slider("Risk per Trade (%)", 1, 10, 2)
            leverage = st.slider("Leverage", 1, 20, 1)
            
        with col2:
            st.subheader("Strategy Parameters")
            if strategy == "Scalping":
                take_profit = st.number_input("Take Profit %", 0.1, 5.0, 1.0)
                stop_loss = st.number_input("Stop Loss %", 0.1, 5.0, 0.5)
            elif strategy == "Trend Following":
                ma_fast = st.number_input("Fast MA Period", 5, 50, 20)
                ma_slow = st.number_input("Slow MA Period", 20, 200, 50)

    elif selected_tab == "Portfolio":
        st.subheader("💼 Portfolio")
        
        # Current Positions
        st.write("Open Positions:")
        if st.session_state.positions:
            df_positions = pd.DataFrame(st.session_state.positions)
            st.dataframe(df_positions)
        else:
            st.info("No open positions")
        
        # Trade History
        st.write("Trade History:")
        if st.session_state.trade_history:
            df_history = pd.DataFrame(st.session_state.trade_history)
            st.dataframe(df_history)
        else:
            st.info("No trade history")

    elif selected_tab == "Settings":
        st.subheader("⚙️ Settings")
        
        # API Configuration
        api_key = st.text_input("API Key", type="password")
        api_secret = st.text_input("API Secret", type="password")
        
        if st.button("Save Settings"):
            st.success("Settings saved!")

logger.info("Application rendered successfully")
