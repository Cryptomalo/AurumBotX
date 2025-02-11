import streamlit as st
import logging
import sys

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
        # Basic title
        st.title("Test Editor")
        st.write("Se vedi questo messaggio, l'app sta funzionando!")

        # Editor di base
        code = st.text_area(
            "Inserisci il tuo codice qui",
            value="""def esempio():
    print("Hello World!")
""",
            height=200
        )

        if st.button("Analizza Codice"):
            st.info("Analisi del codice in corso...")

    except Exception as e:
        logger.error(f"Errore nell'app: {str(e)}", exc_info=True)
        st.error("Si è verificato un errore")

if __name__ == "__main__":
    logger.info("Avvio dell'applicazione")
    main()