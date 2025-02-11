import streamlit as st
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('streamlit_debug.log')
    ]
)
logger = logging.getLogger(__name__)

logger.info("Starting minimal test app")

try:
    st.title("Test AurumBot")
    st.write("Se vedi questo messaggio, l'app funziona correttamente!")

    logger.info("Basic UI elements rendered")

except Exception as e:
    logger.error(f"Error in test app: {str(e)}", exc_info=True)
    st.error("Si è verificato un errore")
