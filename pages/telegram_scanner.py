import streamlit as st
import asyncio
import qrcode
import io
from PIL import Image
from utils.telegram_scanner import TelegramScanner

async def render_telegram_scanner():
    st.title("Telegram Meme Coin Scanner 🔍")

    # Initialize scanner in session state
    if 'telegram_scanner' not in st.session_state:
        st.session_state.telegram_scanner = TelegramScanner()
        st.session_state.scanning = False
        st.session_state.qr_shown = False
        st.session_state.connection_state = "disconnected"

    scanner = st.session_state.telegram_scanner

    # Login section
    if scanner.get_connection_state() != "connected":
        st.info("Per utilizzare lo scanner, effettua l'accesso con il tuo account Telegram")
        st.write("Scansiona il codice QR qui sotto con l'app Telegram:")

        if st.button("Genera QR per Login") or st.session_state.qr_shown:
            st.session_state.qr_shown = True
            with st.spinner("Generazione codice QR in corso..."):
                success = await scanner.start()
                if success:
                    st.success("Login effettuato con successo!")
                    st.experimental_rerun()
                elif scanner.get_connection_state() == "timeout":
                    st.error("Timeout scansione QR. Riprova.")
                    st.session_state.qr_shown = False
                elif scanner.get_connection_state() == "error":
                    st.error("Errore durante il login. Riprova.")
                    st.session_state.qr_shown = False
                else:
                    st.warning("Login non riuscito. Assicurati di scansionare il QR con l'app Telegram.")
    else:
        # Scanning controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Avvia Scansione" if not st.session_state.scanning else "⏹️ Ferma Scansione"):
                st.session_state.scanning = not st.session_state.scanning
                if st.session_state.scanning:
                    # Reset monitoring for fresh scan
                    scanner.reset_monitoring()
                    asyncio.create_task(scanner.scan_channels())
                st.experimental_rerun()

        with col2:
            min_mentions = st.number_input("Menzioni minime", min_value=1, value=3)
            hours = st.number_input("Nelle ultime ore", min_value=1, value=24)

        # Status indicator
        if st.session_state.scanning:
            st.info("📡 Scanner attivo - Monitoraggio canali in corso...")

        # Display trending coins
        trending = scanner.get_trending_coins(min_mentions=min_mentions, hours=hours)
        if trending:
            st.subheader("🔥 Crypto Trending")

            # Metrics overview
            total_coins = len(trending)
            total_mentions = sum(coin['total_mentions'] for coin in trending)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Monete Rilevate", total_coins)
            with col2:
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
                st.info("🔍 Scansione in corso... In attesa di rilevare nuove crypto.")
            else:
                st.info("Avvia la scansione per scoprire nuove crypto!")

        # Scanning status
        if st.session_state.scanning:
            st.warning("⚠️ Scanner attivo - Chiudi la scansione prima di chiudere l'applicazione.")

            # Progress placeholder
            progress_placeholder = st.empty()
            if hasattr(scanner, 'monitored_channels'):
                progress_placeholder.text(f"Canali monitorati: {len(scanner.monitored_channels)}")

        # Logout button
        if st.button("🚪 Logout"):
            asyncio.create_task(scanner.stop())
            st.session_state.scanning = False
            st.session_state.qr_shown = False
            st.session_state.telegram_scanner = TelegramScanner()
            st.success("Logout effettuato con successo!")
            st.experimental_rerun()