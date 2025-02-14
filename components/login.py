import streamlit as st
import os
from urllib.parse import urlencode
from web3 import Web3

from utils.social_auth_manager import SocialAuthManager
from utils.auth_config import get_provider_config, get_wallet_config

def render_wallet_login():
    """Render the wallet connection interface"""
    st.title("🌟 AurumBot Trading Platform")
    st.header("Connect your Wallet to Start")

    # Initialize Web3
    w3 = Web3()

    # Get wallet configuration
    eth_config = get_wallet_config("ETH")

    st.markdown("""
    Per iniziare:
    1. Collega il tuo wallet
    2. Dopo potrai connettere i tuoi social media per l'analisi dei dati
    """)

    if st.button("🔗 Connect Wallet", use_container_width=True):
        # Placeholder for wallet connection
        mock_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"

        if w3.is_address(mock_address):
            st.session_state['user'] = {
                'id': 1,  # Temporary user ID
                'wallet_address': mock_address,
                'authenticated': True
            }
            st.success(f"Wallet connected: {mock_address[:6]}...{mock_address[-4:]}")
            st.rerun()
        else:
            st.error("Invalid wallet address")

def render_social_connections():
    """Render social media connection options after wallet authentication"""
    st.title("🔗 Social Media Connections")
    st.markdown("""
    Collega i tuoi social media per permettere al bot di analizzare i dati e migliorare le strategie di trading.
    """)

    social_auth = SocialAuthManager()

    col1, col2, col3 = st.columns(3)

    with col1:
        # Reddit OAuth
        reddit_config = get_provider_config("reddit")
        if st.button("Connect Reddit", key="reddit_btn", use_container_width=True):
            if all(reddit_config.values()):
                params = {
                    'client_id': reddit_config['client_id'],
                    'response_type': 'code',
                    'state': 'reddit_auth',
                    'redirect_uri': reddit_config['redirect_uri'],
                    'duration': 'permanent',
                    'scope': 'identity read submit'
                }
                auth_url = f"https://www.reddit.com/api/v1/authorize?{urlencode(params)}"
                st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
            else:
                st.error("Reddit configuration not complete")

    with col2:
        # Telegram OAuth
        telegram_config = get_provider_config("telegram")
        if st.button("Connect Telegram", key="telegram_btn", use_container_width=True):
            if all(telegram_config.values()):
                bot_username = telegram_config.get('bot_username', 'YourBotName')
                st.markdown(f'<script async src="https://telegram.org/js/telegram-widget.js?22" '+
                        f'data-telegram-login="{bot_username}" data-size="large" data-radius="8" '+
                        'data-onauth="onTelegramAuth(user)" data-request-access="write"></script>', 
                        unsafe_allow_html=True)
            else:
                st.error("Telegram configuration not complete")

    with col3:
        # GitHub OAuth
        github_config = get_provider_config("github")
        if st.button("Connect GitHub", key="github_btn", use_container_width=True):
            if all(github_config.values()):
                params = {
                    'client_id': github_config['client_id'],
                    'redirect_uri': github_config['redirect_uri'],
                    'scope': 'read:user user:email',
                    'state': 'github_auth'
                }
                auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
                st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
            else:
                st.error("GitHub configuration not complete")

    # Show connected accounts
    st.markdown("---")
    if 'user' in st.session_state:
        st.subheader("Connected Accounts")
        user_data = st.session_state.user
        if user_data:
            connections = social_auth.get_user_connections(user_data['id'])
            if connections['social']:
                for conn in connections['social']:
                    st.success(f"✓ Connected: {conn['provider'].title()}")
                    if st.button(f"Disconnect {conn['provider']}", key=f"disconnect_{conn['provider']}"):
                        if social_auth.disconnect_provider(user_data['id'], conn['provider']):
                            st.success(f"{conn['provider']} disconnected")
                            st.rerun()

def render_login_page():
    """Main login page renderer"""
    if 'user' not in st.session_state or not st.session_state['user'].get('authenticated'):
        render_wallet_login()
    else:
        render_social_connections()

def handle_oauth_callbacks():
    """Handle OAuth callbacks from social platforms"""
    params = st.experimental_get_query_params()
    if 'code' in params:
        code = params['code'][0]
        state = params.get('state', [None])[0]

        social_auth = SocialAuthManager()

        if state == 'reddit_auth':
            try:
                token_data = social_auth.exchange_reddit_code(code)
                if token_data and 'access_token' in token_data:
                    st.success("Successfully connected Reddit account!")
                    st.rerun()
            except Exception as e:
                st.error(f"Failed to connect Reddit account: {str(e)}")

        elif state == 'github_auth':
            try:
                token_data = social_auth.exchange_github_code(code)
                if token_data and 'access_token' in token_data:
                    st.success("Successfully connected GitHub account!")
                    st.rerun()
            except Exception as e:
                st.error(f"Failed to connect GitHub account: {str(e)}")