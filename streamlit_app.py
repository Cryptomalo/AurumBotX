import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from utils.database import DatabaseManager
import logging
import asyncio
import nest_asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('streamlit_app.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize asyncio for Streamlit
nest_asyncio.apply()

# Configure page
st.set_page_config(
    page_title="SolanaBot Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

try:
    # Initialize database
    db = DatabaseManager()
    if not db.initialize():
        st.error("Error connecting to database. Please check your connection settings.")
        logger.error("Failed to initialize database connection")
    else:
        logger.info("Database connection initialized successfully")
except Exception as e:
    st.error(f"Application initialization error: {str(e)}")
    logger.error(f"Critical error during startup: {str(e)}")

# Load custom CSS
try:
    with open('assets/style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        logger.info("CSS styles loaded successfully")
except Exception as e:
    logger.error(f"Error loading CSS file: {str(e)}")
    st.warning("Some visual styles might not be loaded correctly")

def initialize_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'wallet_address' not in st.session_state:
        st.session_state.wallet_address = None

def main():
    initialize_session_state()

    st.title("🚀 SolanaBot Pro Dashboard")

    if not st.session_state.authenticated:
        st.markdown("""
            <div style='text-align: center; margin-top: 50px;'>
                <h2>Welcome to SolanaBot Pro</h2>
                <p>Please connect your wallet to continue</p>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🔐 Connect Wallet"):
            st.session_state.wallet_address = "Demo_Wallet"
            st.session_state.authenticated = True
            st.experimental_rerun()
    else:
        st.success("Connected to wallet: " + st.session_state.wallet_address)
        st.markdown("### Welcome to your trading dashboard")

        # Basic metrics display
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Portfolio Value", "$10,000", "+5.2%")
        with col2:
            st.metric("24h Trading Volume", "$25,000", "+12.3%")
        with col3:
            st.metric("Active Positions", "3", "-1")

if __name__ == "__main__":
    try:
        main()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An error occurred while running the application")