import streamlit as st
import logging
import sys
from datetime import datetime
from streamlit_option_menu import option_menu
from utils.data_loader import CryptoDataLoader
from utils.auto_trader import AutoTrader
from utils.wallet_manager import WalletManager
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
    initial_sidebar_state="collapsed"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
    }
    div[data-testid="stSidebarNav"] {
        background-color: #1E1E1E;
        padding-top: 2rem;
        position: fixed;
        top: 0;
        left: 0;
        height: 100%;
        width: auto;
    }
    .main {
        margin-left: 0;
    }
    .css-1d391kg {
        background-color: #1E1E1E;
    }
    section[data-testid="stSidebar"] > div {
        background-color: #1E1E1E;
        padding: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"] {
        background-color: #1E1E1E;
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #2E2E2E;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'page' not in st.session_state:
        st.session_state.page = "Dashboard"
    if 'bot_running' not in st.session_state:
        st.session_state.bot_running = False

def render_sidebar():
    """Render collapsible sidebar with navigation"""
    with st.sidebar:
        st.title("🤖 AurumBot")

        selected = option_menu(
            "",  # empty menu title for cleaner look
            ["Dashboard", "Trading", "Wallet"],
            icons=['house', 'graph-up', 'wallet2'],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#1E1E1E"},
                "icon": {"color": "orange", "font-size": "25px"}, 
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px"},
                "nav-link-selected": {"background-color": "#2E2E2E"},
            }
        )

        st.session_state.page = selected
        return selected

def render_trading_chart(data_loader: CryptoDataLoader):
    """Render trading chart with key metrics"""
    st.subheader("Market Analysis")

    col1, col2 = st.columns([3, 1])

    with col1:
        selected_coin = st.selectbox("Select Trading Pair", ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"])
        timeframe = st.select_slider("Timeframe", options=["1H", "4H", "1D", "1W"], value="1D")

        df = data_loader.get_historical_data(selected_coin, timeframe)

        if df is not None and not df.empty:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                  vertical_spacing=0.03, row_heights=[0.7, 0.3])

            # Candlestick chart
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'], name="OHLC"
            ), row=1, col=1)

            # Volume bars
            fig.add_trace(go.Bar(
                x=df.index, y=df['Volume'], name="Volume",
                marker_color='rgba(128,128,128,0.5)'
            ), row=2, col=1)

            fig.update_layout(
                height=600,
                template='plotly_dark',
                xaxis_rangeslider_visible=False,
                margin=dict(l=0, r=0, t=30, b=0)
            )

            st.plotly_chart(fig, use_container_width=True)

    with col2:
        current_price = df['Close'].iloc[-1] if df is not None and not df.empty else 0
        price_change = ((current_price - df['Open'].iloc[-1])/df['Open'].iloc[-1] * 100
                       if df is not None and not df.empty else 0)

        st.metric("Current Price", f"${current_price:,.2f}", f"{price_change:+.2f}%")

        # Trading controls
        st.subheader("Trading Controls")
        if st.button("Start Bot" if not st.session_state.bot_running else "Stop Bot"):
            st.session_state.bot_running = not st.session_state.bot_running

        st.metric("24h PnL", "+$234.56", "+2.3%")
        st.metric("Open Positions", "3")

def render_wallet_section(wallet_manager: WalletManager):
    """Render wallet information and balances"""
    st.subheader("Wallet Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Balance", "$10,432.21", "+5.2%")
    with col2:
        st.metric("Available Balance", "$8,654.32")
    with col3:
        st.metric("Locked in Orders", "$1,777.89")

    # Asset distribution
    st.subheader("Asset Distribution")
    assets = {
        "BTC": 0.25,
        "ETH": 2.5,
        "SOL": 45.0,
        "USDT": 5000.0
    }

    # Create two columns for assets
    cols = st.columns(len(assets))
    for col, (asset, amount) in zip(cols, assets.items()):
        col.metric(asset, f"{amount:g}")

def main():
    try:
        initialize_session_state()

        # Initialize components
        data_loader = CryptoDataLoader()
        wallet_manager = WalletManager(user_id="default")  # Using default user ID for now

        # Render sidebar and get selected page
        selected_page = render_sidebar()

        # Main content area
        if selected_page == "Dashboard":
            st.title("Trading Dashboard")
            render_trading_chart(data_loader)
            render_wallet_section(wallet_manager)

        elif selected_page == "Trading":
            st.title("Advanced Trading")
            render_trading_chart(data_loader)

        elif selected_page == "Wallet":
            st.title("Wallet Management")
            render_wallet_section(wallet_manager)

    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()