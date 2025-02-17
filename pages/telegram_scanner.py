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
        st.write("Scan the QR code below to login with your Telegram account:")

        if st.button("Generate QR Login") or st.session_state.qr_shown:
            st.session_state.qr_shown = True
            with st.spinner("Generating QR code..."):
                success = await scanner.start()
                if success:
                    st.success("Login successful!")
                    st.experimental_rerun()
                else:
                    st.error("Login failed. Please try again.")
    else:
        # Scanning controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Scanning" if not st.session_state.scanning else "Stop Scanning"):
                st.session_state.scanning = not st.session_state.scanning
                if st.session_state.scanning:
                    # Reset monitoring for fresh scan
                    scanner.reset_monitoring()
                    asyncio.create_task(scanner.scan_channels())
                st.experimental_rerun()

        with col2:
            min_mentions = st.number_input("Minimum mentions", min_value=1, value=3)
            hours = st.number_input("In last hours", min_value=1, value=24)

        # Display trending coins
        trending = scanner.get_trending_coins(min_mentions=min_mentions, hours=hours)
        if trending:
            st.subheader("Trending Meme Coins")

            # Metrics overview
            total_coins = len(trending)
            total_mentions = sum(coin['total_mentions'] for coin in trending)
            st.metric("Detected Coins", total_coins)
            st.metric("Total Mentions", total_mentions)

            # Detailed coin information
            for coin in trending:
                with st.expander(f"💎 {coin['symbol']} - {coin['recent_mentions']} recent mentions"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"⚡ Trend Score: {coin['trending_score']}")
                        st.write(f"📈 Velocity: {coin['velocity']} mentions/hour")
                        st.write(f"📅 First seen: {coin['first_seen']}")

                    with col2:
                        st.write(f"🔄 Total mentions: {coin['total_mentions']}")
                        st.write(f"📢 Channels: {coin['channels']}")

                    if coin.get('latest_message'):
                        st.text_area("Latest message", coin['latest_message'], height=100)
        else:
            if st.session_state.scanning:
                st.info("Scanning in progress... Waiting for first coins to be detected.")
            else:
                st.info("No trending coins detected. Start scanning to discover new coins!")

        # Scanning status
        if st.session_state.scanning:
            st.warning("Scanner active... Stop scanning before closing the application.")

            # Progress placeholder
            progress_placeholder = st.empty()
            if hasattr(scanner, 'monitored_channels'):
                progress_placeholder.text(f"Monitored channels: {len(scanner.monitored_channels)}")