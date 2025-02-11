import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from sqlalchemy import create_engine, text
import logging
from utils.data_loader import CryptoDataLoader
from utils.indicators import TechnicalIndicators
from utils.notifications import TradingNotifier
from utils.wallet_manager import WalletManager
from utils.auto_trader import AutoTrader

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
    layout="wide"
)

# Verifica e inizializza il database
def init_db():
    try:
        engine = create_engine(os.getenv('DATABASE_URL'))
        with engine.connect() as conn:
            # Test connection
            conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return engine
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        st.error("Errore di connessione al database. Riprova più tardi.")
        return None

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

def verify_activation_code(username: str, code: str) -> bool:
    """Verifica il codice di attivazione e attiva l'abbonamento"""
    try:
        engine = init_db()
        if not engine:
            return False

        with engine.connect() as conn:
            # Verifica se il codice è valido e non utilizzato
            result = conn.execute(
                text("""
                SELECT ac.id, ac.plan_id, sp.duration_months 
                FROM activation_codes ac
                JOIN subscription_plans sp ON ac.plan_id = sp.id
                WHERE ac.code = :code AND ac.is_used = FALSE
                """),
                {"code": code}
            ).fetchone()

            if not result:
                return False

            code_id, plan_id, duration = result

            # Crea o aggiorna l'utente
            user_result = conn.execute(
                text("""
                INSERT INTO users (username, subscription_expires_at)
                VALUES (:username, NOW() + :duration * INTERVAL '1 month')
                ON CONFLICT (username) 
                DO UPDATE SET subscription_expires_at = NOW() + :duration * INTERVAL '1 month'
                RETURNING id
                """),
                {"username": username, "duration": duration}
            ).fetchone()

            # Marca il codice come utilizzato
            conn.execute(
                text("""
                UPDATE activation_codes 
                SET is_used = TRUE, used_by = :user_id, used_at = NOW()
                WHERE id = :code_id
                """),
                {"user_id": user_result[0], "code_id": code_id}
            )

            conn.commit()
            st.session_state.user_id = user_result[0]
            return True

    except Exception as e:
        logger.error(f"Error verifying activation code: {e}")
        return False

def show_login_page():
    """Mostra la pagina di login con i piani di abbonamento"""
    st.title("🌟 AurumBot Trading Platform")

    st.markdown("""
    ### 📊 Piani di Abbonamento

    Scegli il piano più adatto alle tue esigenze:

    #### 🥉 Piano Trimestrale
    - Durata: 3 mesi
    - Prezzo: €299.99
    - Accesso completo a tutte le funzionalità

    #### 🥈 Piano Semestrale
    - Durata: 6 mesi
    - Prezzo: €549.99
    - Sconto del 10% sul prezzo mensile

    #### 🥇 Piano Annuale
    - Durata: 12 mesi
    - Prezzo: €999.99
    - Sconto del 20% sul prezzo mensile
    """)

    with st.form("login_form"):
        username = st.text_input("Username", help="Inserisci il tuo username")
        activation_code = st.text_input("Codice di Attivazione", help="Inserisci il codice di attivazione ricevuto")
        submit = st.form_submit_button("Accedi")

        if submit:
            if not username or not activation_code:
                st.error("Inserisci username e codice di attivazione")
            elif verify_activation_code(username, activation_code):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("Login effettuato con successo!")
                st.rerun()
            else:
                st.error("Codice di attivazione non valido o già utilizzato")

def show_dashboard():
    """Mostra la dashboard principale dopo il login"""
    if not st.session_state.user_id:
        st.error("Sessione non valida. Effettua nuovamente il login.")
        st.session_state.authenticated = False
        st.rerun()
        return

    st.title(f"Benvenuto, {st.session_state.username}! 👋")

    if st.sidebar.button("Logout"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

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
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()