import streamlit as st
import os
from urllib.parse import urlencode

from utils.social_auth_manager import SocialAuthManager
from utils.auth_config import get_provider_config

def render_login_page():
    st.title("Aurum Bot")
    st.header("Connect your social media accounts")

    social_auth = SocialAuthManager()

    # Reddit OAuth
    reddit_config = get_provider_config("reddit")
    if st.button("Connect Reddit", key="reddit_btn"):
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

    # Telegram OAuth
    telegram_config = get_provider_config("telegram")
    if st.button("Connect Telegram", key="telegram_btn"):
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
    if st.button("Connect GitHub", key="github_btn"):
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

    # Handle OAuth callbacks
    params = st.experimental_get_query_params()
    if 'code' in params:
        code = params['code'][0]
        state = params.get('state', [None])[0]

        if state == 'reddit_auth':
            handle_reddit_callback(code, social_auth)
        elif state == 'github_auth':
            handle_github_callback(code, social_auth)

    # Show connected accounts
    if 'user' in st.session_state:
        st.markdown("---")
        st.subheader("Connected Accounts")
        user_data = st.session_state.user
        if user_data:
            connections = social_auth.get_user_connections(user_data['id'])
            if connections['social']:
                for conn in connections['social']:
                    st.write(f"✓ {conn['provider'].title()}")
                    if st.button(f"Disconnect {conn['provider']}", key=f"disconnect_{conn['provider']}"):
                        if social_auth.disconnect_provider(user_data['id'], conn['provider']):
                            st.success(f"{conn['provider']} disconnected")
                            st.rerun()

def handle_reddit_callback(code, social_auth):
    try:
        token_data = social_auth.exchange_reddit_code(code)
        if token_data and 'access_token' in token_data:
            st.success("Successfully connected Reddit account!")
            st.session_state.user = {'id': 1}  # Temporary user ID
            st.rerun()
    except Exception as e:
        st.error(f"Failed to connect Reddit account: {str(e)}")

def handle_github_callback(code, social_auth):
    try:
        token_data = social_auth.exchange_github_code(code)
        if token_data and 'access_token' in token_data:
            st.success("Successfully connected GitHub account!")
            st.session_state.user = {'id': 1}  # Temporary user ID
            st.rerun()
    except Exception as e:
        st.error(f"Failed to connect GitHub account: {str(e)}")