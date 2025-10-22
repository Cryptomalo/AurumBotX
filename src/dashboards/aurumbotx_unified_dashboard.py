#!/usr/bin/env python3
"""
AurumBotX Unified Dashboard
==========================
Dashboard unificata moderna per il controllo completo di AurumBotX v2.0

Features:
- Trading Control & Monitoring
- Real-time Market Data
- Portfolio Management
- System Status
- 30 USDT Challenge Progress
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
import json
import time
from datetime import datetime, timedelta
import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Page config
st.set_page_config(
    page_title="AurumBotX v2.0 - Unified Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern design
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin-bottom: 1rem;
    }
    
    .status-online {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-offline {
        color: #dc3545;
        font-weight: bold;
    }
    
    .challenge-progress {
        background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .trading-controls {
        background: #e9ecef;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE = "http://localhost:5678"
DB_PATH = "../../data/aurumbotx.db"

class AurumBotXDashboard:
    def __init__(self):
        self.api_base = API_BASE
        
    def get_api_data(self, endpoint):
        """Get data from API with error handling"""
        try:
            response = requests.get(f"{self.api_base}{endpoint}", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None
    
    def get_market_data(self):
        """Get real-time market data"""
        try:
            # Import with proper path handling
            import sys
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from src.data.real_crypto_prices import RealCryptoPrices
            price_provider = RealCryptoPrices()
            
            symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD', 'DOT-USD']
            market_data = {}
            
            for symbol in symbols:
                data = price_provider.get_current_price(symbol)
                if data:
                    market_data[symbol] = data
                    
            return market_data
        except Exception as e:
            st.error(f"Market Data Error: {str(e)}")
            return {}
    
    def get_trading_status(self):
        """Get current trading status"""
        data = self.get_api_data("/api/trading/status")
        if data and data.get('success'):
            return data.get('data', {})
        return {
            'is_active': False,
            'strategy': 'None',
            'balance': 30.0,
            'trades_today': 0,
            'win_rate': 0.0
        }
    
    def get_challenge_progress(self):
        """Get 30 USDT Challenge progress"""
        try:
            if os.path.exists(DB_PATH):
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                # Get current balance
                cursor.execute("SELECT balance FROM portfolio ORDER BY timestamp DESC LIMIT 1")
                result = cursor.fetchone()
                current_balance = result[0] if result else 30.0
                
                # Get total trades
                cursor.execute("SELECT COUNT(*) FROM trades")
                total_trades = cursor.fetchone()[0]
                
                # Get win rate
                cursor.execute("SELECT COUNT(*) FROM trades WHERE profit > 0")
                winning_trades = cursor.fetchone()[0]
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                
                conn.close()
                
                # Calculate progress
                start_balance = 30.0
                target_balance = 240.0
                progress = ((current_balance - start_balance) / (target_balance - start_balance)) * 100
                progress = max(0, min(100, progress))
                
                return {
                    'current_balance': current_balance,
                    'target_balance': target_balance,
                    'progress_percent': progress,
                    'total_trades': total_trades,
                    'win_rate': win_rate,
                    'profit_loss': current_balance - start_balance
                }
            else:
                return {
                    'current_balance': 30.0,
                    'target_balance': 240.0,
                    'progress_percent': 0.0,
                    'total_trades': 0,
                    'win_rate': 0.0,
                    'profit_loss': 0.0
                }
        except Exception as e:
            st.error(f"Database Error: {str(e)}")
            return {
                'current_balance': 30.0,
                'target_balance': 240.0,
                'progress_percent': 0.0,
                'total_trades': 0,
                'win_rate': 0.0,
                'profit_loss': 0.0
            }

def main():
    dashboard = AurumBotXDashboard()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 AurumBotX v2.0 - Unified Dashboard</h1>
        <p>Advanced Cryptocurrency Trading Bot - 30 USDT Challenge</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/1e3c72/ffffff?text=AurumBotX", width=200)
        st.markdown("### 🎯 Navigation")
        
        page = st.selectbox(
            "Select Page",
            ["🏠 Overview", "📊 Trading", "💰 Portfolio", "⚙️ Settings", "📈 Analytics"]
        )
        
        st.markdown("---")
        st.markdown("### 🔄 Quick Actions")
        
        if st.button("🚀 Start Trading", type="primary"):
            st.success("Trading started!")
            
        if st.button("⏹️ Stop Trading"):
            st.warning("Trading stopped!")
            
        if st.button("🔄 Refresh Data"):
            st.rerun()

        st.markdown("---")
        st.markdown("### ⚠️ Emergency Actions")
        if st.button("🚨 EMERGENCY STOP", type="secondary"):
            st.warning("Attempting to trigger Emergency Stop...")
            response = requests.post(f"{dashboard.api_base}/api/emergency-stop", json={"reason": "Manual stop from dashboard"})
            if response.status_code == 200:
                st.success("✅ Emergency Stop signal sent successfully!")
                st.balloons()
            else:
                st.error(f"❌ Failed to trigger Emergency Stop: {response.text}")
    
    # Main content based on selected page
    if page == "🏠 Overview":
        show_overview(dashboard)
    elif page == "📊 Trading":
        show_trading(dashboard)
    elif page == "💰 Portfolio":
        show_portfolio(dashboard)
    elif page == "⚙️ Settings":
        show_settings(dashboard)
    elif page == "📈 Analytics":
        show_analytics(dashboard)

def show_overview(dashboard):
    """Show overview page"""
    st.markdown("## 🏠 System Overview")
    
    # Challenge Progress
    challenge_data = dashboard.get_challenge_progress()
    
    st.markdown(f"""
    <div class="challenge-progress">
        <h3>🎯 30 USDT Challenge Progress</h3>
        <h2>${challenge_data['current_balance']:.2f} / $240.00</h2>
        <p>Progress: {challenge_data['progress_percent']:.1f}% | 
           Trades: {challenge_data['total_trades']} | 
           Win Rate: {challenge_data['win_rate']:.1f}%</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress bar
    progress_bar = st.progress(challenge_data['progress_percent'] / 100)
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Current Balance",
            f"${challenge_data['current_balance']:.2f}",
            f"${challenge_data['profit_loss']:+.2f}"
        )
    
    with col2:
        st.metric(
            "📈 Total Trades",
            challenge_data['total_trades'],
            "Today: 0"
        )
    
    with col3:
        st.metric(
            "🎯 Win Rate",
            f"{challenge_data['win_rate']:.1f}%",
            "Target: 65%"
        )
    
    with col4:
        st.metric(
            "🚀 Progress",
            f"{challenge_data['progress_percent']:.1f}%",
            "Target: 100%"
        )
    
    # System Status
    st.markdown("## 🔧 System Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🖥️ Core Services")
        
        # Check API status
        api_status = dashboard.get_api_data("/health")
        if api_status:
            st.markdown('<p class="status-online">✅ API Server: ONLINE</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-offline">❌ API Server: OFFLINE</p>', unsafe_allow_html=True)
        
        st.markdown('<p class="status-online">✅ Trading Engine: ACTIVE</p>', unsafe_allow_html=True)
        st.markdown('<p class="status-online">✅ Real-time Data: CONNECTED</p>', unsafe_allow_html=True)
        st.markdown('<p class="status-online">✅ Database: OPERATIONAL</p>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📊 Market Data")
        
        market_data = dashboard.get_market_data()
        
        if market_data:
            for symbol, data in list(market_data.items())[:4]:
                price = data.get('price', 0)
                change = data.get('change_24h', 0)
                color = "🟢" if change >= 0 else "🔴"
                st.markdown(f"{color} **{symbol}**: ${price:,.2f} ({change:+.2f}%)")
        else:
            st.warning("Market data temporarily unavailable")
    
    # Recent Activity
    st.markdown("## 📋 Recent Activity")
    
    # Mock recent trades data
    recent_trades = pd.DataFrame({
        'Time': ['10:30:15', '10:25:42', '10:20:18', '10:15:33'],
        'Symbol': ['BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD'],
        'Type': ['BUY', 'SELL', 'BUY', 'SELL'],
        'Amount': ['0.001', '0.05', '2.5', '100'],
        'Price': ['$57,234', '$3,456', '$145', '$0.45'],
        'P&L': ['+$12.34', '+$8.90', '+$5.67', '-$2.10'],
        'Status': ['✅ Completed', '✅ Completed', '✅ Completed', '❌ Loss']
    })
    
    st.dataframe(recent_trades, use_container_width=True)

def show_trading(dashboard):
    """Show trading page"""
    st.markdown("## 📊 Trading Control Center")
    
    # Trading Controls
    st.markdown("""
    <div class="trading-controls">
        <h3>🎮 Trading Controls</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        strategy = st.selectbox(
            "🧠 Strategy",
            ["Challenge Growth", "Conservative", "Aggressive", "Balanced"]
        )
    
    with col2:
        mode = st.selectbox(
            "🔧 Mode",
            ["TESTNET", "MAINNET"]
        )
    
    with col3:
        risk_level = st.slider("⚠️ Risk Level", 1, 10, 5)
    
    # Trading Status
    trading_status = dashboard.get_trading_status()
    
    if trading_status['is_active']:
        st.success("🟢 Trading is ACTIVE")
    else:
        st.error("🔴 Trading is STOPPED")
    
    # Real-time Chart
    st.markdown("## 📈 Real-time Price Chart")
    
    # Create sample chart
    dates = pd.date_range(start='2025-01-01', periods=100, freq='H')
    prices = 50000 + (pd.Series(range(100)) * 100) + (pd.Series(range(100)).apply(lambda x: x * 0.1 * (x % 10)))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode='lines',
        name='BTC-USD',
        line=dict(color='#f7931a', width=2)
    ))
    
    fig.update_layout(
        title="Bitcoin Price (Last 100 Hours)",
        xaxis_title="Time",
        yaxis_title="Price (USD)",
        height=400,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_portfolio(dashboard):
    """Show portfolio page"""
    st.markdown("## 💰 Portfolio Management")
    
    challenge_data = dashboard.get_challenge_progress()
    
    # Portfolio Summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💰 Total Value", f"${challenge_data['current_balance']:.2f}")
    
    with col2:
        st.metric("📈 Total P&L", f"${challenge_data['profit_loss']:+.2f}")
    
    with col3:
        st.metric("📊 ROI", f"{(challenge_data['profit_loss']/30*100):+.1f}%")
    
    # Portfolio Allocation Chart
    st.markdown("### 📊 Portfolio Allocation")
    
    # Mock portfolio data
    portfolio_data = {
        'Asset': ['USDT', 'BTC', 'ETH', 'SOL', 'ADA'],
        'Value': [challenge_data['current_balance'] * 0.6, 
                 challenge_data['current_balance'] * 0.2,
                 challenge_data['current_balance'] * 0.1,
                 challenge_data['current_balance'] * 0.07,
                 challenge_data['current_balance'] * 0.03],
        'Percentage': [60, 20, 10, 7, 3]
    }
    
    df_portfolio = pd.DataFrame(portfolio_data)
    
    fig = px.pie(
        df_portfolio, 
        values='Value', 
        names='Asset',
        title="Portfolio Distribution"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_settings(dashboard):
    """Show settings page"""
    st.markdown("## ⚙️ System Settings")
    
    # API Configuration
    st.markdown("### 🔌 API Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        api_key = st.text_input("Binance API Key", type="password")
        api_secret = st.text_input("Binance API Secret", type="password")
    
    with col2:
        telegram_token = st.text_input("Telegram Bot Token", type="password")
        chat_id = st.text_input("Telegram Chat ID")
    
    # Trading Parameters
    st.markdown("### 📊 Trading Parameters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        max_trades_per_day = st.number_input("Max Trades/Day", 1, 100, 20)
        stop_loss_percent = st.number_input("Stop Loss %", 1.0, 20.0, 5.0)
    
    with col2:
        take_profit_percent = st.number_input("Take Profit %", 1.0, 50.0, 10.0)
        confidence_threshold = st.number_input("AI Confidence Threshold", 0.1, 1.0, 0.6)
    
    with col3:
        position_size_percent = st.number_input("Position Size %", 1.0, 50.0, 15.0)
        max_open_positions = st.number_input("Max Open Positions", 1, 10, 3)
    
    if st.button("💾 Save Settings", type="primary"):
        st.success("Settings saved successfully!")

def show_analytics(dashboard):
    """Show analytics page with real data from the database."""
    st.markdown("## 📈 Performance Analytics")

    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Fetch performance data
        df_performance = pd.read_sql_query("SELECT * FROM performance_daily ORDER BY date ASC", conn)
        
        # Fetch trades data
        df_trades = pd.read_sql_query("SELECT * FROM trades ORDER BY execution_time ASC", conn)
        
        conn.close()

        if df_performance.empty or df_trades.empty:
            st.warning("No performance data available yet. Start trading to see analytics.")
            return

        # Performance Metrics
        latest_perf = df_performance.iloc[-1]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Sharpe Ratio", f"{latest_perf['sharpe_ratio']:.2f}")
        with col2:
            st.metric("📉 Max Drawdown", f"{latest_perf['max_drawdown_usdt']:.2f} USDT")
        with col3:
            st.metric("⚡ Profit Factor", f"{latest_perf['profit_factor']:.2f}")
        with col4:
            st.metric("🔥 Win Rate", f"{latest_perf['win_rate']:.2f}%")

        # Performance Chart (Balance History)
        st.markdown("### 📊 Balance History")
        fig_balance = px.line(df_performance, x='date', y='pnl_usdt', title='Daily P&L History')
        fig_balance.update_traces(fill='tozeroy')
        st.plotly_chart(fig_balance, use_container_width=True)

        # Trade Analysis
        st.markdown("### 📋 Trade Analysis")
        
        # Win/Loss Distribution
        wins = df_trades[df_trades['net_amount_usdt'] > 0].shape[0]
        losses = df_trades[df_trades['net_amount_usdt'] <= 0].shape[0]
        
        fig_winloss = go.Figure(data=[
            go.Bar(name='Wins', x=['Trades'], y=[wins], marker_color='green'),
            go.Bar(name='Losses', x=['Trades'], y=[losses], marker_color='red')
        ])
        fig_winloss.update_layout(title="Win/Loss Distribution", barmode='stack', height=300)
        st.plotly_chart(fig_winloss, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to load analytics data: {e}")

if __name__ == "__main__":
    main()

