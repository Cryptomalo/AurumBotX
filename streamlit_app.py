import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, Any, Optional
from binance.client import Client
from utils.database_manager import DatabaseManager
from utils.auto_trader import AutoTrader
from utils.strategies.strategy_manager import StrategyManager

# Configure page
st.set_page_config(
    page_title="AurumBot Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Styling
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
    }
    .tradingview-widget-container {
        height: 400px !important;
    }
    .market-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #2D2D2D;
    }
    .metric-card {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 8px;
        margin: 5px;
        border: 1px solid #2D2D2D;
    }
    </style>
""", unsafe_allow_html=True)

def connect_wallet():
    """Connect to cryptocurrency wallet"""
    st.session_state.wallet_address = "0x..."  # Will be replaced with actual wallet connection
    st.session_state.authenticated = True
    st.rerun()

def login_page():
    """Modern wallet-based login page"""
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("""
            <div style='text-align: center; margin-top: 100px;'>
                <h1 style='color: #00FF94; font-size: 3em;'>🤖 AurumBot</h1>
                <p style='font-size: 1.5em; color: #888888;'>AI-Powered Crypto Trading</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div style='background: linear-gradient(45deg, #1E1E1E, #2D2D2D);
                      padding: 30px;
                      border-radius: 15px;
                      margin-top: 50px;
                      text-align: center;
                      border: 1px solid #3D3D3D;'>
                <h2 style='color: #FFFFFF;'>Connect Your Wallet</h2>
                <p style='color: #888888;'>Start trading with AI-powered insights</p>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🔐 Connect Wallet", use_container_width=True):
            connect_wallet()

def render_ai_insights():
    """Render AI trading insights section"""
    st.subheader("🤖 AI Market Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
            <div class='market-card'>
                <h4>Market Sentiment Analysis</h4>
                <div style='display: flex; justify-content: space-between; margin-top: 20px;'>
                    <div>
                        <h5>BTC/USDT</h5>
                        <p style='color: #00FF94;'>Strong Buy (85%)</p>
                    </div>
                    <div>
                        <h5>ETH/USDT</h5>
                        <p style='color: #FFB700;'>Neutral (52%)</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class='market-card'>
                <h4>AI Price Predictions (24h)</h4>
                <div style='display: flex; justify-content: space-between; margin-top: 20px;'>
                    <div>
                        <h5>BTC Target</h5>
                        <p style='color: #00FF94;'>$48,500 (+5.2%)</p>
                    </div>
                    <div>
                        <h5>ETH Target</h5>
                        <p style='color: #00FF94;'>$3,200 (+4.1%)</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

def render_trading_interface():
    """Render the main trading interface"""
    col1, col2 = st.columns([7,3])

    with col1:
        # Advanced Chart
        st.subheader("📈 Advanced Trading Chart")

        # Chart settings
        chart_settings = st.columns([2,2,2,2])
        with chart_settings[0]:
            pair = st.selectbox("Trading Pair", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
        with chart_settings[1]:
            timeframe = st.select_slider("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"], value="1h")
        with chart_settings[2]:
            indicator = st.multiselect("Indicators", ["RSI", "MACD", "Bollinger Bands"], default=["RSI"])
        with chart_settings[3]:
            chart_type = st.selectbox("Chart Type", ["Candlestick", "Line", "Heikin-Ashi"])

        # Generate chart
        fig = go.Figure(data=[go.Candlestick(
            x=[datetime.now() - timedelta(hours=x) for x in range(100)],
            open=[45000 + x*10 for x in range(100)],
            high=[45100 + x*10 for x in range(100)],
            low=[44900 + x*10 for x in range(100)],
            close=[45050 + x*10 for x in range(100)]
        )])

        fig.update_layout(
            height=600,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="#1E1E1E",
            plot_bgcolor="#1E1E1E",
            font=dict(color="#CCCCCC"),
            yaxis=dict(gridcolor="#333333"),
            xaxis=dict(gridcolor="#333333")
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("💫 Quick Trade")
        with st.form("trade_form"):
            st.selectbox("Trading Pair", ["BTC/USDT", "ETH/USDT", "SOL/USDT"], key="trade_pair")
            cols = st.columns(2)
            with cols[0]:
                st.radio("Side", ["Buy", "Sell"], key="trade_side")
            with cols[1]:
                st.radio("Type", ["Market", "Limit"], key="trade_type")

            amount = st.number_input("Amount", min_value=0.0, step=0.001, format="%.3f")
            if st.session_state.get("trade_type") == "Limit":
                price = st.number_input("Limit Price", min_value=0.0, step=0.1, format="%.2f")

            submit = st.form_submit_button("Place Order", use_container_width=True)
            if submit:
                st.success("Order placed successfully!")

def render_portfolio_metrics():
    """Render portfolio metrics and performance"""
    st.subheader("📊 Portfolio Overview")

    # Key metrics
    cols = st.columns(4)
    metrics = [
        {"label": "Portfolio Value", "value": "$50,234.56", "delta": "+2.3%"},
        {"label": "24h PnL", "value": "$1,234.56", "delta": "+4.2%"},
        {"label": "Active Trades", "value": "5", "delta": "+2"},
        {"label": "Win Rate", "value": "73%", "delta": "+5%"}
    ]

    for col, metric in zip(cols, metrics):
        with col:
            st.metric(
                label=metric["label"],
                value=metric["value"],
                delta=metric["delta"]
            )

def render_auto_trading():
    """Render auto-trading configuration"""
    st.subheader("⚡ Auto-Trading")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
            <div class='market-card'>
                <h4>Strategy Configuration</h4>
                <div style='margin-top: 20px;'>
        """, unsafe_allow_html=True)

        strategy = st.selectbox("Trading Strategy", 
            ["AI Momentum", "Smart Grid", "Volatility Breakout"])
        risk_level = st.slider("Risk Level", 1, 10, 5)
        max_trades = st.number_input("Max Concurrent Trades", 1, 10, 3)

        st.markdown("</div></div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class='market-card'>
                <h4>Active Bot Status</h4>
                <div style='margin-top: 20px;'>
        """, unsafe_allow_html=True)

        st.write("🟢 Bot Status: Running")
        st.write("📈 Active Pairs: BTC/USDT, ETH/USDT")
        st.write("⚡ Last Trade: 5 minutes ago")
        st.write("💰 Today's Bot PnL: +$234.56")

        st.markdown("</div></div>", unsafe_allow_html=True)

def dashboard():
    """Main dashboard after login"""
    # Sidebar
    with st.sidebar:
        st.title("🤖 AurumBot Pro")

        # Wallet info
        if st.session_state.wallet_address:
            st.markdown("""
                <div style='background: #1E1E1E; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
                    <p style='color: #888888; margin-bottom: 5px;'>Connected Wallet</p>
                    <code style='color: #00FF94;'>
                        {}...{}
                    </code>
                </div>
            """.format(
                st.session_state.wallet_address[:6],
                st.session_state.wallet_address[-4:]
            ), unsafe_allow_html=True)

        # Simplified Navigation
        st.markdown("### Menu")
        nav = st.radio("", ["Trading", "Portfolio", "Auto-Trading"])

        st.markdown("---")
        if st.button("📤 Disconnect Wallet"):
            st.session_state.authenticated = False
            st.session_state.wallet_address = None
            st.rerun()

    # Main content based on navigation
    if nav == "Trading":
        render_trading_interface()
        render_ai_insights()
    elif nav == "Portfolio":
        render_portfolio_metrics()
    elif nav == "Auto-Trading":
        render_auto_trading()


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
        dashboard()

if __name__ == "__main__":
    main()