import logging
import os
import sys
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.auto_trader import AutoTrader
from utils.data_loader import CryptoDataLoader
from utils.test_suite import AurumBotTester

# Configurazione logging avanzata
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('streamlit_app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class StreamlitApp:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.init_session_state()

    def init_session_state(self):
        """Initialize session state variables"""
        if 'initialized' not in st.session_state:
            try:
                self.logger.info("Initializing session state...")
                st.session_state.update({
                    'initialized': True,
                    'start_time': datetime.now(),
                    'bot': None,
                    'data_loader': None,
                    'selected_strategy': 'scalping',
                    'trade_history': [],
                    'performance_metrics': {},
                    'chart_data': None,
                    'error_count': 0,
                    'last_update': datetime.now()
                })
                self.logger.info("Session state initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize session state: {str(e)}")
                st.error("Error initializing application state. Please try refreshing the page.")

    def create_candlestick_chart(self, df):
        """Create an interactive candlestick chart"""
        try:
            if df is None or df.empty:
                self.logger.warning("No data available for chart creation")
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
                xaxis_rangeslider_visible=False
            )

            return fig
        except Exception as e:
            self.logger.error(f"Failed to create candlestick chart: {str(e)}")
            return None

    def display_trading_controls(self):
        """Display trading controls in the sidebar"""
        try:
            st.sidebar.title("Trading Controls")

            # Trading pair selection
            available_pairs = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT", "SHIB/USDT"]
            trading_pair = st.sidebar.selectbox(
                "Select Trading Pair",
                available_pairs,
                index=0
            )

            # Initial balance input
            initial_balance = st.sidebar.number_input(
                "Initial Balance (USDT)",
                min_value=10.0,
                value=1000.0,
                step=10.0
            )

            # Risk per trade slider
            risk_per_trade = st.sidebar.slider(
                "Risk Per Trade (%)",
                min_value=0.1,
                max_value=5.0,
                value=2.0,
                step=0.1
            )

            # Strategy selection
            strategy = st.sidebar.selectbox(
                "Trading Strategy",
                ["scalping", "swing", "meme_coin"],
                index=0
            )

            # Start/Stop trading buttons
            if st.sidebar.button("Start Trading"):
                try:
                    self.logger.info(f"Initializing bot for {trading_pair}...")
                    st.session_state.bot = AutoTrader(
                        symbol=trading_pair,
                        initial_balance=initial_balance,
                        risk_per_trade=risk_per_trade/100,
                        testnet=True
                    )
                    st.session_state.data_loader = CryptoDataLoader(testnet=True)
                    st.session_state.selected_strategy = strategy
                    st.session_state.last_update = datetime.now()
                    self.logger.info("Bot initialized successfully")
                    st.sidebar.success(f"Bot initialized for {trading_pair}")
                except Exception as e:
                    error_msg = f"Error initializing bot: {str(e)}"
                    self.logger.error(error_msg)
                    st.sidebar.error(error_msg)
                    st.session_state.error_count += 1

            if st.sidebar.button("Stop Trading") and st.session_state.bot:
                st.session_state.bot = None
                st.session_state.data_loader = None
                self.logger.info("Trading stopped")
                st.sidebar.info("Trading stopped")

        except Exception as e:
            self.logger.error(f"Error in trading controls: {str(e)}")
            st.error("Failed to display trading controls")

    def display_market_analysis(self):
        """Display market analysis and charts"""
        try:
            if not st.session_state.bot or not st.session_state.data_loader:
                st.warning("Please initialize the trading bot first")
                return

            # Get market data
            df = st.session_state.data_loader.get_historical_data(
                st.session_state.bot.symbol,
                period='1d'
            )

            if df is not None and not df.empty:
                # Display chart
                chart = self.create_candlestick_chart(df)
                if chart:
                    st.plotly_chart(chart)

                # Market metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current Price", f"${df['Close'].iloc[-1]:.2f}")
                with col2:
                    price_change = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
                    st.metric("24h Change", f"{price_change:.2f}%")
                with col3:
                    st.metric("Volume", f"${df['Volume'].iloc[-1]:,.0f}")
            else:
                st.warning("No market data available")

        except Exception as e:
            self.logger.error(f"Market analysis error: {str(e)}")
            st.error("Failed to display market analysis")
            st.session_state.error_count += 1

    def run(self):
        """Main application entry point"""
        try:
            # Page configuration
            st.set_page_config(
                page_title="AurumBot Trading Platform",
                page_icon="🤖",
                layout="wide",
                initial_sidebar_state="expanded"
            )

            # Custom styling
            st.markdown("""
                <style>
                .reportview-container {
                    background: #0E1117
                }
                .sidebar .sidebar-content {
                    background: #262730
                }
                </style>
                """, unsafe_allow_html=True)

            # Main content
            st.title("🤖 AurumBot Trading Platform")

            # Display system status
            st.sidebar.write("### System Status")
            st.sidebar.write(f"Started: {st.session_state.get('start_time', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}")
            if st.session_state.get('error_count', 0) > 0:
                st.sidebar.warning(f"Errors encountered: {st.session_state.error_count}")

            # Trading controls in sidebar
            self.display_trading_controls()

            # Main content area
            tab1, tab2 = st.tabs(["Market Analysis", "Trading Performance"])

            with tab1:
                self.display_market_analysis()

            with tab2:
                if st.session_state.bot:
                    st.metric("Current Balance", f"${st.session_state.bot.balance:.2f}")
                    if st.session_state.bot.is_in_position:
                        st.info("Active Trade in Progress")
                else:
                    st.info("Start trading to see performance metrics")

        except Exception as e:
            self.logger.error(f"Critical application error: {str(e)}")
            st.error("An unexpected error occurred. Please check the logs for details.")

def main():
    """Application entry point"""
    try:
        app = StreamlitApp()
        app.run()
    except Exception as e:
        st.error(f"Failed to start application: {str(e)}")
        logging.error(f"Application startup error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()