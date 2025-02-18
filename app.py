import logging
import os
import sys
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.auto_trader import AutoTrader
from utils.data_loader import CryptoDataLoader
from utils.backup_manager import BackupManager
from streamlit_option_menu import option_menu
import json
from pathlib import Path
import asyncio
import nest_asyncio

# Enable nested event loops for Streamlit
nest_asyncio.apply()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system/app.log', mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('streamlit').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Color theme
COLORS = {
    'primary': '#FF4B4B',
    'secondary': '#0083B8',
    'background': '#0E1117',
    'text': '#FAFAFA',
    'success': '#00C853',
    'warning': '#FFD700',
    'error': '#FF4444'
}

def init_session_state():
    """Initialize session state with default values"""
    defaults = {
        'bot': None,
        'data_loader': None,
        'last_update': datetime.now(),
        'error_count': 0,
        'market_data': None,
        'wallet_connected': False,
        'theme': 'dark',
        'notifications_enabled': True,
        'auto_trade': False,
        'selected_tab': "Dashboard",
        'initialization_running': False,
        'wallet_address': None,
        'profile': {
            'username': None,
            'email': None,
            'preferences': {}
        }
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def custom_theme():
    """Apply custom theme to Streamlit"""
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: {COLORS['background']};
            color: {COLORS['text']};
        }}
        .stButton>button {{
            color: {COLORS['text']};
            background-color: {COLORS['primary']};
            border: none;
            border-radius: 5px;
            padding: 10px 24px;
            transition: all 0.3s ease;
        }}
        .stButton>button:hover {{
            background-color: {COLORS['secondary']};
            transform: translateY(-2px);
        }}
        .success-box {{
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: {COLORS['success']}33;
            border: 1px solid {COLORS['success']};
            margin: 1rem 0;
        }}
        .metric-card {{
            background-color: rgba(255, 255, 255, 0.1);
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }}
        </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render the application header with profile"""
    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        st.image("assets/logo.png", width=100)
    with col2:
        st.title("🌟 AurumBot Trading Platform")
    with col3:
        if st.session_state.wallet_connected:
            st.image("assets/profile.png", width=50)
            if st.session_state.wallet_address:
                address = st.session_state.wallet_address[:6] + "..." + st.session_state.wallet_address[-4:]
                st.write(f"🔗 {address}")

def render_wallet_login():
    """Render modern wallet login page"""
    st.markdown(f"""
    <div style='text-align: center; padding: 50px;'>
        <h1 style='color: {COLORS["primary"]}; font-size: 3em;'>🌟 AurumBot</h1>
        <p style='font-size: 1.5em; margin: 20px 0; color: {COLORS["text"]};'>
            Advanced AI-Powered Trading Platform
        </p>
        <p style='color: {COLORS["secondary"]}; font-size: 1.2em;'>
            Connect your wallet to start your trading journey
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Features showcase with modern styling
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    feature_style = f"padding: 20px; background-color: rgba(255,255,255,0.05); border-radius: 10px; min-height: 200px;"

    with col1:
        st.markdown(f"""
        <div style='{feature_style}'>
            <h3 style='color: {COLORS["primary"]};'>🤖 AI Trading</h3>
            <p>Advanced algorithms powered by machine learning for optimal trading decisions</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style='{feature_style}'>
            <h3 style='color: {COLORS["primary"]};'>📊 Real-time Analysis</h3>
            <p>Instant market insights and performance metrics with dynamic updates</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style='{feature_style}'>
            <h3 style='color: {COLORS["primary"]};'>🔒 Secure Trading</h3>
            <p>Enterprise-grade security with multi-layer protection for your assets</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Centered wallet connection
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if not st.session_state.wallet_connected:
            connect_btn = st.button("🔗 Connect Wallet", use_container_width=True)
            if connect_btn:
                # Simulate wallet connection
                st.session_state.wallet_connected = True
                st.session_state.wallet_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
                st.rerun()
        else:
            st.success("✅ Wallet Connected")
            if st.button("Disconnect", use_container_width=True):
                st.session_state.wallet_connected = False
                st.session_state.wallet_address = None
                st.rerun()

def render_settings():
    """Render modern settings interface"""
    st.subheader("⚙️ Settings")

    tabs = st.tabs(["General", "Notifications", "Wallet", "Telegram", "Advanced"])

    with tabs[0]:
        st.subheader("General Settings")
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.theme = st.selectbox(
                "Theme",
                ["dark", "light"],
                index=0 if st.session_state.theme == "dark" else 1
            )
        with col2:
            st.session_state.auto_trade = st.checkbox(
                "Enable Auto Trading",
                value=st.session_state.auto_trade
            )

    with tabs[1]:
        st.subheader("Notification Settings")
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.notifications_enabled = st.checkbox(
                "Enable Notifications",
                value=st.session_state.notifications_enabled
            )
        with col2:
            st.number_input("Price Alert Threshold (%)", 
                          min_value=0.1, 
                          value=5.0,
                          step=0.1)

    with tabs[2]:
        st.subheader("Wallet Settings")
        if st.session_state.wallet_connected:
            st.markdown(f"""
            <div class='success-box'>
                <h4>Wallet Connected</h4>
                <p>Address: {st.session_state.wallet_address}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Disconnect Wallet"):
                st.session_state.wallet_connected = False
                st.session_state.wallet_address = None
        else:
            if st.button("Connect Wallet"):
                st.session_state.wallet_connected = True
                st.session_state.wallet_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"

    with tabs[3]:
        st.subheader("Telegram Integration")
        telegram_enabled = st.checkbox("Enable Telegram Scanner", value=False)
        if telegram_enabled:
            st.text_input("Telegram Bot Token")
            st.text_input("Chat ID")
            st.multiselect(
                "Monitor Channels",
                ["Channel 1", "Channel 2", "Channel 3"]
            )

    with tabs[4]:
        st.subheader("Advanced Settings")
        col1, col2 = st.columns(2)
        with col1:
            st.number_input("API Request Timeout (seconds)", 
                          min_value=1, 
                          value=30)
        with col2:
            st.number_input("Cache Duration (minutes)", 
                          min_value=1, 
                          value=5)
        st.checkbox("Enable Debug Logging")

def render_dashboard():
    """Render modern dashboard with enhanced visualizations"""
    col1, col2, col3 = st.columns([2,1,1])

    with col1:
        st.subheader("Market Overview")
        if st.session_state.market_data is not None:
            chart = create_candlestick_chart(st.session_state.market_data)
            if chart:
                st.plotly_chart(chart, use_container_width=True)

    with col2:
        st.subheader("Portfolio Summary")
        if st.session_state.bot:
            current_balance = st.session_state.bot.balance
            initial_balance = st.session_state.bot.initial_balance
            pnl = current_balance - initial_balance
            pnl_color = COLORS['success'] if pnl >= 0 else COLORS['error']

            st.markdown(f"""
            <div class='metric-card'>
                <h4>Current Balance</h4>
                <h2 style='color: {COLORS["text"]};'>${current_balance:.2f}</h2>
            </div>
            <div class='metric-card'>
                <h4>PNL</h4>
                <h2 style='color: {pnl_color};'>${pnl:.2f} ({(pnl/initial_balance)*100:.1f}%)</h2>
            </div>
            """, unsafe_allow_html=True)

            if hasattr(st.session_state.bot, 'balance_history'):
                pnl_df = pd.DataFrame(st.session_state.bot.balance_history)
                st.line_chart(pnl_df.set_index('timestamp')['balance'])

    with col3:
        st.subheader("Top Meme Coins")
        meme_data = [
            {"coin": "DOGE", "change": "+5.2%", "color": COLORS['success']},
            {"coin": "SHIB", "change": "+3.1%", "color": COLORS['success']},
            {"coin": "PEPE", "change": "+8.7%", "color": COLORS['success']}
        ]

        for coin in meme_data:
            st.markdown(f"""
            <div class='metric-card'>
                <h4>{coin['coin']}</h4>
                <h3 style='color: {coin["color"]};'>{coin["change"]}</h3>
            </div>
            """, unsafe_allow_html=True)

def create_candlestick_chart(df):
    """Create interactive candlestick chart with improved styling"""
    try:
        if df is None or df.empty:
            return None

        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            increasing_line_color=COLORS['success'],
            decreasing_line_color=COLORS['error']
        )])

        fig.update_layout(
            title='Price Chart',
            yaxis_title='Price',
            template='plotly_dark',
            plot_bgcolor=COLORS['background'],
            paper_bgcolor=COLORS['background'],
            xaxis_rangeslider_visible=False,
            height=600,
            font=dict(color=COLORS['text'])
        )

        return fig
    except Exception as e:
        logger.error(f"Error creating chart: {str(e)}")
        return None

