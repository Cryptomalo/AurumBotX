import streamlit as st
import logging
import sys
from datetime import datetime

# Setup logging with detailed output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Starting minimal test app")

        # Basic page config
        st.set_page_config(
            page_title="AurumBot Test",
            layout="wide"
        )
        logger.info("Page configuration completed")

        # Minimal content
        st.title("AurumBot Test")
        st.write("Se vedi questo messaggio, l'app sta funzionando!")
        st.write(f"Orario del server: {datetime.now()}")

        logger.info("Basic content rendered")

    except Exception as e:
        logger.error(f"Error in app: {str(e)}", exc_info=True)
        st.error("Si è verificato un errore. Controlla i log.")

if __name__ == "__main__":
    logger.info("Application startup initiated")
    main()
    logger.info("Main function completed")