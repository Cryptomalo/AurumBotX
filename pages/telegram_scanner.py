import streamlit as st
import asyncio
import qrcode
import io
from PIL import Image
from utils.telegram_scanner import TelegramScanner

async def render_telegram_scanner():
    st.title("Telegram Meme Coin Scanner")

    # Initialize scanner in session state
    if 'telegram_scanner' not in st.session_state:
        st.session_state.telegram_scanner = TelegramScanner()
        st.session_state.scanning = False
        st.session_state.qr_shown = False

    scanner = st.session_state.telegram_scanner

    # Login section
    if not scanner.client or not scanner.client.is_connected():
        st.write("Scansiona il codice QR qui sotto per accedere con il tuo account Telegram:")

        if st.button("Genera QR per Login") or st.session_state.qr_shown:
            st.session_state.qr_shown = True
            with st.spinner("Generazione codice QR in corso..."):
                success = await scanner.start()
                if success:
                    st.success("Login effettuato con successo!")
                    st.experimental_rerun()
                else:
                    st.error("Errore durante il login. Riprova.")
    else:
        # Scanning controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Avvia Scanning" if not st.session_state.scanning else "Ferma Scanning"):
                st.session_state.scanning = not st.session_state.scanning
                if st.session_state.scanning:
                    # Reset monitoring for fresh scan
                    scanner.reset_monitoring()
                    asyncio.create_task(scanner.scan_channels())
                st.experimental_rerun()

        with col2:
            min_mentions = st.number_input("Menzioni minime", min_value=1, value=3)
            hours = st.number_input("Nelle ultime ore", min_value=1, value=24)

        # Display trending coins
        trending = scanner.get_trending_coins(min_mentions=min_mentions, hours=hours)
        if trending:
            st.subheader("Meme Coin Trending")

            # Metrics overview
            total_coins = len(trending)
            total_mentions = sum(coin['total_mentions'] for coin in trending)
            st.metric("Coin Rilevate", total_coins)
            st.metric("Menzioni Totali", total_mentions)

            # Detailed coin information
            for coin in trending:
                with st.expander(f"💎 {coin['symbol']} - {coin['recent_mentions']} menzioni recenti"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"⚡ Trend Score: {coin['trending_score']}")
                        st.write(f"📈 Velocità: {coin['velocity']} menzioni/ora")
                        st.write(f"📅 Prima menzione: {coin['first_seen']}")

                    with col2:
                        st.write(f"🔄 Menzioni totali: {coin['total_mentions']}")
                        st.write(f"📢 Canali: {coin['channels']}")

                    if coin.get('latest_message'):
                        st.text_area("Ultimo messaggio", coin['latest_message'], height=100)
        else:
            if st.session_state.scanning:
                st.info("Scanning in corso... Attendi il rilevamento delle prime coin.")
            else:
                st.info("Nessuna coin trending rilevata. Avvia lo scanning per scoprire nuove coin!")

        # Scanning status
        if st.session_state.scanning:
            st.warning("Scanner attivo... Ferma lo scanning prima di chiudere l'applicazione.")

            # Progress placeholder
            progress_placeholder = st.empty()
            if 'monitored_channels' in dir(scanner):
                progress_placeholder.text(f"Canali monitorati: {len(scanner.monitored_channels)}")