def render_trading_controls():
    """Render modern trading interface"""
    st.subheader("Trading Controls")

    col1, col2 = st.columns(2)
    with col1:
        trading_pair = st.selectbox(
            "Select Trading Pair",
            ["BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT", "SHIB/USDT"],
            index=0
        )
        initial_balance = st.number_input(
            "Initial Balance (USDT)",
            min_value=10.0,
            value=1000.0,
            step=10.0
        )

    with col2:
        strategy = st.selectbox(
            "Trading Strategy",
            ["AI-Enhanced", "Momentum", "Meme Coin Tracker"],
            index=0
        )
        risk_per_trade = st.slider(
            "Risk per Trade (%)",
            min_value=0.1,
            max_value=5.0,
            value=2.0,
            step=0.1
        )

    st.markdown("---")

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        testnet_mode = st.checkbox("Testnet Mode", value=True)

        if st.button("▶️ Start Trading", use_container_width=True):
            if not st.session_state.initialization_running:
                st.session_state.initialization_running = True
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    success = loop.run_until_complete(initialize_bot_and_loader(
                        trading_pair, initial_balance, risk_per_trade, testnet_mode
                    ))
                    loop.close()
                    if success:
                        st.success(f"Bot initialized for {trading_pair}")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error during startup: {str(e)}")
                    logger.error(f"Startup error: {str(e)}")
                finally:
                    st.session_state.initialization_running = False

        if st.session_state.bot:
            if st.button("⏹️ Stop Trading", use_container_width=True):
                st.session_state.bot = None
                st.session_state.data_loader = None
                st.info("Trading stopped")
                st.rerun()

