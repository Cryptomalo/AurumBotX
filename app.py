import streamlit as st
import logging
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('aurumbot.log')
    ]
)
logger = logging.getLogger(__name__)

try:
    # Basic page config
    st.set_page_config(
        page_title="AurumBot",
        page_icon="🌟",
        layout="wide"
    )

    # Title and description
    st.title("🌟 AurumBot")
    st.write("Piattaforma di Trading Automatico")
    
    # Sidebar
    st.sidebar.title("Controlli")
    selected_crypto = st.sidebar.selectbox(
        "Seleziona Crypto",
        ["BTC-USD", "ETH-USD", "SOL-USD"]
    )
    
    # Main content
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Stato Sistema")
        st.info(f"Crypto selezionata: {selected_crypto}")
        st.success("Sistema operativo")
        
    with col2:
        st.subheader("Informazioni")
        st.write(f"Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}")

except Exception as e:
    logger.error(f"Errore nell'applicazione: {str(e)}", exc_info=True)
    st.error("Si è verificato un errore. Per favore controlla i log.")
