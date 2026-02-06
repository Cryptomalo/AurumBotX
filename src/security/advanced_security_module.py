# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX - Advanced Security Module
Protezione avanzata per transazioni, dati sensibili e comunicazioni
"""

import hashlib
import hmac
import secrets
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import json
import logging

logger = logging.getLogger(__name__)


class SecurityModule:
    """Modulo di sicurezza avanzata per AurumBotX"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Inizializza il modulo di sicurezza
        
        Args:
            encryption_key: Chiave di crittografia (se None, ne genera una nuova)
        """
        if encryption_key:
            self.encryption_key = encryption_key.encode()
        else:
            self.encryption_key = Fernet.generate_key()
        
        self.cipher = Fernet(self.encryption_key)
        self.failed_attempts = {}
        self.blacklist = set()
        self.whitelist = set()
        self.transaction_history = []
        
    def encrypt_data(self, data: str) -> str:
        """
        Cripta dati sensibili
        
        Args:
            data: Dati da criptare
            
        Returns:
            Dati criptati in formato stringa
        """
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Errore crittografia: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decripta dati sensibili
        
        Args:
            encrypted_data: Dati criptati
            
        Returns:
            Dati decriptati
        """
        try:
            decrypted = self.cipher.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Errore decrittografia: {e}")
            raise
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        """
        Hash sicuro di password con salt
        
        Args:
            password: Password da hashare
            salt: Salt opzionale (se None, ne genera uno nuovo)
            
        Returns:
            Tuple (hash, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(32)
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = kdf.derive(password.encode())
        return key.hex(), salt.hex()
    
    def verify_password(self, password: str, hash_value: str, salt: str) -> bool:
        """
        Verifica password contro hash
        
        Args:
            password: Password da verificare
            hash_value: Hash memorizzato
            salt: Salt utilizzato
            
        Returns:
            True se password corretta
        """
        computed_hash, _ = self.hash_password(password, bytes.fromhex(salt))
        return hmac.compare_digest(computed_hash, hash_value)
    
    def generate_api_signature(self, secret: str, message: str) -> str:
        """
        Genera firma HMAC per API
        
        Args:
            secret: Chiave segreta
            message: Messaggio da firmare
            
        Returns:
            Firma HMAC
        """
        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify_api_signature(self, secret: str, message: str, signature: str) -> bool:
        """
        Verifica firma HMAC
        
        Args:
            secret: Chiave segreta
            message: Messaggio originale
            signature: Firma da verificare
            
        Returns:
            True se firma valida
        """
        expected_signature = self.generate_api_signature(secret, message)
        return hmac.compare_digest(expected_signature, signature)
    
    def check_rate_limit(self, identifier: str, max_attempts: int = 5, 
                        window_seconds: int = 300) -> bool:
        """
        Rate limiting per prevenire brute force
        
        Args:
            identifier: Identificatore (IP, user_id, etc.)
            max_attempts: Massimo tentativi consentiti
            window_seconds: Finestra temporale in secondi
            
        Returns:
            True se richiesta consentita
        """
        now = time.time()
        
        # Pulisci vecchi tentativi
        if identifier in self.failed_attempts:
            self.failed_attempts[identifier] = [
                t for t in self.failed_attempts[identifier]
                if now - t < window_seconds
            ]
        
        # Controlla se superato limite
        if identifier in self.failed_attempts:
            if len(self.failed_attempts[identifier]) >= max_attempts:
                logger.warning(f"Rate limit superato per {identifier}")
                return False
        
        return True
    
    def record_failed_attempt(self, identifier: str):
        """
        Registra tentativo fallito
        
        Args:
            identifier: Identificatore
        """
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        
        self.failed_attempts[identifier].append(time.time())
        logger.warning(f"Tentativo fallito registrato per {identifier}")
    
    def add_to_blacklist(self, identifier: str):
        """
        Aggiungi a blacklist
        
        Args:
            identifier: Identificatore da bloccare
        """
        self.blacklist.add(identifier)
        logger.warning(f"Aggiunto a blacklist: {identifier}")
    
    def is_blacklisted(self, identifier: str) -> bool:
        """
        Controlla se in blacklist
        
        Args:
            identifier: Identificatore da controllare
            
        Returns:
            True se blacklisted
        """
        return identifier in self.blacklist
    
    def add_to_whitelist(self, identifier: str):
        """
        Aggiungi a whitelist
        
        Args:
            identifier: Identificatore da autorizzare
        """
        self.whitelist.add(identifier)
        logger.info(f"Aggiunto a whitelist: {identifier}")
    
    def is_whitelisted(self, identifier: str) -> bool:
        """
        Controlla se in whitelist
        
        Args:
            identifier: Identificatore da controllare
            
        Returns:
            True se whitelisted
        """
        return identifier in self.whitelist
    
    def validate_transaction(self, transaction: Dict) -> Tuple[bool, str]:
        """
        Valida transazione per rilevare anomalie
        
        Args:
            transaction: Dati transazione
            
        Returns:
            Tuple (is_valid, reason)
        """
        # Controlla campi obbligatori
        required_fields = ['amount', 'pair', 'action', 'timestamp']
        for field in required_fields:
            if field not in transaction:
                return False, f"Campo mancante: {field}"
        
        # Controlla importo
        if transaction['amount'] <= 0:
            return False, "Importo non valido"
        
        # Controlla azione
        if transaction['action'] not in ['BUY', 'SELL', 'HOLD']:
            return False, "Azione non valida"
        
        # Controlla timestamp (non nel futuro, non troppo vecchio)
        now = time.time()
        tx_time = transaction['timestamp']
        if tx_time > now + 60:  # Max 1 minuto nel futuro
            return False, "Timestamp nel futuro"
        if now - tx_time > 3600:  # Max 1 ora nel passato
            return False, "Timestamp troppo vecchio"
        
        # Controlla duplicati
        tx_hash = self._hash_transaction(transaction)
        for hist_tx in self.transaction_history[-100:]:  # Ultimi 100
            if self._hash_transaction(hist_tx) == tx_hash:
                return False, "Transazione duplicata"
        
        # Registra transazione
        self.transaction_history.append(transaction)
        
        return True, "OK"
    
    def _hash_transaction(self, transaction: Dict) -> str:
        """Hash transazione per rilevare duplicati"""
        tx_string = json.dumps(transaction, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()
    
    def detect_suspicious_activity(self, transactions: List[Dict]) -> List[str]:
        """
        Rileva attività sospette
        
        Args:
            transactions: Lista transazioni da analizzare
            
        Returns:
            Lista di alert
        """
        alerts = []
        
        if not transactions:
            return alerts
        
        # Controlla frequenza transazioni
        if len(transactions) > 50:
            time_window = transactions[-1]['timestamp'] - transactions[0]['timestamp']
            if time_window < 300:  # 50 transazioni in 5 minuti
                alerts.append("Frequenza transazioni anomala")
        
        # Controlla importi anomali
        amounts = [tx['amount'] for tx in transactions]
        avg_amount = sum(amounts) / len(amounts)
        for tx in transactions[-10:]:
            if tx['amount'] > avg_amount * 10:
                alerts.append(f"Importo anomalo: {tx['amount']}")
        
        # Controlla pattern sospetti
        recent_actions = [tx['action'] for tx in transactions[-20:]]
        if recent_actions.count('SELL') > 15:
            alerts.append("Pattern sospetto: troppe vendite consecutive")
        
        return alerts
    
    def generate_session_token(self, user_id: str, expiry_hours: int = 24) -> str:
        """
        Genera token di sessione sicuro
        
        Args:
            user_id: ID utente
            expiry_hours: Ore di validità
            
        Returns:
            Token di sessione
        """
        expiry = datetime.now() + timedelta(hours=expiry_hours)
        token_data = {
            'user_id': user_id,
            'expiry': expiry.isoformat(),
            'nonce': secrets.token_hex(16)
        }
        token_string = json.dumps(token_data)
        return self.encrypt_data(token_string)
    
    def verify_session_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """
        Verifica token di sessione
        
        Args:
            token: Token da verificare
            
        Returns:
            Tuple (is_valid, user_id)
        """
        try:
            token_string = self.decrypt_data(token)
            token_data = json.loads(token_string)
            
            # Controlla scadenza
            expiry = datetime.fromisoformat(token_data['expiry'])
            if datetime.now() > expiry:
                return False, None
            
            return True, token_data['user_id']
        except Exception as e:
            logger.error(f"Errore verifica token: {e}")
            return False, None
    
    def sanitize_input(self, input_string: str) -> str:
        """
        Sanitizza input per prevenire injection
        
        Args:
            input_string: Stringa da sanitizzare
            
        Returns:
            Stringa sanitizzata
        """
        # Rimuovi caratteri pericolosi
        dangerous_chars = ['<', '>', '&', '"', "'", ';', '--', '/*', '*/']
        sanitized = input_string
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()


# Singleton instance
_security_module = None

def get_security_module() -> SecurityModule:
    """Ottieni istanza singleton del modulo di sicurezza"""
    global _security_module
    if _security_module is None:
        _security_module = SecurityModule()
    return _security_module

