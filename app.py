
import streamlit as st
import logging
import sys
from datetime import datetime
from utils.data_loader import CryptoDataLoader
from utils.auto_trader import AutoTrader
from utils.wallet_manager import WalletManager
import plotly.graph_objects as go

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

def main():
    try:
        # Page config
        st.set_page_config(
            page_title="AurumBot",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Initialize components
        data_loader = CryptoDataLoader()
        available_coins = data_loader.get_available_coins()

        # Sidebar
        with st.sidebar:
            st.title("🤖 AurumBot")
            
            # Trading pair selection
            selected_coin = st.selectbox(
                "Trading Pair",
                list(available_coins.keys())
            )
            
            # Trading settings
            st.subheader("Trading Settings")
            initial_balance = st.number_input(
                "Initial Balance ($)", 
                min_value=100,
                value=1000
            )
            risk_level = st.slider(
                "Risk Level (%)", 
                min_value=1,
                max_value=10,
                value=2
            )

            # Start/Stop bot
            if st.button("Start Trading", type="primary"):
                st.session_state.bot_running = True
                st.success("Bot started successfully!")

            if st.button("Stop Trading", type="secondary"):
                st.session_state.bot_running = False
                st.error("Bot stopped")

        # Main content
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Price Chart")
            df = data_loader.get_historical_data(selected_coin)
            
            if df is not None and not df.empty:
                fig = go.Figure(data=[go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close']
                )])
                fig.update_layout(
                    height=500,
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Market Overview")
            
            # Current price
            current_price = data_loader.get_current_price(selected_coin)
            if current_price:
                st.metric(
                    "Current Price",
                    f"${current_price:,.2f}"
                )

            # Market summary
            market_data = data_loader.get_market_summary(selected_coin)
            if market_data:
                st.metric(
                    "24h Change",
                    f"{market_data['price_change_24h']:.2f}%"
                )
                st.metric(
                    "RSI",
                    f"{market_data['rsi']:.2f}"
                )

        # Trading signals
        st.subheader("Recent Trading Signals")
        if 'bot_running' in st.session_state and st.session_state.bot_running:
            bot = AutoTrader(
                symbol=selected_coin,
                initial_balance=initial_balance,
                risk_per_trade=risk_level/100
            )
            signals = bot.get_trading_signals()
            
            if signals:
                for signal in signals:
                    with st.container():
                        st.info(
                            f"Signal: {signal['action']} "
                            f"Price: ${signal['price']:.2f} "
                            f"Confidence: {signal['confidence']:.2f}%"
                        )

    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
