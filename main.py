# Page config must be the first Streamlit command
import streamlit as st
st.set_page_config(
    page_title="AurumBot Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

import plotly.graph_objects as go
import logging
from datetime import datetime
from utils.data_loader import CryptoDataLoader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize data loader
@st.cache_resource
def get_data_loader():
    return CryptoDataLoader()

try:
    data_loader = get_data_loader()
except Exception as e:
    st.error(f"Error initializing data loader: {str(e)}")
    logger.error(f"Data loader initialization error: {str(e)}")
    st.stop()

# Sidebar
with st.sidebar:
    st.title("🤖 AurumBot Pro")
    selected_tab = st.selectbox(
        "Navigation",
        ["Dashboard", "Trading", "Analytics", "Settings"]
    )

    try:
        # Get available coins from data loader
        available_coins = data_loader.get_available_coins()
        crypto = st.selectbox(
            "Select Cryptocurrency",
            list(available_coins.keys())
        )
    except Exception as e:
        st.error("Error loading available cryptocurrencies")
        logger.error(f"Error loading coins: {str(e)}")
        st.stop()

    if selected_tab == "Trading":
        st.subheader("Trading Settings")
        risk_level = st.slider("Risk Level", 1, 10, 5)
        strategy = st.selectbox(
            "Strategy",
            ["Scalping", "Swing Trading", "Meme Coin"]
        )

# Main content
if selected_tab == "Dashboard":
    try:
        # Show loading message
        with st.spinner('Loading market data...'):
            # Create columns for metrics
            col1, col2, col3 = st.columns(3)

            # Fetch data using data loader
            logger.info(f"Fetching data for {crypto}")
            data = data_loader.get_historical_data(crypto, period="1d", interval="1m")

            if data is not None and not data.empty:
                # Calculate metrics
                current_price = data['Close'].iloc[-1]
                price_change = ((current_price - data['Close'].iloc[0]) / 
                              data['Close'].iloc[0] * 100)
                daily_volume = data['Volume'].sum()
                volatility = data['Returns'].std() * 100 if 'Returns' in data.columns else 0

                # Display metrics with proper formatting
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
                    st.metric(
                        "Volatility",
                        f"{volatility:.2f}%"
                    )

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

                # Update layout with better styling
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

                # Display technical indicators
                st.subheader("Technical Indicators")

                # RSI Chart
                if 'RSI' in data.columns:
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

                # MACD Chart
                if all(col in data.columns for col in ['MACD', 'Signal']):
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

            else:
                st.error(f"No data available for {crypto}")
                logger.error(f"Empty data received for {crypto}")

    except Exception as e:
        st.error("Error loading market data. Please try again later.")
        logger.error(f"Dashboard error: {str(e)}")

elif selected_tab == "Analytics":
    st.subheader("Performance Analytics")
    st.info("Analytics features coming soon!")

elif selected_tab == "Settings":
    st.subheader("Bot Settings")
    st.info("Settings configuration coming soon!")