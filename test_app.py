import streamlit as st
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('streamlit_test.log')
    ]
)
logger = logging.getLogger(__name__)

logger.info("Starting minimal test app")

try:
    # Basic title
    st.title("Test App")
    st.write("If you see this message, Streamlit is working!")

    logger.info("Basic UI elements rendered")

except Exception as e:
    logger.error(f"Error in test app: {str(e)}", exc_info=True)
    st.error("An error occurred")