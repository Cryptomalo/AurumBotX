import os
import sys
import logging
from datetime import datetime

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('streamlit_app.log')
    ]
)
logger = logging.getLogger(__name__)

try:
    # Import Streamlit and other UI components
    import streamlit as st

    # Page config must be first Streamlit command
    st.set_page_config(
        page_title="AurumBot Test",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.write("# Test Page")
    st.write("This is a test page")

except Exception as e:
    logger.error(f"Critical application error: {str(e)}", exc_info=True)
    if 'st' in globals():
        st.error(f"Critical application error: {str(e)}")
    else:
        print(f"Critical error before Streamlit initialization: {str(e)}")

# Custom styling
try:
    st.markdown("""
        <style>
        .reportview-container {
            background: #0E1117
        }
        .sidebar .sidebar-content {
            background: #262730
        }
        .stApp {
            background: #0E1117
        }
        </style>
        """, unsafe_allow_html=True)
except Exception as e:
    logger.error(f"Style application error: {str(e)}")