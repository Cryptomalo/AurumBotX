import streamlit as st
import asyncio
from utils.telegram_scanner import TelegramScanner

async def render_telegram_scanner():
    st.title("Telegram Meme Coin Scanner 🔍")

    # Initialize scanner in session state
    if 'telegram_scanner' not in st.session_state:
        st.session_state.telegram_scanner = TelegramScanner()

    scanner = st.session_state.telegram_scanner
    setup_status = scanner.get_setup_status()

    # Show setup instructions
    st.header(setup_status['instructions']['title'])

    # Display credentials status
    st.subheader("📱 Status Configurazione")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"API ID: {setup_status['credentials_status']['api_id']}")
    with col2:
        st.info(f"API Hash: {setup_status['credentials_status']['api_hash']}")

    # Show bot information
    st.subheader("🤖 Informazioni Bot")
    st.write(f"Username Bot: `{setup_status['instructions']['bot_username']}`")
    st.write(f"Canale Segnali: {setup_status['instructions']['channel_link']}")

    # Detailed setup instructions
    with st.expander("📋 Istruzioni Configurazione"):
        for step in setup_status['instructions']['steps']:
            st.write(step)

    # Connection status
    st.subheader("🔌 Stato Connessione")
    if setup_status['status'] == 'needs_setup':
        st.warning("⚠️ Configurazione necessaria - Segui le istruzioni sopra per configurare le credenziali API")
    elif setup_status['connection_state'] == 'connected':
        st.success("✅ Bot connesso e funzionante")
    else:
        st.error("❌ Bot non connesso - Verifica le credenziali e riprova")

    # Start scanning button (only show if properly configured)
    if setup_status['status'] == 'ready':
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