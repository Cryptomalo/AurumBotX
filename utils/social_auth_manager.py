import logging
from typing import Dict, Optional, Any
from datetime import datetime
import os
import requests

import streamlit as st
from web3 import Web3
from sqlalchemy.sql import text

from utils.database import get_db
from utils.auth_config import get_provider_config

logger = logging.getLogger(__name__)

class SocialAuthManager:
    def __init__(self):
        self.db = next(get_db())
        self.w3 = Web3()

    def connect_wallet(self, user_id: int, wallet_address: str, chain_type: str = 'ETH') -> bool:
        """Connect a wallet address to a user account"""
        try:
            # Validate wallet address
            if not self.w3.is_address(wallet_address):
                logger.error(f"Invalid wallet address: {wallet_address}")
                return False
                
            # Insert wallet connection
            self.db.execute(
                text("""
                INSERT INTO user_wallets (user_id, wallet_address, chain_type)
                VALUES (:user_id, :wallet_address, :chain_type)
                ON CONFLICT (user_id, wallet_address) 
                DO UPDATE SET chain_type = :chain_type
                """),
                {
                    "user_id": user_id,
                    "wallet_address": wallet_address,
                    "chain_type": chain_type
                }
            )
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error connecting wallet: {e}")
            return False
            
    def verify_wallet_signature(self, wallet_address: str, signature: str, message: str) -> bool:
        """Verify a wallet signature for authentication"""
        try:
            # Recover the address that signed the message
            recovered_address = self.w3.eth.account.recover_message(
                text=message,
                signature=signature
            )
            return recovered_address.lower() == wallet_address.lower()
        except Exception as e:
            logger.error(f"Error verifying wallet signature: {e}")
            return False
            
    def exchange_reddit_code(self, code: str) -> Dict[str, Any]:
        """Exchange Reddit OAuth code for access token"""
        try:
            reddit_config = get_provider_config("reddit")
            token_url = "https://www.reddit.com/api/v1/access_token"

            auth = (reddit_config['client_id'], reddit_config['client_secret'])
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': reddit_config['redirect_uri']
            }

            response = requests.post(
                token_url,
                auth=auth,
                data=data,
                headers={'User-Agent': reddit_config['user_agent']}
            )

            if response.status_code == 200:
                token_data = response.json()
                self.store_social_connection(
                    user_id=1,  # Temporary user ID
                    provider='reddit',
                    access_token=token_data['access_token'],
                    refresh_token=token_data.get('refresh_token'),
                    expires_at=datetime.now()  # Add proper expiration handling
                )
                return token_data

            logger.error(f"Reddit token exchange failed: {response.text}")
            return None

        except Exception as e:
            logger.error(f"Error exchanging Reddit code: {e}")
            return None

    def exchange_github_code(self, code: str) -> Dict[str, Any]:
        """Exchange GitHub OAuth code for access token"""
        try:
            github_config = get_provider_config("github")
            token_url = "https://github.com/login/oauth/access_token"

            data = {
                'client_id': github_config['client_id'],
                'client_secret': github_config['client_secret'],
                'code': code,
                'redirect_uri': github_config['redirect_uri']
            }

            response = requests.post(
                token_url,
                data=data,
                headers={'Accept': 'application/json'}
            )

            if response.status_code == 200:
                token_data = response.json()
                self.store_social_connection(
                    user_id=1,  # Temporary user ID
                    provider='github',
                    access_token=token_data['access_token'],
                    expires_at=datetime.now()  # Add proper expiration handling
                )
                return token_data

            logger.error(f"GitHub token exchange failed: {response.text}")
            return None

        except Exception as e:
            logger.error(f"Error exchanging GitHub code: {e}")
            return None

    def store_social_connection(
        self, 
        user_id: int,
        provider: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Store social media connection in database"""
        try:
            self.db.execute(
                text("""
                INSERT INTO user_connections 
                (user_id, provider, access_token, refresh_token, expires_at)
                VALUES (:user_id, :provider, :access_token, :refresh_token, :expires_at)
                ON CONFLICT (user_id, provider) 
                DO UPDATE SET 
                    access_token = :access_token,
                    refresh_token = :refresh_token,
                    expires_at = :expires_at
                """),
                {
                    "user_id": user_id,
                    "provider": provider,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": expires_at
                }
            )
            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error storing social connection: {e}")
            return False

    def get_user_connections(self, user_id: int) -> Dict[str, Any]:
        """Get all social connections for a user"""
        try:
            social_connections = self.db.execute(
                text("""
                SELECT provider, created_at 
                FROM user_connections 
                WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            ).fetchall()

            return {
                "social": [
                    {
                        "provider": conn[0],
                        "connected_at": conn[1].isoformat()
                    } for conn in social_connections
                ]
            }

        except Exception as e:
            logger.error(f"Error getting user connections: {e}")
            return {"social": []}

    def disconnect_provider(self, user_id: int, provider: str) -> bool:
        """Disconnect a social media provider"""
        try:
            self.db.execute(
                text("DELETE FROM user_connections WHERE user_id = :user_id AND provider = :provider"),
                {"user_id": user_id, "provider": provider}
            )
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error disconnecting provider: {e}")
            return False

    def disconnect_wallet(self, user_id: int, wallet_address: str) -> bool:
        """Disconnect a wallet address"""
        try:
            self.db.execute(
                text("DELETE FROM user_wallets WHERE user_id = :user_id AND wallet_address = :wallet_address"),
                {"user_id": user_id, "wallet_address": wallet_address}
            )
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error disconnecting wallet: {e}")
            return False