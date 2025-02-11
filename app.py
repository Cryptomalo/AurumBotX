
import streamlit as st
import logging
import sys
from datetime import datetime
from utils.data_loader import CryptoDataLoader
from utils.auto_trader import AutoTrader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    try:
        st.set_page_config(
            page_title="AurumBot",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        st.title("🤖 AurumBot")
        
        # Initialize components
        data_loader = CryptoDataLoader()
        available_coins = data_loader.get_available_coins()
        
        # Sidebar controls
        with st.sidebar:
            st.header("Configurazione")
            selected_coin = st.selectbox(
                "Seleziona Cryptocurrency",
                list(available_coins.keys()),
                index=0
            )
            
            initial_balance = st.number_input(
                "Bilancio Iniziale ($)",
                min_value=100,
                value=10000
            )
            
            risk_level = st.slider(
                "Livello di Rischio (%)",
                min_value=1,
                max_value=10,
                value=2
            )

        # Main content
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Stato Sistema")
            if selected_coin:
                price = data_loader.get_current_price(selected_coin)
                st.metric("Prezzo Attuale", f"${price:,.2f}" if price else "N/A")
                
        with col2:
            st.subheader("Performance")
            st.info("Sistema operativo e monitoraggio attivo")

        # Initialize bot
        bot = AutoTrader(
            symbol=selected_coin,
            initial_balance=initial_balance,
            risk_per_trade=risk_level/100,
            testnet=True
        )

    except Exception as e:
        logger.error(f"Errore nell'applicazione: {str(e)}", exc_info=True)
        st.error(f"Si è verificato un errore: {str(e)}")

if __name__ == "__main__":
    main()
