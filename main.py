import os
import logging
from datetime import datetime, timedelta

# Setup logging con più dettagli
logging.basicConfig(
    level=logging.DEBUG,  # Cambiato a DEBUG per maggiori informazioni
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

logger.info("Starting imports...")
try:
    import streamlit as st
    logger.info("Streamlit imported successfully")
    import pandas as pd
    logger.info("Pandas imported successfully")
    import plotly.graph_objects as go
    logger.info("Plotly imported successfully")

    from utils.data_loader import CryptoDataLoader
    from utils.indicators import TechnicalIndicators
    logger.info("Custom modules imported successfully")
except Exception as e:
    logger.error(f"Error during imports: {str(e)}")
    raise

def safe_metric_change(current, previous):
    """Calcola il cambiamento percentuale in modo sicuro"""
    try:
        current = float(current.iloc[0]) if hasattr(current, 'iloc') else float(current)
        previous = float(previous.iloc[0]) if hasattr(previous, 'iloc') else float(previous)

        if pd.isna(current) or pd.isna(previous) or previous == 0:
            return 0.0
        return ((current / previous) - 1.0) * 100
    except Exception as e:
        logger.error(f"Errore nel calcolo della metrica: {e}")
        return 0.0

def format_volume(volume):
    """Formatta il volume in modo leggibile"""
    try:
        volume = float(volume.iloc[0]) if hasattr(volume, 'iloc') else float(volume)
        if pd.isna(volume):
            return "N/A"
        if volume >= 1e9:
            return f"{volume/1e9:.1f}B"
        if volume >= 1e6:
            return f"{volume/1e6:.1f}M"
        if volume >= 1e3:
            return f"{volume/1e3:.1f}K"
        return f"{volume:.0f}"
    except Exception as e:
        logger.error(f"Errore nella formattazione del volume: {e}")
        return "N/A"

def main():
    try:
        logger.info("Setting up Streamlit page config...")
        st.set_page_config(
            page_title="AurumBot Trading Platform",
            page_icon="🌟",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        logger.info("Page config set successfully")

        # Initialize components
        logger.info("Initializing components...")
        data_loader = CryptoDataLoader()
        logger.info("Data loader initialized")

        # Sidebar configuration
        st.sidebar.title("🛠️ Trading Controls")

        # Select cryptocurrency
        selected_coin = st.sidebar.selectbox(
            "Select Cryptocurrency",
            options=list(data_loader.supported_coins.keys()),
            format_func=lambda x: f"{data_loader.supported_coins[x]} ({x})"
        )
        logger.info(f"Selected coin: {selected_coin}")

        # Time period selector
        timeframe = st.sidebar.selectbox(
            "Select Timeframe",
            options=['1d', '7d', '30d', '90d'],
            format_func=lambda x: {
                '1d': '1 Day',
                '7d': '1 Week',
                '30d': '1 Month',
                '90d': '3 Months'
            }[x]
        )
        logger.info(f"Selected timeframe: {timeframe}")

        # Main content
        st.title("🌟 AurumBot Trading Platform")

        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Market Analysis",
            "🤖 Auto Trading",
            "💼 Portfolio",
            "⚙️ Settings"
        ])

        with tab1:
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("Price Chart")
                logger.info("Fetching historical data...")
                df = data_loader.get_historical_data(selected_coin, period=timeframe)
                logger.info(f"Data fetched: {'success' if df is not None else 'failed'}")

                if df is not None and not df.empty:
                    logger.info("Creating price chart...")
                    fig = go.Figure(data=[go.Candlestick(
                        x=df.index,
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close']
                    )])

                    fig.update_layout(
                        title=f"{data_loader.supported_coins[selected_coin]} Price Chart",
                        yaxis_title="Price (USD)",
                        xaxis_title="Date",
                        template="plotly_dark",
                        height=500
                    )

                    st.plotly_chart(fig, use_container_width=True)
                    logger.info("Chart displayed successfully")

                    # Technical indicators
                    st.subheader("Technical Indicators")
                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        if 'RSI' in df.columns:
                            current_rsi = df['RSI'].iloc[-1]
                            prev_rsi = df['RSI'].iloc[-2]
                            if not pd.isna(current_rsi) and not pd.isna(prev_rsi):
                                st.metric(
                                    "RSI",
                                    f"{float(current_rsi):.2f}",
                                    f"{float(current_rsi - prev_rsi):.2f}"
                                )

                    with col_b:
                        if 'MACD' in df.columns:
                            current_macd = df['MACD'].iloc[-1]
                            prev_macd = df['MACD'].iloc[-2]
                            if not pd.isna(current_macd) and not pd.isna(prev_macd):
                                st.metric(
                                    "MACD",
                                    f"{float(current_macd):.2f}",
                                    f"{float(current_macd - prev_macd):.2f}"
                                )

                    with col_c:
                        if 'Volume' in df.columns:
                            current_vol = df['Volume'].iloc[-1]
                            prev_vol = df['Volume'].iloc[-2]
                            vol_change = safe_metric_change(current_vol, prev_vol)
                            st.metric(
                                "Volume",
                                format_volume(current_vol),
                                f"{vol_change:.1f}%"
                            )
                else:
                    logger.error("Unable to load price data")
                    st.error("Unable to load price data. Please try again later.")

            with col2:
                st.subheader("Market Overview")
                current_price = data_loader.get_current_price(selected_coin)

                if current_price is not None:
                    price_change = 0.0
                    if df is not None and not df.empty:
                        prev_price = df['Close'].iloc[-2]
                        price_change = safe_metric_change(current_price, prev_price)

                    st.metric(
                        "Current Price",
                        f"${current_price:,.2f}",
                        f"{price_change:.2f}%"
                    )
                else:
                    st.error("Unable to fetch current price")

        with tab2:
            st.subheader("Auto Trading Settings")
            col1, col2 = st.columns(2)

            with col1:
                risk_per_trade = st.slider(
                    "Risk per Trade (%)",
                    min_value=0.1,
                    max_value=5.0,
                    value=1.0,
                    step=0.1
                )

                strategy = st.selectbox(
                    "Trading Strategy",
                    ["Scalping", "Swing Trading", "Mean Reversion"]
                )

            with col2:
                take_profit = st.number_input(
                    "Take Profit (%)",
                    min_value=0.1,
                    max_value=100.0,
                    value=2.0
                )

                stop_loss = st.number_input(
                    "Stop Loss (%)",
                    min_value=0.1,
                    max_value=100.0,
                    value=1.0
                )

            if st.button("Start Auto Trading"):
                st.warning("Auto trading feature coming soon!")

        with tab3:
            st.subheader("Portfolio Overview")
            st.info("Connect your wallet to view portfolio details")

            if st.button("Connect Wallet"):
                st.warning("Wallet connection feature coming soon!")

        with tab4:
            st.subheader("Platform Settings")
            with st.expander("Notification Settings"):
                st.checkbox("Enable Email Notifications")
                st.checkbox("Enable Telegram Notifications")
                if st.button("Save Settings"):
                    st.success("Settings saved successfully!")

        st.sidebar.info("Version: 1.0.0")
        logger.info("Application setup completed successfully")

    except Exception as e:
        logger.error(f"Critical error in main app: {str(e)}")
        st.error("An unexpected error occurred. Please try again later.")

if __name__ == "__main__":
    logger.info("Starting main application...")
    main()