import os
import sys
import streamlit as st
import plotly.graph_objects as go
import logging
from datetime import datetime
from utils.data_loader import CryptoDataLoader
from pathlib import Path

# Configura directory per i log
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configurazione logging avanzata
logger = logging.getLogger("AurumBot")
logger.setLevel(logging.DEBUG)

# Handler per file
file_handler = logging.FileHandler(log_dir / f"aurumbot_{datetime.now().strftime('%Y%m%d')}.log")
file_handler.setLevel(logging.DEBUG)

# Handler per console
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Formattazione
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

try:
    logger.info("Starting AurumBot application...")

    # Page config must be the first Streamlit command
    st.set_page_config(
        page_title="AurumBot Pro",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    logger.info("Page config set successfully")

except Exception as e:
    logger.error(f"Failed to set page config: {str(e)}", exc_info=True)
    st.error("Error initializing application. Please try refreshing the page.")
    st.stop()

# Initialize data loader with error handling
@st.cache_resource(show_spinner=True)
def get_data_loader():
    try:
        logger.info("Initializing data loader...")
        loader = CryptoDataLoader()

        # Verifica che il loader funzioni correttamente
        logger.debug("Testing data loader with BTC-USD...")
        test_data = loader.get_historical_data("BTC-USD", period="1d", interval="1h")
        if test_data is None:
            raise Exception("Failed to fetch test data")

        logger.info("Data loader initialized successfully")
        return loader

    except Exception as e:
        logger.error(f"Data loader initialization failed: {str(e)}", exc_info=True)
        raise Exception(f"Data loader initialization failed: {str(e)}")

# Sidebar with error handling
def render_sidebar():
    try:
        logger.debug("Rendering sidebar...")
        with st.sidebar:
            st.title("🤖 AurumBot Pro")

            # Get available coins from data loader
            data_loader = get_data_loader()
            available_coins = data_loader.get_available_coins()

            # Always show these controls
            selected_tab = st.selectbox(
                "Navigation",
                ["Dashboard", "Trading", "Analytics", "Settings"]
            )

            crypto = st.selectbox(
                "Select Cryptocurrency",
                list(available_coins.keys())
            )

            # Trading controls
            st.subheader("Trading Settings")
            risk_level = st.slider("Risk Level", 1, 10, 5)
            strategy = st.selectbox(
                "Strategy",
                ["Scalping", "Swing Trading", "Meme Coin"]
            )
            
            # Add trading buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Buy"):
                    st.success("Buy order placed")
            with col2:
                if st.button("Sell"):
                    st.error("Sell order placed")

            logger.debug(f"Sidebar rendered with selected crypto: {crypto}")
            return selected_tab, crypto, risk_level, strategy

    except Exception as e:
        logger.error(f"Sidebar rendering failed: {str(e)}", exc_info=True)
        st.error("Error loading application components")
        st.stop()

def render_dashboard(crypto):
    try:
        logger.info(f"Rendering dashboard for {crypto}...")

        with st.spinner('Loading market data...'):
            data_loader = get_data_loader()
            data = data_loader.get_historical_data(crypto, period="1d", interval="1m")

            if data is None or data.empty:
                logger.error(f"No data available for {crypto}")
                st.error(f"No data available for {crypto}")
                return

            logger.debug(f"Data loaded successfully for {crypto}")

            # Display metrics
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

            logger.debug("Metrics displayed successfully")

            # Create candlestick chart
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Price'
            ))

            # Add technical indicators
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
                title=f"{crypto} Price Chart",
                yaxis_title="Price (USD)",
                xaxis_title="Time",
                height=600,
                template="plotly_dark",
                showlegend=True,
                xaxis_rangeslider_visible=False
            )

            st.plotly_chart(fig, use_container_width=True)
            logger.debug("Main chart rendered successfully")

            # Display technical indicators
            if any(indicator in data.columns for indicator in ['RSI', 'MACD', 'Signal']):
                st.subheader("Technical Indicators")

                if 'RSI' in data.columns:
                    render_rsi_chart(data)

                if all(col in data.columns for col in ['MACD', 'Signal']):
                    render_macd_chart(data)

            logger.debug("Technical indicators rendered successfully")

    except Exception as e:
        logger.error(f"Dashboard rendering failed: {str(e)}", exc_info=True)
        st.error("Error loading dashboard data")

def render_rsi_chart(data):
    try:
        rsi_fig = go.Figure()
        rsi_fig.add_trace(go.Scatter(
            x=data.index,
            y=data['RSI'],
            name='RSI'
        ))
        rsi_fig.add_hline(y=70, line_dash="dash", line_color="red")
        rsi_fig.add_hline(y=30, line_dash="dash", line_color="green")
        rsi_fig.update_layout(
            title="RSI (14)",
            height=300,
            template="plotly_dark"
        )
        st.plotly_chart(rsi_fig, use_container_width=True)
        logger.debug("RSI chart rendered successfully")

    except Exception as e:
        logger.error(f"RSI chart rendering failed: {str(e)}", exc_info=True)
        st.warning("Unable to display RSI chart")

def render_macd_chart(data):
    try:
        macd_fig = go.Figure()
        macd_fig.add_trace(go.Scatter(
            x=data.index,
            y=data['MACD'],
            name='MACD'
        ))
        macd_fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Signal'],
            name='Signal'
        ))
        macd_fig.update_layout(
            title="MACD",
            height=300,
            template="plotly_dark"
        )
        st.plotly_chart(macd_fig, use_container_width=True)
        logger.debug("MACD chart rendered successfully")

    except Exception as e:
        logger.error(f"MACD chart rendering failed: {str(e)}", exc_info=True)
        st.warning("Unable to display MACD chart")

def main():
    try:
        logger.info("Starting main application loop")
        selected_tab, crypto = render_sidebar()

        if selected_tab == "Dashboard":
            render_dashboard(crypto)
        elif selected_tab == "Analytics":
            st.subheader("Performance Analytics")
            st.info("Analytics features coming soon!")
            logger.info("Analytics page displayed")
        elif selected_tab == "Settings":
            st.subheader("Bot Settings")
            st.info("Settings configuration coming soon!")
            logger.info("Settings page displayed")

    except Exception as e:
        logger.error(f"Main application error: {str(e)}", exc_info=True)
        st.error("An error occurred. Please try refreshing the page.")
        st.stop()

if __name__ == "__main__":
    try:
        logger.info("Application startup initiated")
        main()
        logger.info("Application running successfully")
    except Exception as e:
        logger.critical(f"Critical application error: {str(e)}", exc_info=True)
        st.error("A critical error occurred. Please check the logs and try again.")