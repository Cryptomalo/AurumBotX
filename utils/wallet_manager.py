import os
from typing import Optional, List, Dict
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from utils.database import get_db

logger = logging.getLogger(__name__)

class WalletManager:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def add_wallet(self, wallet_address: str, chain_type: str, label: Optional[str] = None) -> bool:
        """Add a new wallet for the user"""
        try:
            with next(get_db()) as session:
                session.execute(
                    text("""
                    INSERT INTO wallets (user_id, wallet_address, chain_type, label)
                    VALUES (:user_id, :wallet_address, :chain_type, :label)
                    """),
                    {
                        "user_id": self.user_id,
                        "wallet_address": wallet_address,
                        "chain_type": chain_type,
                        "label": label
                    }
                )
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding wallet: {str(e)}")
            return False

    def get_wallets(self) -> List[Dict]:
        """Get all wallets for the user"""
        try:
            with next(get_db()) as session:
                result = session.execute(
                    text("""
                    SELECT wallet_address, chain_type, label, created_at
                    FROM wallets
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    """),
                    {"user_id": self.user_id}
                ).fetchall()
                
                return [
                    {
                        "address": row[0],
                        "chain": row[1],
                        "label": row[2],
                        "added_on": row[3].strftime("%Y-%m-%d %H:%M:%S")
                    }
                    for row in result
                ]
        except Exception as e:
            logger.error(f"Error getting wallets: {str(e)}")
            return []

    def record_transaction(
        self,
        transaction_type: str,
        amount: float,
        currency: str,
        wallet_address: Optional[str] = None
    ) -> bool:
        """Record a new transaction"""
        try:
            with next(get_db()) as session:
                session.execute(
                    text("""
                    INSERT INTO transactions
                    (user_id, transaction_type, amount, currency, status, wallet_address)
                    VALUES (:user_id, :type, :amount, :currency, 'completed', :wallet)
                    """),
                    {
                        "user_id": self.user_id,
                        "type": transaction_type,
                        "amount": amount,
                        "currency": currency,
                        "wallet": wallet_address
                    }
                )
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error recording transaction: {str(e)}")
            return False

    def get_transactions(self, limit: int = 50) -> List[Dict]:
        """Get recent transactions for the user"""
        try:
            with next(get_db()) as session:
                result = session.execute(
                    text("""
                    SELECT transaction_type, amount, currency, status, wallet_address, created_at
                    FROM transactions
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                    """),
                    {"user_id": self.user_id, "limit": limit}
                ).fetchall()
                
                return [
                    {
                        "type": row[0],
                        "amount": float(row[1]),
                        "currency": row[2],
                        "status": row[3],
                        "wallet": row[4],
                        "date": row[5].strftime("%Y-%m-%d %H:%M:%S")
                    }
                    for row in result
                ]
        except Exception as e:
            logger.error(f"Error getting transactions: {str(e)}")
            return []
