
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import ccxt
import time
import logging

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

# Page config
st.set_page_config(
    page_title="AurumBot",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
with open('assets/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize session state
if 'balance' not in st.session_state:
    st.session_state.balance = 10000
if 'positions' not in st.session_state:
    st.session_state.positions = []
if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []

# Header
st.markdown("""
    <div class="header" style="text-align: center; padding: 1rem;">
        <h1 style="color: #FFD700;">AurumBot</h1>
        <p style="color: #FFF;">AI-Powered Trading Platform</p>
    </div>
""", unsafe_allow_html=True)

# Main layout
left_col, center_col, right_col = st.columns([1,2,1])

with left_col:
    st.markdown("### 📊 Market Overview")
    exchange = initialize_exchange()
    if exchange:
        try:
            market_data_btc = get_market_data("BTC/USDT", exchange)
            market_data_eth = get_market_data("ETH/USDT", exchange)
            market_data_sol = get_market_data("SOL/USDT", exchange)

            if market_data_btc and market_data_eth and market_data_sol:
                st.metric("BTC/USDT", f"${market_data_btc['price']:,.2f}", f"{market_data_btc['change_24h']:.2f}%")
                st.metric("ETH/USDT", f"${market_data_eth['price']:,.2f}", f"{market_data_eth['change_24h']:.2f}%")
                st.metric("SOL/USDT", f"${market_data_sol['price']:,.2f}", f"{market_data_sol['change_24h']:.2f}%")
        except Exception as e:
            st.error(f"Error fetching market data: {str(e)}")
    else:
        st.error("Error initializing exchange")

    st.markdown("### 💼 Portfolio")
    st.metric("Total Balance", f"${st.session_state.balance:,.2f}")
    pnl = sum(pos.get('profit', 0) for pos in st.session_state.positions)
    st.metric("24h P/L", f"${pnl:,.2f}", f"{(pnl/st.session_state.balance)*100:+.2f}%")
    st.metric("Open Positions", len(st.session_state.positions))

with center_col:
    st.markdown("### 📈 Trading Chart")
    selected_asset = st.selectbox("Select Asset", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
    timeframe = st.select_slider("Timeframe", options=["1m", "5m", "15m", "1h", "4h", "1d"])

    if exchange:
        market_data = get_market_data(selected_asset, exchange)
        if market_data and 'ohlcv' in market_data:
            fig = go.Figure(data=[go.Candlestick(
                x=market_data['ohlcv']['timestamp'],
                open=market_data['ohlcv']['open'],
                high=market_data['ohlcv']['high'],
                low=market_data['ohlcv']['low'],
                close=market_data['ohlcv']['close']
            )])

            fig.update_layout(
                title=f"{selected_asset} Price Chart",
                yaxis_title="Price (USDT)",
                xaxis_title="Time",
                template="plotly_dark",
                height=500,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )

            st.plotly_chart(fig, use_container_width=True)

            volume_fig = go.Figure(data=[go.Bar(
                x=market_data['ohlcv']['timestamp'],
                y=market_data['ohlcv']['volume'],
                name="Volume"
            )])

            volume_fig.update_layout(
                title=f"{selected_asset} Volume",
                yaxis_title="Volume (USDT)",
                xaxis_title="Time",
                template="plotly_dark",
                height=200,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )

            st.plotly_chart(volume_fig, use_container_width=True)

with right_col:
    st.markdown("### 🤖 AI Signals")
    st.markdown("""
        <div style="background-color: rgba(0,255,0,0.1); padding: 1rem; border-radius: 5px; margin-bottom: 1rem;">
            <h4 style="color: #FFD700;">BTC/USDT</h4>
            <p style="color: #00FF00;">Strong Buy</p>
            <div>Confidence: 85%</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📝 Recent Trades")
    if st.session_state.trade_history:
        for trade in st.session_state.trade_history[-5:]:
            st.markdown(f"**{trade['symbol']}** - {trade['type']}")
            st.caption(f"P/L: {trade['profit']:+.2f} USDT")
    else:
        st.info("No recent trades")

logger.info("Application rendered successfully")
