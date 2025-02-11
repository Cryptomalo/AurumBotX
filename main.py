
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import logging
from datetime import datetime
import requests
import ccxt

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

# Sidebar
with st.sidebar:
    st.title("🤖 AurumBot Pro")
    
    # Navigation Menu
    selected_tab = st.radio("Navigation", ["Dashboard", "Trading", "Portfolio", "Settings"])
    
    # Crypto selection
    crypto = st.selectbox("Select Cryptocurrency", ["BTC/USD", "ETH/USD", "SOL/USD"])
    
    # Account Info
    st.subheader("💰 Account")
    st.metric("Balance", f"${st.session_state.balance:.2f}")
    
    if st.button("Start Bot"):
        st.success("Trading bot started!")

def get_market_data(symbol):
    try:
        exchange = ccxt.binance()
        ticker = exchange.fetch_ticker(symbol)
        return {
            'price': ticker['last'],
            'change_24h': ticker['percentage'],
            'volume': ticker['quoteVolume'],
            'high': ticker['high'],
            'low': ticker['low']
        }
    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}")
        return None

def execute_trade(action, symbol, amount, price):
    if action == 'BUY' and st.session_state.balance >= amount * price:
        st.session_state.balance -= amount * price
        st.session_state.positions.append({
            'symbol': symbol,
            'amount': amount,
            'entry_price': price,
            'timestamp': datetime.now()
        })
        return True
    elif action == 'SELL':
        for i, pos in enumerate(st.session_state.positions):
            if pos['symbol'] == symbol:
                profit = (price - pos['entry_price']) * pos['amount']
                st.session_state.balance += amount * price + profit
                st.session_state.positions.pop(i)
                st.session_state.trade_history.append({
                    'symbol': symbol,
                    'profit': profit,
                    'exit_price': price,
                    'timestamp': datetime.now()
                })
                return True
    return False

# Main content
if selected_tab == "Dashboard":
    st.title(f"📊 Market Analysis - {crypto}")
    
    # Market Data
    market_data = get_market_data(crypto)
    if market_data:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Price", f"${market_data['price']:.2f}", f"{market_data['change_24h']:.2f}%")
        with col2:
            st.metric("24h High", f"${market_data['high']:.2f}")
        with col3:
            st.metric("24h Low", f"${market_data['low']:.2f}")
            
        # Price Chart
        df = pd.DataFrame({
            'time': pd.date_range(start='2024-01-01', periods=100, freq='H'),
            'price': np.random.normal(market_data['price'], market_data['price']*0.01, 100)
        })
        
        fig = go.Figure(data=[go.Candlestick(
            x=df['time'],
            open=df['price'],
            high=df['price']*1.001,
            low=df['price']*0.999,
            close=df['price']
        )])
        
        st.plotly_chart(fig, use_container_width=True)

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
        
        if st.button("Execute Trade"):
            amount = (st.session_state.balance * risk_percent/100) * leverage
            if execute_trade('BUY', crypto, amount/market_data['price'], market_data['price']):
                st.success(f"Bought {amount/market_data['price']:.6f} {crypto}")
            else:
                st.error("Insufficient funds")

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
    st.text_input("API Key", type="password")
    st.text_input("API Secret", type="password")
    
    if st.button("Save Settings"):
        st.success("Settings saved!")

logger.info("Application rendered successfully")
