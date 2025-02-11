
import streamlit as st
import logging
import sys
from datetime import datetime
from utils.data_loader import CryptoDataLoader

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('streamlit_test.log', mode='w')
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
        
        st.title("🤖 AurumBot Test")
        st.write("Test di funzionalità base")

        # Initialize data loader
        data_loader = CryptoDataLoader()
        
        # Test cryptocurrency data loading
        btc_price = data_loader.get_current_price("BTC-USD")
        if btc_price:
            st.success(f"✅ Data Loader funzionante - Prezzo BTC: ${btc_price:,.2f}")
        else:
            st.error("❌ Errore nel caricamento dei dati")

    except Exception as e:
        logger.error(f"Error in app: {str(e)}", exc_info=True)
        st.error(f"Si è verificato un errore: {str(e)}")

if __name__ == "__main__":
    main()
