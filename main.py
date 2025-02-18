import logging
import sys
import streamlit as st

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('streamlit_app.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.debug("Starting Streamlit application initialization")
    try:
        # Page configuration
        st.set_page_config(
            page_title="AurumBot Dashboard",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        logger.info("Page configuration set successfully")

        # Main title
        st.title("🤖 AurumBot Dashboard")

        # Sidebar
        with st.sidebar:
            st.header("Navigation")
            st.markdown("---")
            st.info("Welcome to AurumBot Dashboard")

        # Main content
        st.markdown("### System Status")
        st.success("System is healthy and running")

        logger.info("Streamlit dashboard initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Streamlit dashboard: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()