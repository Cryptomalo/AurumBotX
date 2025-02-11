import os
import sys
import logging
from datetime import datetime
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

from utils.data_loader import CryptoDataLoader

# Application Constants
APP_NAME = "AurumBot Pro"
DEFAULT_RISK_LEVEL = 5
SUPPORTED_STRATEGIES = ["Scalping", "Swing Trading", "Meme Coin"]

class AppConfig:
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.setup_logging()

    def setup_logging(self):
        """Configure logging with both file and console handlers"""
        self.logger = logging.getLogger(APP_NAME)
        self.logger.setLevel(logging.DEBUG)

        # File handler
        file_handler = logging.FileHandler(
            self.log_dir / f"{APP_NAME.lower()}_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def initialize_streamlit(self):
        """Initialize Streamlit configuration"""
        try:
            self.logger.info("Initializing Streamlit application...")
            st.set_page_config(
                page_title=APP_NAME,
                page_icon="🤖",
                layout="wide",
                initial_sidebar_state="expanded"
            )
            self.logger.info("Streamlit configuration initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Streamlit: {str(e)}", exc_info=True)
            return False

class DataManager:
    def __init__(self, logger):
        self.logger = logger
        self.data_loader = None

    @st.cache_resource(show_spinner=True)
    def initialize_data_loader(self):
        """Initialize and test the data loader"""
        try:
            self.logger.info("Initializing data loader...")
            self.data_loader = CryptoDataLoader()

            # Test data loader
            self.logger.debug("Testing data loader...")
            test_data = self.data_loader.get_historical_data(
                "BTC-USD", 
                period="1d", 
                interval="1h"
            )

            if test_data is None:
                raise Exception("Failed to fetch test data")

            self.logger.info("Data loader initialized and tested successfully")
            return self.data_loader

        except Exception as e:
            self.logger.error(
                f"Failed to initialize data loader: {str(e)}", 
                exc_info=True
            )
            raise

class DashboardUI:
    def __init__(self, logger, data_manager):
        self.logger = logger
        self.data_manager = data_manager

    def render_sidebar(self):
        """Render sidebar with navigation and controls"""
        try:
            self.logger.debug("Rendering sidebar...")
            with st.sidebar:
                st.title(f"🤖 {APP_NAME}")

                available_coins = self.data_manager.data_loader.get_available_coins()

                selected_tab = st.selectbox(
                    "Navigation",
                    ["Dashboard", "Trading", "Analytics", "Settings"]
                )

                crypto = st.selectbox(
                    "Select Cryptocurrency",
                    list(available_coins.keys())
                )

                if selected_tab == "Trading":
                    st.subheader("Trading Settings")
                    risk_level = st.slider(
                        "Risk Level", 
                        1, 
                        10, 
                        DEFAULT_RISK_LEVEL
                    )
                    strategy = st.selectbox(
                        "Strategy",
                        SUPPORTED_STRATEGIES
                    )

            self.logger.debug(f"Sidebar rendered with crypto: {crypto}")
            return selected_tab, crypto

        except Exception as e:
            self.logger.error(
                f"Error rendering sidebar: {str(e)}", 
                exc_info=True
            )
            st.error("Error loading sidebar components")
            st.stop()

    def render_price_metrics(self, data):
        """Render price metrics section"""
        try:
            col1, col2, col3 = st.columns(3)

            current_price = data['Close'].iloc[-1]
            price_change = ((current_price - data['Close'].iloc[0]) / 
                          data['Close'].iloc[0] * 100)
            daily_volume = data['Volume'].sum()

            with col1:
                st.metric(
                    "Current Price",
                    f"${current_price:,.2f}",
                    f"{price_change:+.2f}%"
                )

            with col2:
                st.metric(
                    "24h Volume",
                    f"${daily_volume/1000000:,.2f}M"
                )

            with col3:
                if 'Returns' in data.columns:
                    volatility = data['Returns'].std() * 100
                    st.metric("Volatility", f"{volatility:.2f}%")

            self.logger.debug("Price metrics rendered successfully")

        except Exception as e:
            self.logger.error(
                f"Error rendering price metrics: {str(e)}", 
                exc_info=True
            )
            st.warning("Unable to display price metrics")

    def render_price_chart(self, data):
        """Render main price chart"""
        try:
            fig = go.Figure()

            # Candlestick chart
            fig.add_trace(go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Price'
            ))

            # Add moving averages if available
            if 'Price_MA_50' in data.columns:
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data['Price_MA_50'],
                    name='MA50',
                    line=dict(color='orange')
                ))

            if 'Price_MA_200' in data.columns:
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data['Price_MA_200'],
                    name='MA200',
                    line=dict(color='blue')
                ))

            fig.update_layout(
                title="Price Chart",
                yaxis_title="Price (USD)",
                xaxis_title="Time",
                height=600,
                template="plotly_dark",
                showlegend=True,
                xaxis_rangeslider_visible=False
            )

            st.plotly_chart(fig, use_container_width=True)
            self.logger.debug("Price chart rendered successfully")

        except Exception as e:
            self.logger.error(
                f"Error rendering price chart: {str(e)}", 
                exc_info=True
            )
            st.warning("Unable to display price chart")

    def render_technical_indicators(self, data):
        """Render technical indicators"""
        try:
            if 'RSI' in data.columns:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data['RSI'],
                    name='RSI'
                ))
                fig.add_hline(y=70, line_dash="dash", line_color="red")
                fig.add_hline(y=30, line_dash="dash", line_color="green")
                fig.update_layout(
                    title="RSI (14)",
                    height=300,
                    template="plotly_dark"
                )
                st.plotly_chart(fig, use_container_width=True)

            if all(col in data.columns for col in ['MACD', 'Signal']):
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data['MACD'],
                    name='MACD'
                ))
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data['Signal'],
                    name='Signal'
                ))
                fig.update_layout(
                    title="MACD",
                    height=300,
                    template="plotly_dark"
                )
                st.plotly_chart(fig, use_container_width=True)

            self.logger.debug("Technical indicators rendered successfully")

        except Exception as e:
            self.logger.error(
                f"Error rendering technical indicators: {str(e)}", 
                exc_info=True
            )
            st.warning("Unable to display technical indicators")

    def render_dashboard(self, crypto):
        """Render main dashboard view"""
        try:
            self.logger.info(f"Rendering dashboard for {crypto}...")

            with st.spinner('Loading market data...'):
                data = self.data_manager.data_loader.get_historical_data(
                    crypto, 
                    period="1d", 
                    interval="1m"
                )

                if data is None or data.empty:
                    self.logger.error(f"No data available for {crypto}")
                    st.error(f"No data available for {crypto}")
                    return

                self.logger.debug("Market data loaded successfully")

                # Render all components
                self.render_price_metrics(data)
                self.render_price_chart(data)

                if any(indicator in data.columns for indicator in ['RSI', 'MACD', 'Signal']):
                    st.subheader("Technical Indicators")
                    self.render_technical_indicators(data)

        except Exception as e:
            self.logger.error(
                f"Dashboard rendering failed: {str(e)}", 
                exc_info=True
            )
            st.error("Error loading dashboard data")

def main():
    """Main application entry point"""
    try:
        # Initialize application
        app_config = AppConfig()
        if not app_config.initialize_streamlit():
            st.error("Failed to initialize application")
            st.stop()

        # Initialize data manager
        data_manager = DataManager(app_config.logger)
        data_manager.initialize_data_loader()

        # Initialize UI
        dashboard = DashboardUI(app_config.logger, data_manager)

        # Render main application
        selected_tab, crypto = dashboard.render_sidebar()

        if selected_tab == "Dashboard":
            dashboard.render_dashboard(crypto)
        elif selected_tab == "Analytics":
            st.subheader("Performance Analytics")
            st.info("Analytics features coming soon!")
            app_config.logger.info("Analytics page displayed")
        elif selected_tab == "Settings":
            st.subheader("Bot Settings")
            st.info("Settings configuration coming soon!")
            app_config.logger.info("Settings page displayed")

    except Exception as e:
        app_config.logger.critical(
            f"Critical application error: {str(e)}", 
            exc_info=True
        )
        st.error("A critical error occurred. Please try again later.")
        st.stop()

if __name__ == "__main__":
    main()