import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import websocket
import threading
from solana.rpc.api import Client
from utils.auto_trader import AutoTrader
from utils.strategies.strategy_manager import StrategyManager

# Configure page
st.set_page_config(
    page_title="SolanaBot Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Styling
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
    }
    .trading-card {
        background: linear-gradient(45deg, #1E1E1E, #2D2D2D);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #3D3D3D;
        margin-bottom: 20px;
    }
    .nav-pill {
        background: linear-gradient(45deg, #2D2D2D, #3D3D3D);
        padding: 10px 20px;
        border-radius: 25px;
        border: 1px solid #4D4D4D;
        color: #FFFFFF;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .nav-pill:hover {
        background: linear-gradient(45deg, #3D3D3D, #4D4D4D);
        transform: translateY(-2px);
    }
    .nav-pill.active {
        background: linear-gradient(45deg, #00FF94, #00E0A0);
        color: #0E1117;
        font-weight: bold;
    }
    .metric-value {
        color: #00FF94;
        font-size: 24px;
        font-weight: bold;
    }
    .bot-status-active {
        color: #00FF94;
        font-weight: bold;
    }
    .bot-status-inactive {
        color: #FF4B4B;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

def connect_wallet():
    """Connect Solana wallet"""
    st.session_state.wallet_address = "GkDg...Rnq9"
    st.session_state.authenticated = True
    st.rerun()

def login_page():
    """Modern Solana wallet login page"""
    col1, col2, col3 = st.columns([1,2,1])

    with col2:
        st.markdown("""
            <div style='text-align: center; margin-top: 100px;'>
                <h1 style='color: #00FF94; font-size: 3em;'>🚀 SolanaBot Pro</h1>
                <p style='font-size: 1.5em; color: #888888;'>Meme Coin Trading Bot</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div style='background: linear-gradient(45deg, #1E1E1E, #2D2D2D);
                      padding: 30px;
                      border-radius: 15px;
                      margin-top: 50px;
                      text-align: center;
                      border: 1px solid #3D3D3D;'>
                <h2 style='color: #FFFFFF;'>Connect Solana Wallet</h2>
                <p style='color: #888888;'>Start trading meme coins with AI-powered strategies</p>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🔐 Connect Phantom Wallet", use_container_width=True):
            connect_wallet()

def render_meme_coin_charts():
    """Render real-time meme coin charts from DEXScreener"""
    st.subheader("📊 Top Solana Meme Coins")

    # Meme coin selector
    col1, col2, col3 = st.columns([2,2,1])
    with col1:
        selected_pair = st.selectbox(
            "Select Pair",
            ["BONK/SOL", "WIF/SOL", "POPCAT/SOL", "SLERF/SOL"]
        )
    with col2:
        timeframe = st.select_slider(
            "Timeframe",
            ["5m", "15m", "1h", "4h", "1d"],
            value="1h"
        )
    with col3:
        st.button("🔄 Refresh", use_container_width=True)

    # Trading chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=[datetime.now() - timedelta(hours=x) for x in range(100)],
        open=[0.1 + x*0.01 for x in range(100)],
        high=[0.15 + x*0.01 for x in range(100)],
        low=[0.05 + x*0.01 for x in range(100)],
        close=[0.12 + x*0.01 for x in range(100)]
    ))

    fig.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#1E1E1E",
        plot_bgcolor="#1E1E1E",
        font=dict(color="#CCCCCC"),
        yaxis=dict(gridcolor="#333333"),
        xaxis=dict(gridcolor="#333333")
    )

    st.plotly_chart(fig, use_container_width=True)

    # Market metrics
    cols = st.columns(4)
    with cols[0]:
        st.metric("Price", "$0.00023", "+5.2%")
    with cols[1]:
        st.metric("24h Volume", "$1.2M", "+12.3%")
    with cols[2]:
        st.metric("Market Cap", "$45M", "+3.1%")
    with cols[3]:
        st.metric("Holders", "12.5K", "+156")

def render_trading_strategies():
    """Configure and manage trading strategies"""
    st.subheader("⚙️ Trading Strategies")

    col1, col2 = st.columns([2,1])

    with col1:
        st.markdown("""
            <div class='trading-card'>
                <h4>Strategy Configuration</h4>
        """, unsafe_allow_html=True)

        strategy = st.selectbox(
            "Select Strategy",
            ["Momentum Scanner", "Volatility Breakout", "DEX Flow Tracker", "Social Sentiment"]
        )

        col_risk, col_size = st.columns(2)
        with col_risk:
            risk_level = st.slider("Risk Level", 1, 10, 5)
        with col_size:
            position_size = st.number_input("Position Size (SOL)", 0.1, 100.0, 1.0)

        tokens = st.multiselect(
            "Target Tokens",
            ["BONK", "WIF", "POPCAT", "SLERF", "MOONCAT"],
            ["BONK", "WIF"]
        )

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class='trading-card'>
                <h4>Quick Settings</h4>
        """, unsafe_allow_html=True)

        stop_loss = st.number_input("Stop Loss %", 5, 50, 15)
        take_profit = st.number_input("Take Profit %", 10, 200, 50)
        max_trades = st.number_input("Max Concurrent Trades", 1, 5, 2)

        st.markdown("</div>", unsafe_allow_html=True)

def render_bot_control():
    """Bot control panel and live operations"""
    st.subheader("🤖 Bot Control")

    # Bot status and controls
    col1, col2 = st.columns([3,1])

    with col1:
        st.markdown("""
            <div class='trading-card'>
                <h4>Bot Status</h4>
                <p class='bot-status-active'>● Bot Active - Running Strategy: Momentum Scanner</p>
                <p>Current Position: Long BONK/SOL @ 0.00023</p>
                <p>Last Action: Buy signal detected for WIF/SOL</p>
                <p>Uptime: 2h 15m</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='trading-card'>", unsafe_allow_html=True)
        if st.button("▶️ Start Bot", use_container_width=True):
            st.success("Bot started successfully!")

        if st.button("⏹️ Stop Bot", use_container_width=True):
            st.error("Bot stopped")
        st.markdown("</div>", unsafe_allow_html=True)

    # Live operations
    st.subheader("📈 Live Operations")
    operations = pd.DataFrame({
        'Time': ['2025-02-19 15:30:22', '2025-02-19 15:15:10', '2025-02-19 14:55:33'],
        'Token': ['BONK/SOL', 'WIF/SOL', 'POPCAT/SOL'],
        'Type': ['BUY', 'SELL', 'BUY'],
        'Price': ['0.00023', '0.00158', '0.00012'],
        'Size (SOL)': ['2.5', '1.8', '3.0'],
        'Profit/Loss': ['+2.3%', '+15.2%', '-1.5%']
    })
    st.dataframe(operations, use_container_width=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'wallet_address' not in st.session_state:
        st.session_state.wallet_address = None

def main():
    initialize_session_state()

    if not st.session_state.authenticated:
        login_page()
    else:
        # Wallet info in top right
        col_wallet = st.columns([3, 1])
        with col_wallet[1]:
            st.markdown(f"""
                <div style='text-align: right; padding: 10px;'>
                    <span style='color: #888888;'>Connected: </span>
                    <code style='color: #00FF94; background: #1E1E1E; padding: 5px 10px; border-radius: 5px;'>
                        {st.session_state.wallet_address[:6]}...{st.session_state.wallet_address[-4:]}
                    </code>
                    </div>
            """, unsafe_allow_html=True)

        # Horizontal Navigation
        st.markdown("<br>", unsafe_allow_html=True)
        nav_cols = st.columns(4)
        nav_options = ["Market Analysis", "Trading", "Bot Control"]

        if 'nav_selection' not in st.session_state:
            st.session_state.nav_selection = "Market Analysis"

        for i, option in enumerate(nav_options):
            with nav_cols[i]:
                if st.button(
                    f"{option}",
                    key=f"nav_{option}",
                    use_container_width=True,
                    help=f"View {option}"
                ):
                    st.session_state.nav_selection = option

        # Add visual separator
        st.markdown("<hr style='border: 1px solid #2D2D2D; margin: 20px 0;'>", unsafe_allow_html=True)

        # Main content based on navigation
        if st.session_state.nav_selection == "Market Analysis":
            render_meme_coin_charts()
        elif st.session_state.nav_selection == "Trading":
            render_trading_strategies()
        elif st.session_state.nav_selection == "Bot Control":
            render_bot_control()

        # Logout button at bottom
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📤 Disconnect Wallet", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.wallet_address = None
            st.rerun()

if __name__ == "__main__":
    main()