
import os
import sys
import logging
from datetime import datetime
import streamlit as st
from utils.auto_trader import AutoTrader
from utils.data_loader import CryptoDataLoader
from utils.test_suite import AurumBotTester

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('streamlit_app.log')
    ]
)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="AurumBot Testnet",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
    <style>
    .reportview-container {
        background: #0E1117
    }
    .sidebar .sidebar-content {
        background: #262730
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.title("🌟 AurumBot Testnet")
    
    # Sidebar
    st.sidebar.title("Trading Controls")
    trading_pair = st.sidebar.selectbox(
        "Select Trading Pair",
        ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    )
    
    initial_balance = st.sidebar.number_input(
        "Initial Balance (USDT)",
        min_value=10.0,
        value=1000.0
    )
    
    if st.sidebar.button("Start Test Trading"):
        bot = AutoTrader(
            symbol=trading_pair,
            initial_balance=initial_balance,
            testnet=True
        )
        
        st.session_state['bot'] = bot
        st.success(f"Bot initialized for {trading_pair} with {initial_balance} USDT")
        
        # Start test analysis
        try:
            signal = bot.analyze_market()
            if signal:
                st.info(f"Signal detected: {signal}")
                if bot.execute_trade(signal):
                    st.success("Test trade executed successfully")
        except Exception as e:
            st.error(f"Error during test: {str(e)}")
            logger.error(f"Test error: {str(e)}")

    # Display current status if bot exists
    if 'bot' in st.session_state:
        bot = st.session_state['bot']
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Current Balance", f"{bot.balance:.2f} USDT")
        with col2:
            st.metric("Active Trades", "0" if not bot.is_in_position else "1")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error(f"Application error: {str(e)}")
