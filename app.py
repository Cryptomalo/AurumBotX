import logging
import os
import sys
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Verifica se il modulo streamlit_option_menu è installato
try:
    from streamlit_option_menu import option_menu
except ImportError:
    os.system('pip install streamlit-option-menu')
    from streamlit_option_menu import option_menu

from utils.auto_trader import AutoTrader
from utils.data_loader import CryptoDataLoader
from utils.backup_manager import BackupManager
import json
from pathlib import Path
import asyncio
import nest_asyncio
import plotly.express as px # Added import for plotly.express

# Enable nested event loops for Streamlit
nest_asyncio.apply()

# Assicurati che il percorso del file di log esista
log_dir = 'logs/system'
os.makedirs(log_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'app.log'), mode='a'),
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
        'wallet_error': None,
        'login_attempted': False,
        'data_loader_initialized': False,  # New flag
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
        .error-box {{
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: {COLORS['error']}33;
            border: 1px solid {COLORS['error']};
            margin: 1rem 0;
        }}
        .metric-card {{
            background-color: rgba(255, 255, 255, 0.1);
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }}
        .nav-menu {{
            background-color: rgba(255, 255, 255, 0.05);
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }}
        </style>
    """, unsafe_allow_html=True)

def render_wallet_login():
    """Render wallet login interface"""
    try:
        st.markdown(f"""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='color: {COLORS["primary"]}; font-size: 3em; margin-bottom: 1rem;'>
                🌟 AurumBot
            </h1>
            <p style='font-size: 1.5em; color: {COLORS["text"]}; margin: 1rem 0;'>
                Advanced AI-Powered Trading Platform
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.wallet_error:
            st.markdown(f"""
            <div class='error-box'>
                <p style='color: {COLORS["error"]};'>
                    {st.session_state.wallet_error}
                </p>
            </div>
            """, unsafe_allow_html=True)

        # Features showcase
        col1, col2, col3 = st.columns(3)

        feature_style = f"""
            padding: 2rem;
            background-color: rgba(255,255,255,0.05);
            border-radius: 10px;
            min-height: 200px;
            text-align: center;
            margin: 1rem 0;
        """

        with col1:
            st.markdown(f"""
            <div style='{feature_style}'>
                <h3 style='color: {COLORS["primary"]};'>🤖 AI Trading</h3>
                <p>Advanced ML algorithms for optimal trading decisions</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style='{feature_style}'>
                <h3 style='color: {COLORS["primary"]};'>📊 Real-time Analysis</h3>
                <p>Instant market insights and performance metrics</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style='{feature_style}'>
                <h3 style='color: {COLORS["primary"]};'>🔒 Secure Trading</h3>
                <p>Enterprise-grade security for your assets</p>
            </div>
            """, unsafe_allow_html=True)

        # Wallet connection
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])

        with col2:
            if st.button("🔗 Connect Wallet", use_container_width=True, key="connect_wallet"):
                try:
                    # Simulate wallet connection
                    st.session_state.login_attempted = True
                    st.session_state.wallet_connected = True
                    st.session_state.wallet_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
                    st.session_state.wallet_error = None
                    st.rerun()
                except Exception as e:
                    logger.error(f"Wallet connection error: {str(e)}")
                    st.session_state.wallet_error = "Unable to connect wallet. Please try again."
                    st.session_state.wallet_connected = False
                    st.session_state.wallet_address = None
                    st.rerun()
    except Exception as e:
        logger.error(f"Error in wallet login: {str(e)}")
        st.error("An error occurred during login. Please try again.")

