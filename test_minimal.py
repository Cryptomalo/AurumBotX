import streamlit as st
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('streamlit_debug.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

try:
    logger.info("Starting minimal Streamlit test")
    
    st.set_page_config(
        page_title="Test Minimo",
        layout="wide"
    )
    
    st.title("Test AurumBot")
    st.write("Test di connessione base")
    st.write(f"Orario del server: {datetime.now()}")
    
    logger.info("Basic UI elements rendered")
    
except Exception as e:
    logger.error(f"Error in minimal test: {str(e)}", exc_info=True)
    st.error("Si è verificato un errore nel test")
