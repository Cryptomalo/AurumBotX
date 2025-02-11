import streamlit as st
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('streamlit_debug.log')
    ]
)
logger = logging.getLogger(__name__)

logger.info("Starting minimal Streamlit app")

try:
    # Basic page config
    st.set_page_config(
        page_title="AurumBot Test",
        layout="wide",
    )

    # Simple content
    st.title("🌟 AurumBot Test")
    st.write("Initializing...")

    logger.info("Basic UI elements rendered")

except Exception as e:
    logger.error(f"Error in Streamlit app: {str(e)}", exc_info=True)
    st.error("An error occurred while starting the application")