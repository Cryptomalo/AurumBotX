
import streamlit as st

# Configurazione base della pagina
st.set_page_config(
    page_title="AurumBot",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Disabilita alcuni avvisi Streamlit
st.set_option('deprecation.showfileUploaderEncoding', False)
st.set_option('deprecation.showPyplotGlobalUse', False)

# Contenuto principale
st.title("🌟 AurumBot Trading Platform")
st.write("Welcome to AurumBot!")

# Test di funzionamento
if st.button("Test Connessione"):
    st.success("Connessione funzionante!")
