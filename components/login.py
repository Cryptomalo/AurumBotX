import streamlit as st
from web3 import Web3
import json
from datetime import datetime
import os
from urllib.parse import urlencode

from utils.social_auth_manager import SocialAuthManager
from utils.auth_config import get_provider_config, get_wallet_config

def render_login_page():
    st.title("Login to Aurum Bot")

    social_auth = SocialAuthManager()

    # Initialize session state
    if 'login_method' not in st.session_state:
        st.session_state.login_method = 'social'

    st.subheader("Connect with Social Media")

    # Reddit OAuth
    reddit_config = get_provider_config("reddit")
    if st.button("Connect with Reddit"):
        if all(reddit_config.values()):
            params = {
                'client_id': reddit_config['client_id'],
                'response_type': 'code',
                'state': 'random_state_string',
                'redirect_uri': reddit_config['redirect_uri'],
                'duration': 'permanent',
                'scope': 'identity read submit'
            }
            auth_url = f"https://www.reddit.com/api/v1/authorize?{urlencode(params)}"
            st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
        else:
            st.error("Reddit configuration not complete")

    # Telegram OAuth
    telegram_config = get_provider_config("telegram")
    if st.button("Connect with Telegram"):
        if all(telegram_config.values()):
            bot_username = telegram_config.get('bot_username', 'YourBotName')
            st.markdown(f'<script async src="https://telegram.org/js/telegram-widget.js?22" '+
                       f'data-telegram-login="{bot_username}" data-size="large" data-radius="8" '+
                       'data-onauth="onTelegramAuth(user)" data-request-access="write"></script>', 
                       unsafe_allow_html=True)
        else:
            st.error("Telegram configuration not complete")

    # GitHub OAuth
    github_config = get_provider_config("github")
    if st.button("Connect with GitHub"):
        if all(github_config.values()):
            params = {
                'client_id': github_config['client_id'],
                'redirect_uri': github_config['redirect_uri'],
                'scope': 'read:user user:email',
                'state': 'random_state_string'
            }
            auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
            st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
        else:
            st.error("GitHub configuration not complete")

    # Handle OAuth callbacks
    params = st.experimental_get_query_params()

    if 'code' in params:  # OAuth callback received
        code = params['code'][0]
        state = params.get('state', [None])[0]

        if 'reddit' in st.session_state.get('oauth_state', ''):
            handle_reddit_callback(code, social_auth)
        elif 'github' in st.session_state.get('oauth_state', ''):
            handle_github_callback(code, social_auth)

    # Show connected accounts if user is logged in
    if 'user' in st.session_state:
        st.subheader("Connected Accounts")
        user_data = st.session_state.user
        if user_data:
            connections = social_auth.get_user_connections(user_data['id'])

            # Display connected social accounts
            if connections['social']:
                st.write("Social Media Accounts:")
                for conn in connections['social']:
                    st.write(f"- {conn['provider']}: Connected on {conn['connected_at']}")
                    if st.button(f"Disconnect {conn['provider']}", key=f"disconnect_{conn['provider']}"):
                        if social_auth.disconnect_provider(user_data['id'], conn['provider']):
                            st.success(f"{conn['provider']} disconnected")
                            st.rerun()

def handle_reddit_callback(code, social_auth):
    """Handle Reddit OAuth callback"""
    reddit_config = get_provider_config("reddit")
    try:
        # Exchange code for token (implementation in social_auth_manager.py)
        token_data = social_auth.exchange_reddit_code(code)
        if token_data and 'access_token' in token_data:
            st.success("Successfully connected Reddit account!")
            st.session_state.user = {'id': 1}  # Temporary user ID
            st.rerun()
    except Exception as e:
        st.error(f"Failed to connect Reddit account: {str(e)}")

def handle_github_callback(code, social_auth):
    """Handle GitHub OAuth callback"""
    github_config = get_provider_config("github")
    try:
        # Exchange code for token (implementation in social_auth_manager.py)
        token_data = social_auth.exchange_github_code(code)
        if token_data and 'access_token' in token_data:
            st.success("Successfully connected GitHub account!")
            st.session_state.user = {'id': 1}  # Temporary user ID
            st.rerun()
    except Exception as e:
        st.error(f"Failed to connect GitHub account: {str(e)}")