def render_header():
    """Render application header"""
    try:
        col1, col2, col3 = st.columns([1,2,1])

        with col1:
            st.markdown("🌟", help="AurumBot")

        with col2:
            st.title("🌟 AurumBot Trading Platform")

        with col3:
            if st.session_state.wallet_connected and st.session_state.wallet_address:
                col3.markdown(f"""
                <div style='text-align: right;'>
                    <img src="assets/profile.png" width="50" style="border-radius: 25px;">
                    <p style='margin-top: 5px;'>🔗 {st.session_state.wallet_address[:6]}...{st.session_state.wallet_address[-4:]}</p>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Disconnect", key="disconnect_wallet"):
                    st.session_state.wallet_connected = False
                    st.session_state.wallet_address = None
                    st.session_state.wallet_error = None
                    st.rerun()
    except Exception as e:
        logger.error(f"Error in header: {str(e)}")
        st.error("An error occurred in the header. Please refresh the page.")

def render_navigation():
    """Render main navigation menu"""
    try:
        selected = option_menu(
            menu_title=None,
            options=["Dashboard", "Trading", "Portfolio", "Analytics", "Profile", "Settings"],
            icons=['house', 'currency-bitcoin', 'wallet2', 'graph-up', 'person', 'gear'],
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "rgba(255, 255, 255, 0.05)"},
                "icon": {"color": COLORS['text'], "font-size": "25px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "center",
                    "margin": "0px",
                    "--hover-color": COLORS['secondary']
                },
                "nav-link-selected": {"background-color": COLORS['primary']},
            }
        )
        return selected
    except Exception as e:
        logger.error(f"Error in navigation: {str(e)}")
        st.error("An error occurred in the navigation menu. Please refresh the page.")
        return "Dashboard"

def render_dashboard():
    """Render modern dashboard with enhanced visualizations"""
    try:
        st.title("Trading Dashboard")

        # Top metrics row
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Portfolio Value",
                value="$10,000",
                delta="↑ $500 (5%)",
                help="Current portfolio value including all assets"
            )

        with col2:
            st.metric(
                label="24h Trading Volume",
                value="$25,000",
                delta="↑ 15%",
                help="Total trading volume in the last 24 hours"
            )

        with col3:
            st.metric(
                label="Active Positions",
                value="3",
                help="Number of currently open trading positions"
            )

        # Charts row
        st.subheader("Market Overview")
        col1, col2 = st.columns([2, 1])

        with col1:
            # Price chart
            if st.session_state.data_loader:
                df = load_market_data("BTC/USDT")
                if df is not None and not df.empty:
                    chart = create_candlestick_chart(df)
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                    else:
                        st.error("Could not create chart. Please try again.")
                else:
                    st.warning("Loading market data...")

        with col2:
            # Portfolio composition
            portfolio_data = {
                'Asset': ['BTC', 'ETH', 'SOL', 'USDT'],
                'Value': [4000, 3000, 2000, 1000]
            }
            df_portfolio = pd.DataFrame(portfolio_data)

            fig = px.pie(
                df_portfolio, 
                values='Value', 
                names='Asset',
                title='Portfolio Composition'
            )
            st.plotly_chart(fig, use_container_width=True)

        # Bottom row - Trading activity and alerts
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Recent Trading Activity")
            activity_data = [
                {"time": "10:30", "pair": "BTC/USDT", "type": "Buy", "amount": "$1000"},
                {"time": "11:15", "pair": "ETH/USDT", "type": "Sell", "amount": "$500"},
                {"time": "12:00", "pair": "SOL/USDT", "type": "Buy", "amount": "$300"}
            ]

            st.table(activity_data)

        with col2:
            st.subheader("Active Alerts")
            alerts = [
                "BTC price above $45,000",
                "ETH volume spike detected",
                "New trading opportunity in SOL"
            ]

            for alert in alerts:
                st.info(alert)

    except Exception as e:
        st.error(f"Error rendering dashboard: {str(e)}")


def create_candlestick_chart(df):
    """Create an interactive candlestick chart"""
    try:
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            increasing_line_color='#00C853',
            decreasing_line_color='#FF4444'
        )])

        fig.update_layout(
            title='Price Chart',
            yaxis_title='Price',
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_rangeslider_visible=False,
            height=400
        )

        return fig
    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")
        return None

def render_trading_controls():
    """Render modern trading interface"""
    try:
        st.subheader("Trading Controls")

        # Trading form in card-like container
        st.markdown("""
        <div style='background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 10px; margin: 20px 0;'>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            trading_pair = st.selectbox(
                "Select Trading Pair",
                ["BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT", "SHIB/USDT"],
                index=0,
                key="trading_pair_select"
            )
            initial_balance = st.number_input(
                "Initial Balance (USDT)",
                min_value=10.0,
                value=1000.0,
                step=10.0,
                key="initial_balance_input"
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

        # Control buttons
        st.markdown("---")
        col1, col2, col3 = st.columns([1,2,1])

        with col2:
            testnet_mode = st.checkbox("Testnet Mode", value=True)

            start_button = st.button(
                "▶️ Start Trading" if not st.session_state.get('trading_active', False) else "⏹️ Stop Trading",
                use_container_width=True,
                key="trading_control_button"
            )

            if start_button:
                if not st.session_state.get('trading_active', False):
                    if not st.session_state.get('initialization_running', False):
                        st.session_state.initialization_running = True
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            success = loop.run_until_complete(initialize_bot_and_loader(
                                trading_pair, initial_balance, risk_per_trade, testnet_mode
                            ))
                            loop.close()

                            if success:
                                st.session_state.trading_active = True
                                st.success(f"Bot initialized and running for {trading_pair}")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error during startup: {str(e)}")
                            logger.error(f"Startup error: {str(e)}")
                        finally:
                            st.session_state.initialization_running = False
                else:
                    try:
                        if st.session_state.bot:
                            st.session_state.bot.stop_trading()
                        st.session_state.trading_active = False
                        st.session_state.bot = None
                        st.session_state.data_loader = None
                        st.info("Trading stopped successfully")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error stopping trading: {str(e)}")
                        logger.error(f"Stop trading error: {str(e)}")

            if st.session_state.bot:
                if st.button("⏹️ Stop Trading", use_container_width=True):
                    st.session_state.bot = None
                    st.session_state.data_loader = None
                    st.info("Trading stopped")
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        logger.error(f"Error in trading controls: {str(e)}")
        st.error("An error occurred while rendering trading controls. Please try again.")

def render_settings():
    """Render modern settings interface"""
    try:
        st.subheader("⚙️ Settings")

        tabs = st.tabs(["General", "Notifications", "Wallet"])

        with tabs[0]:
            st.subheader("General Settings")
            col1, col2 = st.columns(2)
            with col1:
                st.selectbox(
                    "Theme",
                    ["dark", "light"],
                    index=0 if st.session_state.theme == "dark" else 1,
                    key="theme"
                )
            with col2:
                st.checkbox(
                    "Enable Auto Trading",
                    value=st.session_state.auto_trade,
                    key="auto_trade"
                )

        with tabs[1]:
            st.subheader("Notification Settings")
            col1, col2 = st.columns(2)
            with col1:
                st.checkbox(
                    "Enable Notifications",
                    value=st.session_state.notifications_enabled,
                    key="notifications_enabled"
                )
            with col2:
                st.number_input(
                    "Price Alert Threshold (%)",
                    min_value=0.1,
                    value=5.0,
                    step=0.1
                )

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
                    st.rerun()

    except Exception as e:
        logger.error(f"Error in settings: {str(e)}")
        st.error("An error occurred while rendering settings. Please try again.")

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

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_market_data(symbol, period='1d'):
    """Load market data safely with improved error handling and caching"""
    try:
        if not st.session_state.data_loader:
            logger.warning("Data loader not initialized")
            return None

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Add loading message
        logger.info(f"Loading market data for {symbol}...")

        df = loop.run_until_complete(st.session_state.data_loader.get_historical_data(symbol, period))
        loop.close()

        if df is not None and len(df) > 0:
            logger.info(f"Successfully loaded {len(df)} rows of market data for {symbol}")
            st.session_state.market_data = df
            return df

        logger.warning(f"No data available for {symbol}")
        return None
    except Exception as e:
        logger.error(f"Error loading market data for {symbol}: {str(e)}")
        return None


def render_profile():
    """Render profile section with Telegram integration"""
    try:
        st.title("Profile")

        st.markdown(f"""
        <div class='metric-card'>
            <h4>Wallet Address</h4>
            <p>{st.session_state.wallet_address if st.session_state.wallet_connected else 'Not Connected'}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Telegram Scanner")
        telegram_enabled = st.checkbox("Enable Telegram Scanner")
        if telegram_enabled:
            st.text_input("Telegram Bot Token")
            st.text_input("Chat ID")
            st.multiselect(
                "Monitor Channels",
                ["Channel 1", "Channel 2", "Channel 3"]
            )

    except Exception as e:
        logger.error(f"Error in profile section: {str(e)}")
        st.error("An error occurred while rendering the profile section. Please try again.")

def render_portfolio():
    """Render portfolio analysis"""
    try:
        st.title("Portfolio Analysis")
        st.subheader("Current Holdings")

        # Example portfolio data
        portfolio_data = {
            'Asset': ['BTC', 'ETH', 'SOL', 'USDT'],
            'Amount': [0.5, 2.0, 10.0, 1000.0],
            'Value (USDT)': [25000, 6000, 2000, 1000]
        }
        df_portfolio = pd.DataFrame(portfolio_data)

        st.table(df_portfolio)

        # Portfolio value over time (example data)
        st.subheader("Portfolio Value Over Time")
        dates = pd.date_range(start="2023-01-01", periods=100)
        values = pd.Series([10000 + i * 50 for i in range(100)], index=dates)

        fig = px.line(values, title="Portfolio Value Over Time")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        logger.error(f"Error rendering portfolio: {str(e)}")
        st.error("An error occurred while rendering the portfolio. Please try again.")

async def initialize_data_loader():
    """Initialize data loader if not already initialized"""
    if not st.session_state.data_loader_initialized:
        try:
            data_loader = CryptoDataLoader(testnet=True)
            await data_loader.initialize()
            st.session_state.data_loader = data_loader
            st.session_state.data_loader_initialized = True
            logger.info("Data loader initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize data loader: {str(e)}")
            st.error("Error initializing market data. Please refresh the page.")

def render_analytics():
    """Render advanced analytics section"""
    try:
        st.title("Advanced Analytics")
        st.subheader("Market Sentiment Analysis")

        # Example sentiment data
        sentiment_data = {
            'Time': pd.date_range(start="2023-01-01", periods=100),
            'Sentiment': pd.Series([0.5 + 0.1 * i for i in range(100)])
        }
        df_sentiment = pd.DataFrame(sentiment_data)

        fig = px.line(df_sentiment, x='Time', y='Sentiment', title="Market Sentiment Over Time")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Correlation Matrix")
        # Example correlation data
        correlation_data = {
            'BTC': [1, 0.8, 0.6],
            'ETH': [0.8, 1, 0.7],
            'SOL': [0.6, 0.7, 1]
        }
        df_correlation = pd.DataFrame(correlation_data, index=['BTC', 'ETH', 'SOL'])

        fig = px.imshow(df_correlation, text_auto=True, title="Asset Correlation Matrix")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        logger.error(f"Error rendering analytics: {str(e)}")
        st.error("An error occurred while rendering analytics. Please try again.")

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

        # Initialize data loader asynchronously
        if not st.session_state.data_loader_initialized:
            asyncio.run(initialize_data_loader())

        # Handle wallet connection state
        if not st.session_state.wallet_connected:
            render_wallet_login()
            return

        # Main application interface
        render_header()
        selected_tab = render_navigation()
        st.session_state.selected_tab = selected_tab

        if selected_tab == "Dashboard":
            if st.session_state.data_loader_initialized:
                render_dashboard()
            else:
                st.warning("Initializing market data, please wait...")
        elif selected_tab == "Trading":
            render_trading_controls()
        elif selected_tab == "Portfolio":
            render_portfolio()  # Call the new function
        elif selected_tab == "Analytics":
            render_analytics()  # Call the new function
        elif selected_tab == "Profile":
            render_profile()
        elif selected_tab == "Settings":
            render_settings()

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An unexpected error occurred. Please refresh the page.")

if __name__ == "__main__":
    main()