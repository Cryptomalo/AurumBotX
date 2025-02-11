import os
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from sqlalchemy import text
from dotenv import load_dotenv

from utils.data_loader import CryptoDataLoader
from utils.indicators import TechnicalIndicators
from utils.notifications import TradingNotifier
from utils.wallet_manager import WalletManager
from utils.subscription_manager import SubscriptionManager
from utils.auto_trader import AutoTrader
from utils.database import get_db, init_db
from typing import Optional

# Load environment variables
load_dotenv()

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

# Configurazione pagina
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

def get_user_id_by_username(username: str) -> Optional[int]:
    """Recupera l'ID utente dal database"""
    try:
        with next(get_db()) as session:
            result = session.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": username}
            ).fetchone()
            return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting user ID: {e}")
        return None

def verify_activation_code(username: str, code: str) -> bool:
    """Verifica il codice di attivazione e attiva l'abbonamento"""
    try:
        subscription_manager = SubscriptionManager()
        success = subscription_manager.activate_subscription(code, username)
        if success:
            user_id = get_user_id_by_username(username)
            if user_id:
                st.session_state.user_id = user_id
                st.session_state.username = username
                logger.info(f"Successfully activated subscription for user: {username}")
                return True
            else:
                logger.error(f"User ID not found for username: {username}")
        else:
            logger.warning(f"Failed to activate subscription for user: {username}")
        return False
    except Exception as e:
        logger.error(f"Error verifying activation code: {e}")
        return False

def show_login_page():
    """Mostra la pagina di login con i piani di abbonamento"""
    try:
        st.title("🌟 AurumBot Trading Platform")
        st.header("📊 Piani di Abbonamento")

        subscription_manager = SubscriptionManager()
        available_plans = subscription_manager.get_available_plans()

        if not available_plans:
            st.error("Errore nel caricamento dei piani di abbonamento")
            return

        cols = st.columns(len(available_plans))
        for idx, plan in enumerate(available_plans):
            with cols[idx]:
                st.markdown(f"""
                ### {'🥉' if plan['duration_months'] == 3 else '🥈' if plan['duration_months'] == 6 else '🥇'} {plan['name']}
                - Durata: {plan['duration_months']} mesi
                - Prezzo: €{plan['price']:.2f}
                - {plan['description']}
                """)

        with st.form("login_form"):
            username = st.text_input("Username", 
                                  help="Inserisci il tuo username",
                                  placeholder="Il tuo username")
            activation_code = st.text_input("Codice di Attivazione", 
                                        help="Inserisci il codice di attivazione ricevuto",
                                        type="password",
                                        placeholder="AB12345...")
            submit = st.form_submit_button("Accedi")

            if submit:
                if not username or not activation_code:
                    st.error("Inserisci username e codice di attivazione")
                elif verify_activation_code(username, activation_code):
                    st.success("Login effettuato con successo!")
                    st.session_state.authenticated = True
                    st.experimental_rerun()
                else:
                    st.error("Codice di attivazione non valido o già utilizzato")

    except Exception as e:
        logger.error(f"Error in login page: {e}")
        st.error("Si è verificato un errore. Riprova più tardi.")

def show_dashboard():
    """Mostra la dashboard principale dopo il login"""
    st.title(f"Benvenuto, {st.session_state.username}! 👋")

    # Verifica abbonamento
    subscription_manager = SubscriptionManager()
    if not subscription_manager.check_subscription(st.session_state.user_id):
        st.error("Il tuo abbonamento è scaduto. Inserisci un nuovo codice di attivazione.")
        st.session_state.authenticated = False
        st.experimental_rerun()
        return

    if st.sidebar.button("Logout"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.experimental_rerun()

    # Initialize components
    data_loader = CryptoDataLoader()
    indicators = TechnicalIndicators()
    notifier = TradingNotifier()
    auto_trader = None # Initialize auto_trader here

    # Sidebar Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Wallet", "Trade", "Orders", "History", "Settings"]
    )

    if page == "Dashboard":
        st.header("Trading Dashboard")

        # Portfolio Overview
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Portfolio Value", f"${st.session_state.balance:,.2f}", "+5.2%")
        with col2:
            st.metric("24h Change", "+$521.43", "+5.21%")
        with col3:
            st.metric("Active Positions", len(st.session_state.positions))

        # Market Analysis Section
        st.subheader("Market Analysis")
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
                auto_trader = None

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
                fig = go.Figure(data=[go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close']
                )])

                fig.update_layout(
                    title=f"{selected_pair} Price Chart",
                    yaxis_title="Price (USD)",
                    template="plotly_dark",
                    height=600
                )

                st.plotly_chart(fig, use_container_width=True)

                # Technical Indicators
                st.subheader("Technical Indicators")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("RSI", f"{df['RSI'].iloc[-1]:.2f}")
                with col2:
                    st.metric("MACD", f"{df['MACD'].iloc[-1]:.2f}")

                # Display Active Orders
                st.subheader("Active Orders")
                if st.session_state.trading_active and auto_trader:
                    st.write(auto_trader.portfolio['open_orders'])
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
        st.info("Trading interface coming soon...")

    elif page == "Orders":
        st.title("Order History")
        # Add order history here
        st.info("Order history coming soon...")

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
        st.info("Account settings coming soon...")


def main():
    """Funzione principale dell'applicazione"""
    try:
        # Initialize database if needed
        init_db()

        if not st.session_state.authenticated:
            show_login_page()
        else:
            if not st.session_state.user_id:
                logger.error("Invalid session: user_id not found")
                st.error("Sessione non valida. Effettua nuovamente il login.")
                st.session_state.authenticated = False
                st.experimental_rerun()
                return

            # Verifica abbonamento
            subscription_manager = SubscriptionManager()
            if not subscription_manager.check_subscription(st.session_state.user_id):
                logger.warning(f"Subscription expired for user: {st.session_state.username}")
                st.error("Il tuo abbonamento è scaduto. Inserisci un nuovo codice di attivazione.")
                st.session_state.authenticated = False
                st.experimental_rerun()
                return

            show_dashboard()

    except Exception as e:
        logger.error(f"Critical error in main: {e}")
        st.error("Si è verificato un errore critico. Contatta il supporto.")

if __name__ == "__main__":
    main()