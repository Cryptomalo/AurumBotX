import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import bcrypt
from utils.data_loader import CryptoDataLoader
from utils.database import get_db
import sqlalchemy as sa
import logging
from utils.indicators import TechnicalIndicators
from utils.auto_trader import AutoTrader
from utils.notifications import TradingNotifier
from utils.wallet_manager import WalletManager

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


# Page config
st.set_page_config(
    page_title="AurumBot Trading Platform",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'trading_active' not in st.session_state:
    st.session_state.trading_active = False
if 'selected_strategy' not in st.session_state:
    st.session_state.selected_strategy = None
if 'balance' not in st.session_state:
    st.session_state.balance = 10000.0
if 'positions' not in st.session_state:
    st.session_state.positions = []


def login_user(username, password):
    try:
        with next(get_db()) as session:
            # Query user
            result = session.execute(
                sa.text("SELECT id, username, password_hash FROM users WHERE username = :username"),
                {"username": username}
            ).fetchone()

            if result and bcrypt.checkpw(password.encode('utf-8'), result[2].encode('utf-8')):
                st.session_state.authenticated = True
                st.session_state.user_id = result[0]
                st.session_state.username = result[1]
                # Update last login
                session.execute(
                    sa.text("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = :user_id"),
                    {"user_id": result[0]}
                )
                session.commit()
                return True
        return False
    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return False


def register_user(username, email, password):
    try:
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        with next(get_db()) as session:
            # Insert new user
            session.execute(
                sa.text("""
                INSERT INTO users (username, email, password_hash)
                VALUES (:username, :email, :password_hash)
                """),
                {
                    "username": username,
                    "email": email,
                    "password_hash": password_hash.decode('utf-8')
                }
            )
            session.commit()
            return True
    except Exception as e:
        st.error(f"Registration error: {str(e)}")
        return False


def show_login_page():
    st.title("Welcome to AurumBot Trading Platform")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                if login_user(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")

    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Username")
            email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Register")

            if submit:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif register_user(new_username, email, new_password):
                    st.success("Registration successful! Please login.")
                else:
                    st.error("Registration failed")


def show_main_dashboard():
    # Initialize components
    data_loader = CryptoDataLoader()
    indicators = TechnicalIndicators()
    notifier = TradingNotifier()
    auto_trader = None

    # Sidebar
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.username}!")

        # Navigation
        page = st.radio(
            "Navigation",
            ["Dashboard", "Wallet", "Trade", "Orders", "History", "Settings"]
        )

        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()

    if page == "Dashboard":
        st.title("Trading Dashboard")

        # Portfolio Overview
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Portfolio Value", f"${st.session_state.balance:,.2f}", "+5.2%")  # using session state
        with col2:
            st.metric("24h Change", "+$521.43", "+5.21%")
        with col3:
            st.metric("Active Positions", len(st.session_state.positions))  # using session state

        # Market Overview and Trading Controls (from original code, adapted)
        st.subheader("Market Analysis & Trading Controls")
        selected_pair = st.selectbox(
            "Select Trading Pair",
            data_loader.get_available_coins().keys()
        )

        risk_level = st.select_slider(
            "Risk Level",
            options=["Low", "Medium", "High"],
            value="Medium"
        )

        if st.button("🟢 Start Trading" if not st.session_state.trading_active else "🔴 Stop Trading"):
            st.session_state.trading_active = not st.session_state.trading_active
            if st.session_state.trading_active:
                auto_trader = AutoTrader(
                    symbol=selected_pair,
                    initial_balance=st.session_state.balance,
                    risk_per_trade=0.02 if risk_level == "Low" else 0.05 if risk_level == "Medium" else 0.1
                )
            else:
                auto_trader = None  # added to handle stopping trading

        # Timeframe selector
        timeframe = st.select_slider(
            "Timeframe",
            options=["1h", "4h", "1d", "1w"],
            value="1d"
        )

        try:
            # Get historical data
            df = data_loader.get_historical_data(selected_pair, period=timeframe)

            if df is not None:
                # Add technical indicators
                df = indicators.add_rsi(df)
                df = indicators.add_macd(df)

                # Create main chart
                fig = go.Figure()

                # Candlestick
                fig.add_trace(go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name='OHLC'
                ))

                # Customize chart
                fig.update_layout(
                    title=f"{selected_pair} Price Chart",
                    yaxis_title="Price (USD)",
                    template="plotly_dark",
                    height=600,
                    margin=dict(l=50, r=50, t=50, b=50)
                )

                st.plotly_chart(fig, use_container_width=True)

                # Display indicators
                indicators_tab, orders_tab = st.tabs(["📊 Indicators", "📝 Orders"])

                with indicators_tab:
                    col_ind1, col_ind2 = st.columns(2)
                    with col_ind1:
                        st.metric("RSI", f"{df['RSI'].iloc[-1]:.2f}")
                    with col_ind2:
                        st.metric("MACD", f"{df['MACD'].iloc[-1]:.2f}")

                with orders_tab:
                    if st.session_state.trading_active and auto_trader:
                        st.write("Active Orders:", auto_trader.portfolio['open_orders'])
                    else:
                        st.info("Start trading to see active orders")

            else:
                st.error("Failed to load market data")

        except Exception as e:
            logger.error(f"Error in chart generation: {str(e)}")
            st.error("Error generating market analysis")

        # Retained from original, adapted to use session state
        st.subheader("🎯 Active Trades")
        for pos in st.session_state.positions:  # Iterate through positions
            with st.container():
                st.markdown(f"""
                <div class="trade-card">
                    <small>{pos['pair']}</small><br>
                    {pos['action']} @{pos['price']}
                </div>
                """, unsafe_allow_html=True)

        # Trading Stats (from original code, adapted)
        st.subheader("📊 Statistics")

        if st.session_state.trading_active and auto_trader:
            metrics = auto_trader.portfolio['performance_metrics']
            st.metric("Total Profit", f"${metrics['total_profit']:.2f}")
            st.metric("Win Rate", f"{metrics['win_rate']:.1%}")
            st.metric("Avg Profit/Trade", f"${metrics['avg_profit_per_trade']:.2f}")
        else:
            st.info("Start trading to see statistics")

        # Recent Activity (retained from original, mostly)
        st.subheader("📝 Recent Activity")
        col_logs1, col_logs2 = st.columns([3, 2])

        with col_logs1:
            st.markdown("""
            | Time | Action | Pair | Price | Status |
            |------|--------|------|-------|--------|
            | 12:45 | Buy | BTC/USDT | 48,235 | Completed |
            | 12:30 | Sell | ETH/USDT | 2,890 | Completed |
            | 12:15 | Buy | SOL/USDT | 98.5 | Pending |
            """)

        with col_logs2:
            st.subheader("System Status")
            st.markdown("✅ All systems operational")
            st.markdown("✅ Connected to exchanges")
            st.markdown("✅ AI models running")

    elif page == "Wallet":
        st.title("Wallet Management")

        if st.session_state.user_id:
            wallet_manager = WalletManager(st.session_state.user_id)

            # Add New Wallet
            with st.expander("➕ Add New Wallet"):
                with st.form("add_wallet"):
                    wallet_address = st.text_input("Wallet Address")
                    chain = st.selectbox(
                        "Blockchain",
                        ["Ethereum", "Binance Smart Chain", "Solana", "Bitcoin"]
                    )
                    label = st.text_input("Wallet Label (Optional)")
                    submit = st.form_submit_button("Add Wallet")

                    if submit and wallet_address:
                        if wallet_manager.add_wallet(wallet_address, chain, label):
                            st.success("Wallet added successfully!")
                        else:
                            st.error("Failed to add wallet")

            # Display Wallets
            st.subheader("Connected Wallets")
            wallets = wallet_manager.get_wallets()

            if wallets:
                for wallet in wallets:
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"""
                            **{wallet['label'] or 'Wallet'}** ({wallet['chain']})  
                            `{wallet['address']}`  
                            Added: {wallet['added_on']}
                            """)
                        with col2:
                            if st.button("Deposit", key=f"dep_{wallet['address']}"):
                                st.info(f"Send funds to: {wallet['address']}")
                            if st.button("Withdraw", key=f"wit_{wallet['address']}"):
                                amount = st.number_input("Amount", min_value=0.0, key=f"amt_{wallet['address']}")
                                if st.button("Confirm Withdrawal", key=f"conf_{wallet['address']}"):
                                    if wallet_manager.record_transaction("withdrawal", amount, "USD", wallet['address']):
                                        st.success("Withdrawal initiated")
                                    else:
                                        st.error("Withdrawal failed")
            else:
                st.info("No wallets connected. Add a wallet to get started.")

    elif page == "Trade":
        st.title("Trade")
        # Add trading interface here

    elif page == "Orders":
        st.title("Order History")
        # Add order history here

    elif page == "History":
        st.title("Transaction History")

        if st.session_state.user_id:
            wallet_manager = WalletManager(st.session_state.user_id)
            transactions = wallet_manager.get_transactions()

            if transactions:
                # Summary metrics
                deposits = sum(t['amount'] for t in transactions if t['type'] == 'deposit')
                withdrawals = sum(t['amount'] for t in transactions if t['type'] == 'withdrawal')

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Deposits", f"${deposits:,.2f}")
                with col2:
                    st.metric("Total Withdrawals", f"${withdrawals:,.2f}")

                # Transactions table
                st.dataframe(
                    pd.DataFrame(transactions).sort_values(by='date', ascending=False),
                    use_container_width=True
                )
            else:
                st.info("No transactions found")

    elif page == "Settings":
        st.title("Account Settings")
        # Add settings interface here


# Main app logic
def main():
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_main_dashboard()


if __name__ == "__main__":
    main()