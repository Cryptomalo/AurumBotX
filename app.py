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

# Configurazione logging
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

def init_session_state():
    """Inizializza lo stato della sessione"""
    defaults = {
        'bot': None,
        'data_loader': None,
        'last_update': datetime.now(),
        'error_count': 0,
        'market_data': None,
        'wallet_connected': False,
        'theme': 'light',
        'notifications_enabled': True,
        'auto_trade': False,
        'selected_tab': "Dashboard",
        'initialization_running': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

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
            st.write(f"Wallet Connected")

def render_wallet_login():
    """Render the wallet login page"""
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h1>🌟 Welcome to AurumBot</h1>
        <p style='font-size: 1.2em; margin: 20px 0;'>The Advanced AI-Powered Trading Platform</p>
        <p>Connect your wallet to start your trading journey</p>
    </div>
    """, unsafe_allow_html=True)

    # Features showcase
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        ### 🤖 AI Trading
        Leverage advanced AI algorithms for smart trading decisions
        """)

    with col2:
        st.markdown("""
        ### 📊 Real-time Analysis
        Get instant market insights and performance metrics
        """)

    with col3:
        st.markdown("""
        ### 🔒 Secure Trading
        Connect your wallet for safe and secure transactions
        """)

    st.markdown("---")

    # Wallet connection
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if not st.session_state.wallet_connected:
            if st.button("🔗 Connect Wallet", use_container_width=True):
                # Here you would implement actual wallet connection logic
                st.session_state.wallet_connected = True
                st.rerun()
        else:
            st.success("✅ Wallet Connected")
            if st.button("Disconnect"):
                st.session_state.wallet_connected = False
                st.rerun()

def render_settings():
    """Render settings page"""
    st.subheader("⚙️ Settings")

    tabs = st.tabs(["General", "Notifications", "Wallet", "Telegram", "Advanced"])

    with tabs[0]:
        st.subheader("General Settings")
        st.session_state.theme = st.selectbox(
            "Theme",
            ["light", "dark"],
            index=0 if st.session_state.theme == "light" else 1
        )
        st.session_state.auto_trade = st.checkbox(
            "Auto Trading",
            value=st.session_state.auto_trade
        )

    with tabs[1]:
        st.subheader("Notification Settings")
        st.session_state.notifications_enabled = st.checkbox(
            "Enable Notifications",
            value=st.session_state.notifications_enabled
        )
        st.number_input("Price Alert Threshold (%)", min_value=0.1, value=5.0)

    with tabs[2]:
        st.subheader("Wallet Settings")
        if st.session_state.wallet_connected:
            st.success("Wallet Connected")
            st.text("Address: 0x...")  # Would show actual wallet address
            if st.button("Disconnect Wallet"):
                st.session_state.wallet_connected = False
        else:
            if st.button("Connect Wallet"):
                st.session_state.wallet_connected = True

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
        st.number_input("API Request Timeout (seconds)", min_value=1, value=30)
        st.number_input("Cache Duration (minutes)", min_value=1, value=5)
        st.checkbox("Enable Debug Logging")

def render_dashboard():
    """Render the main dashboard"""
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
            pnl_color = "green" if pnl >= 0 else "red"

            st.metric("Current Balance", f"${current_balance:.2f}")
            st.metric("PNL", f"${pnl:.2f}", delta=f"{(pnl/initial_balance)*100:.1f}%")

            # Add PNL Chart
            if hasattr(st.session_state.bot, 'balance_history'):
                pnl_df = pd.DataFrame(st.session_state.bot.balance_history)
                st.line_chart(pnl_df.set_index('timestamp')['balance'])

    with col3:
        st.subheader("Top Meme Coins")
        st.markdown("""
        | Coin | 24h Change |
        |------|------------|
        | DOGE | +5.2% |
        | SHIB | +3.1% |
        | PEPE | +8.7% |
        """)

def show_main_app():
    """Main application UI"""
    render_header()

    if not st.session_state.wallet_connected:
        render_wallet_login()
        return

    # Main navigation after login
    selected_tab = st.sidebar.selectbox(
        "Main Menu",
        ["Dashboard", "Trading", "Portfolio", "Analytics", "Social", "Settings"],
    )
    st.session_state.selected_tab = selected_tab

    if st.session_state.selected_tab == "Dashboard":
        render_dashboard()
    elif st.session_state.selected_tab == "Settings":
        render_settings()
    elif st.session_state.selected_tab == "Portfolio":
        st.title("Portfolio Analysis")
        render_portfolio_status()
    elif st.session_state.selected_tab == "Analytics":
        st.title("Advanced Analytics")
        # Add analytics content here
    elif st.session_state.selected_tab == "Social":
        st.title("Social Trading")
        # Add social trading content here
    elif st.session_state.selected_tab == "Trading":
        render_trading_controls()

def create_candlestick_chart(df):
    """Crea un grafico candlestick interattivo"""
    try:
        if df is None or df.empty:
            return None

        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close']
        )])

        fig.update_layout(
            title='Price Chart',
            yaxis_title='Price',
            template='plotly_dark',
            xaxis_rangeslider_visible=False,
            height=600
        )

        return fig
    except Exception as e:
        logger.error(f"Errore creazione grafico: {str(e)}")
        return None

def render_trading_controls():
    """Render trading controls"""
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
            ["Scalping", "Swing", "Meme Coin"],
            index=0
        )
        risk_per_trade = st.slider(
            "Risk per Trade (%)",
            min_value=0.1,
            max_value=5.0,
            value=2.0,
            step=0.1
        )

    testnet_mode = st.checkbox("Testnet Mode", value=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Start"):
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

    with col2:
        if st.button("⏹️ Stop"):
            st.session_state.bot = None
            st.session_state.data_loader = None
            st.info("Trading stopped")
            st.rerun()

async def initialize_bot_and_loader(trading_pair: str, initial_balance: float, risk_per_trade: float, testnet_mode: bool):
    """Initialize bot and loader asynchronously"""
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

def render_portfolio_status():
    """Visualizza lo stato del portfolio"""
    try:
        if not st.session_state.bot:
            return

        st.subheader("Stato Portfolio")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Bilancio Attuale", f"${st.session_state.bot.balance:.2f}")
            profit_loss = st.session_state.bot.balance - st.session_state.bot.initial_balance
            st.metric("P/L Totale", f"${profit_loss:.2f}")

        with col2:
            if st.session_state.bot.is_in_position:
                st.info("Trade Attivo")
                if st.session_state.bot.current_position:
                    position = st.session_state.bot.current_position
                    st.json({
                        "Prezzo Entrata": f"${position['entry_price']:.2f}",
                        "Dimensione": f"{position['size']:.6f}",
                        "Strategia": position['strategy'],
                        "Target": f"${position['target_price']:.2f}",
                        "Stop Loss": f"${position['stop_loss']:.2f}"
                    })
    except Exception as e:
        logger.error(f"Errore visualizzazione portfolio: {str(e)}")
        st.error("Errore nell'aggiornamento del portfolio")

def main():
    try:
        st.set_page_config(
            page_title="AurumBot Trading Platform",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        init_session_state()
        show_main_app()
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An unexpected error occurred. Please reload the page.")

if __name__ == "__main__":
    main()