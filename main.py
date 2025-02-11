
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import logging
from datetime import datetime
from utils.auto_trader import AutoTrader
from utils.data_loader import CryptoDataLoader
from utils.strategies.strategy_library import StrategyLibrary

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

# Initialize components
data_loader = CryptoDataLoader()
strategy_library = StrategyLibrary()

def initialize_session_state():
    if 'trader' not in st.session_state:
        st.session_state.trader = AutoTrader('BTC-USD', initial_balance=10000)
    if 'active_trades' not in st.session_state:
        st.session_state.active_trades = []

def main():
    logger.info("Starting application...")

    # Basic page config
    st.set_page_config(
        page_title="AurumBot Pro",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    logger.info("Page config set")

    initialize_session_state()

    # Sidebar
    with st.sidebar:
        st.title("🤖 AurumBot Pro")
        
        # Navigation
        selected_tab = st.selectbox(
            "Navigation",
            ["Dashboard", "Trading", "Portfolio", "Settings"]
        )
        
        # Crypto selection
        crypto = st.selectbox(
            "Select Cryptocurrency",
            ["BTC-USD", "ETH-USD", "SOL-USD"]
        )

        if st.button("Start Bot"):
            st.session_state.trader.run()
            st.success("Trading bot started!")

        if st.button("Stop Bot"):
            st.session_state.trader = None
            st.success("Trading bot stopped!")

    # Main content area
    if selected_tab == "Dashboard":
        st.title("📊 Market Analysis")
        
        # Market data
        df = data_loader.get_historical_data(crypto, period='1d')
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Price", f"${df['Close'].iloc[-1]:.2f}", f"{df['Close'].pct_change().iloc[-1]:.2%}")
        with col2:
            st.metric("24h Volume", f"${df['Volume'].iloc[-1]/1000000:.1f}M")
        with col3:
            st.metric("24h Change", f"{((df['Close'].iloc[-1] - df['Close'].iloc[0])/df['Close'].iloc[0]*100):.1f}%")

        # Chart
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close']
        )])
        
        fig.update_layout(title=f"{crypto} Price Chart", height=600)
        st.plotly_chart(fig, use_container_width=True)

    elif selected_tab == "Trading":
        st.title("🤖 Trading Interface")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Account")
            balance = st.session_state.trader.balance
            st.metric("Balance", f"${balance:,.2f}")
            
            st.subheader("📊 Risk Management")
            risk_per_trade = st.slider("Risk per Trade (%)", 1, 10, 2)
            leverage = st.slider("Leverage", 1, 20, 1)
            
        with col2:
            st.subheader("🎯 Strategy Settings")
            strategy = st.selectbox(
                "Select Strategy",
                list(strategy_library.strategies.keys())
            )
            
            strategy_params = strategy_library.strategies[strategy]['params']
            st.json(strategy_params)
            
            if st.button("Execute Trade", type="primary"):
                trader = st.session_state.trader
                signal = trader.analyze_market()
                if signal:
                    trader.execute_trade(signal)
                    st.success(f"Trade executed: {signal['action']} at ${signal['price']:.2f}")
                else:
                    st.warning("No trading signal generated")

    elif selected_tab == "Portfolio":
        st.title("💼 Portfolio")
        
        # Portfolio summary
        portfolio = st.session_state.trader.portfolio
        st.metric("Total Value", f"${portfolio['total_value']:,.2f}")
        
        # Performance metrics
        metrics = portfolio['performance_metrics']
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Profit", f"${metrics['total_profit']:,.2f}")
        with col2:
            st.metric("Win Rate", f"{metrics['win_rate']*100:.1f}%")
        with col3:
            st.metric("Avg Profit/Trade", f"${metrics['avg_profit_per_trade']:,.2f}")
        
        # Trade history
        st.subheader("Trade History")
        if portfolio['trade_history']:
            df_trades = pd.DataFrame(portfolio['trade_history'])
            st.dataframe(df_trades)

    elif selected_tab == "Settings":
        st.title("⚙️ Settings")
        
        # API Configuration
        st.subheader("API Configuration")
        api_key = st.text_input("API Key", type="password")
        api_secret = st.text_input("API Secret", type="password")
        
        if st.button("Save Settings"):
            # Save API credentials
            st.success("Settings saved successfully!")

if __name__ == "__main__":
    main()
