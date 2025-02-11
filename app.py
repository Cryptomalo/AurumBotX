import streamlit as st
import logging
import sys
from datetime import datetime
from streamlit_option_menu import option_menu
from utils.data_loader import CryptoDataLoader
from utils.auto_trader import AutoTrader
from utils.wallet_manager import WalletManager
from utils.sentiment_analyzer import SentimentAnalyzer
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="AurumBot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #0E1117;
    }
    .stApp {
        background-color: #0E1117;
    }
    .css-1d391kg {
        background-color: #1E1E1E;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 1px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E1E1E;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
        color: white;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2E2E2E;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'active_wallets' not in st.session_state:
        st.session_state.active_wallets = []
    if 'bot_running' not in st.session_state:
        st.session_state.bot_running = False

def render_sidebar():
    """Render sidebar with navigation and settings"""
    with st.sidebar:
        st.title("🤖 AurumBot")

        # User profile section
        if st.session_state.authenticated:
            st.subheader(f"Welcome, {st.session_state.current_user}")

        # Navigation
        selected = option_menu(
            "Main Menu",
            ["Dashboard", "Trading", "Wallets", "Analysis", "Settings"],
            icons=['house', 'graph-up', 'wallet2', 'bar-chart', 'gear'],
            menu_icon="cast",
            default_index=0,
        )

        # Trading settings if on trading page
        if selected == "Trading":
            st.subheader("Trading Settings")
            initial_balance = st.number_input("Initial Balance ($)", min_value=100, value=1000)
            risk_level = st.slider("Risk Level (%)", min_value=1, max_value=10, value=2)

            if st.button("Start Trading", type="primary"):
                st.session_state.bot_running = True
                st.success("Bot started successfully!")

            if st.button("Stop Trading", type="secondary"):
                st.session_state.bot_running = False
                st.error("Bot stopped")

        return selected

def render_dashboard(data_loader: CryptoDataLoader):
    """Render main dashboard view"""
    st.title("Market Overview")

    # Multi-coin price overview
    cols = st.columns(4)
    for idx, (symbol, name) in enumerate(list(data_loader.supported_coins.items())[:4]):
        with cols[idx]:
            price = data_loader.get_current_price(symbol)
            if price:
                st.metric(
                    name,
                    f"${price:,.2f}",
                    delta=f"{data_loader.get_market_summary(symbol).get('price_change_24h', 0):.2f}%"
                )

    # Main chart
    st.subheader("Price Action")
    selected_coin = st.selectbox("Select Trading Pair", list(data_loader.supported_coins.keys()))
    df = data_loader.get_historical_data(selected_coin)

    if df is not None and not df.empty:
        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add candlestick
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name="OHLC"
            ),
            secondary_y=False,
        )

        # Add volume bars
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                name="Volume",
                opacity=0.3
            ),
            secondary_y=True,
        )

        # Update layout
        fig.update_layout(
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)

        # Market metrics
        col1, col2, col3 = st.columns(3)
        market_data = data_loader.get_market_summary(selected_coin)

        with col1:
            st.metric("24h Volume", f"${market_data.get('volume_24h', 0):,.0f}")
        with col2:
            st.metric("RSI", f"{market_data.get('rsi', 0):.2f}")
        with col3:
            st.metric("Volatility", f"{market_data.get('volatility', 0):.2f}%")

def render_trading_view(data_loader: CryptoDataLoader):
    """Render trading interface"""
    st.title("Trading Interface")

    col1, col2 = st.columns([2, 1])

    with col1:
        selected_coin = st.selectbox("Trading Pair", list(data_loader.supported_coins.keys()))

        if st.session_state.bot_running:
            st.success("Bot is actively trading")

            # Show active trading signals
            bot = AutoTrader(
                symbol=selected_coin,
                initial_balance=1000,  # Get from settings
                risk_per_trade=0.02    # Get from settings
            )

            signals = bot.get_trading_signals()
            if signals:
                st.subheader("Active Signals")
                for signal in signals:
                    with st.container():
                        st.info(
                            f"Signal: {signal['action']} "
                            f"Price: ${signal['price']:.2f} "
                            f"Confidence: {signal['confidence']:.2f}%"
                        )

    with col2:
        st.subheader("Performance")
        metrics = {
            "Daily PnL": "+$234.56",
            "Win Rate": "67%",
            "Active Trades": "3"
        }

        for label, value in metrics.items():
            st.metric(label, value)

def render_wallet_view():
    """Render wallet management interface"""
    st.title("Wallet Management")

    # Add wallet
    with st.expander("Add New Wallet"):
        col1, col2 = st.columns(2)
        with col1:
            wallet_name = st.text_input("Wallet Name")
            wallet_type = st.selectbox("Wallet Type", ["Hot Wallet", "Cold Storage", "Exchange"])
        with col2:
            wallet_address = st.text_input("Wallet Address")
            wallet_chain = st.selectbox("Blockchain", ["Ethereum", "Bitcoin", "Solana", "Binance Smart Chain"])

        if st.button("Add Wallet"):
            st.success(f"Wallet {wallet_name} added successfully!")

    # Display wallets
    st.subheader("Your Wallets")

    # Example wallets
    example_wallets = [
        {"name": "Trading Wallet", "type": "Hot Wallet", "balance": "$5,432.10", "chain": "Ethereum"},
        {"name": "Cold Storage", "type": "Cold Storage", "balance": "$15,678.90", "chain": "Bitcoin"},
        {"name": "DEX Wallet", "type": "Hot Wallet", "balance": "$2,345.67", "chain": "Solana"}
    ]

    for wallet in example_wallets:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            col1.write(f"**{wallet['name']}**")
            col2.write(wallet['type'])
            col3.write(wallet['chain'])
            col4.write(wallet['balance'])

def main():
    try:
        initialize_session_state()

        # Initialize components
        data_loader = CryptoDataLoader()

        # Render sidebar and get selected page
        selected_page = render_sidebar()

        # Render selected page
        if selected_page == "Dashboard":
            render_dashboard(data_loader)
        elif selected_page == "Trading":
            render_trading_view(data_loader)
        elif selected_page == "Wallets":
            render_wallet_view()
        # Add other pages as needed

    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()