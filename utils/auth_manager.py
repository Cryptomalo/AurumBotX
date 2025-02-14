import logging
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import streamlit as st
from utils.database import get_db

logger = logging.getLogger(__name__)

class UserAuth:
    def __init__(self):
        self.db = next(get_db())
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def login(self, username: str, password: str) -> bool:
        try:
            result = self.db.execute(
                "SELECT id, username, password_hash FROM users WHERE username = %s",
                (username,)
            ).fetchone()
            
            if result and self.verify_password(password, result[2]):
                # Aggiorna last_login
                self.db.execute(
                    "UPDATE users SET last_login = %s WHERE id = %s",
                    (datetime.now(), result[0])
                )
                self.db.commit()
                
                # Imposta la sessione
                st.session_state['user'] = {
                    'id': result[0],
                    'username': result[1],
                    'authenticated': True,
                    'login_time': datetime.now().isoformat()
                }
                return True
            return False
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def logout(self):
        if 'user' in st.session_state:
            del st.session_state['user']
    
    def is_authenticated(self) -> bool:
        return 'user' in st.session_state and st.session_state['user'].get('authenticated', False)
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        return st.session_state.get('user', None)
    
    def check_subscription(self) -> bool:
        if not self.is_authenticated():
            return False
        
        try:
            user_id = st.session_state['user']['id']
            result = self.db.execute(
                "SELECT subscription_expires_at FROM users WHERE id = %s",
                (user_id,)
            ).fetchone()
            
            if result and result[0]:
                return datetime.now() < result[0]
            return False
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            return False

def login_required(func):
    """Decoratore per proteggere le pagine che richiedono autenticazione"""
    def wrapper(*args, **kwargs):
        if not st.session_state.get('user', {}).get('authenticated', False):
            st.error("Effettua il login per accedere a questa funzionalità")
            return
        return func(*args, **kwargs)
    return wrapper
