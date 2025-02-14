import logging
import bcrypt
from datetime import datetime
from typing import Optional, Dict, Any
import streamlit as st
from sqlalchemy import text
from utils.database import get_db

logger = logging.getLogger(__name__)

class UserAuth:
    def __init__(self):
        self.db = next(get_db())

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        try:
            if not plain_password or not hashed_password:
                logger.warning("Empty password or hash provided")
                return False

            # Convert strings to bytes for bcrypt
            plain_bytes = plain_password.encode('utf-8')
            hash_bytes = hashed_password.encode('utf-8')

            return bcrypt.checkpw(plain_bytes, hash_bytes)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    def hash_password(self, password: str) -> str:
        """Hash a password for storing."""
        try:
            if not password:
                raise ValueError("Password cannot be empty")

            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_bytes, salt)
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise

    def login(self, username: str, password: str) -> bool:
        """Attempt to log in a user."""
        try:
            if not username or not password:
                logger.warning("Empty username or password")
                return False

            logger.info(f"Attempting login for user: {username}")
            result = self.db.execute(
                text("SELECT id, username, password_hash FROM users WHERE username = :username"),
                {"username": username}
            ).fetchone()

            if not result:
                logger.warning(f"No user found with username: {username}")
                return False

            logger.info("User found in database")
            stored_hash = result[2]

            if self.verify_password(password, stored_hash):
                logger.info("Password verified successfully")
                # Update last_login
                self.db.execute(
                    text("UPDATE users SET last_login = :login_time WHERE id = :user_id"),
                    {"login_time": datetime.now(), "user_id": result[0]}
                )
                self.db.commit()

                # Set session
                st.session_state['user'] = {
                    'id': result[0],
                    'username': result[1],
                    'authenticated': True,
                    'login_time': datetime.now().isoformat()
                }
                return True
            else:
                logger.warning("Invalid password provided")
                return False

        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def logout(self):
        """Log out the current user."""
        if 'user' in st.session_state:
            del st.session_state['user']
            logger.info("User logged out successfully")

    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return 'user' in st.session_state and st.session_state['user'].get('authenticated', False)

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user data if authenticated."""
        return st.session_state.get('user', None)

    def check_subscription(self) -> bool:
        """Check if the current user has an active subscription."""
        if not self.is_authenticated():
            return False

        try:
            user_id = st.session_state['user']['id']
            result = self.db.execute(
                text("SELECT subscription_expires_at FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            ).fetchone()

            if result and result[0]:
                return datetime.now() < result[0]
            return False
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            return False

def login_required(func):
    """Decorator for protecting routes that require authentication."""
    def wrapper(*args, **kwargs):
        if not st.session_state.get('user', {}).get('authenticated', False):
            st.error("Effettua il login per accedere a questa funzionalità")
            return
        return func(*args, **kwargs)
    return wrapper