async def initialize_bot_and_loader(trading_pair: str, initial_balance: float, risk_per_trade: float, testnet_mode: bool):
    """Initialize trading bot and data loader"""
    try:
        bot = AutoTrader(
            symbol=trading_pair,
            initial_balance=initial_balance,
            risk_per_trade=risk_per_trade/100,
            testnet=testnet_mode
        )
        data_loader = CryptoDataLoader(testnet=testnet_mode)
        await data_loader.initialize()
        bot.backup_manager = BackupManager()

        df = await data_loader.get_historical_data(trading_pair, '1d')
        if df is not None and not df.empty:
            st.session_state.market_data = df
            st.session_state.bot = bot
            st.session_state.data_loader = data_loader
            return True
        else:
            st.warning("Cannot load initial data. Please try again in a few seconds.")
            return False
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        st.error(f"Startup error: {str(e)}")
        return False

def main():
    """Main application entry point"""
    try:
        st.set_page_config(
            page_title="AurumBot Trading Platform",
            page_icon="🌟",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        init_session_state()
        custom_theme()

        if not st.session_state.wallet_connected:
            render_wallet_login()
            return

        render_header()

        # Main navigation
        selected = option_menu(
            menu_title=None,
            options=["Dashboard", "Trading", "Portfolio", "Analytics", "Social", "Settings"],
            icons=['house', 'currency-bitcoin', 'wallet2', 'graph-up', 'people', 'gear'],
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
        )
        st.session_state.selected_tab = selected

        if selected == "Dashboard":
            render_dashboard()
        elif selected == "Settings":
            render_settings()
        elif selected == "Trading":
            render_trading_controls()
        elif selected == "Portfolio":
            st.title("Portfolio Analysis")
            # Add portfolio content
        elif selected == "Analytics":
            st.title("Advanced Analytics")
            # Add analytics content
        elif selected == "Social":
            st.title("Social Trading")
            # Add social trading content

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An unexpected error occurred. Please reload the page.")

if __name__ == "__main__":
    main()