
import streamlit as st
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('streamlit_test.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting minimal Streamlit test app")

    try:
        st.set_page_config(
            page_title="Test App",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        st.title("Test Streamlit App")
        st.write("If you see this message, Streamlit is working correctly!")
        
        logger.info("App initialized successfully")
    except Exception as e:
        logger.error(f"Error in test app: {str(e)}")
        st.error("An error occurred while running the test app")

if __name__ == "__main__":
    main()
