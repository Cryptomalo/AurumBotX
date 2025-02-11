import os
from typing import Optional, Dict, List
import logging
from datetime import datetime, timedelta
import secrets
import string
from sqlalchemy import text
from utils.database import get_db

logger = logging.getLogger(__name__)

class SubscriptionManager:
    def __init__(self):
        self.code_length = 16

    def generate_admin_code(self, plan_id: int, batch_size: int = 1) -> List[str]:
        """Genera nuovi codici di attivazione (solo per amministratori)"""
        try:
            generated_codes = []
            with next(get_db()) as session:
                # Ottieni la durata del piano
                plan = session.execute(
                    text("SELECT duration_months FROM subscription_plans WHERE id = :plan_id"),
                    {"plan_id": plan_id}
                ).fetchone()

                if not plan:
                    raise ValueError("Piano non valido")

                # Genera codici univoci
                for _ in range(batch_size):
                    # Genera un codice casuale con prefisso
                    prefix = "AB"  # AurumBot prefix
                    alphabet = string.ascii_uppercase + string.digits
                    code = prefix + ''.join(secrets.choice(alphabet) for _ in range(self.code_length - 2))

                    # Calcola la data di scadenza
                    expires_at = datetime.now() + timedelta(days=30 * plan[0])

                    # Inserisci il codice nel database
                    session.execute(
                        text("""
                        INSERT INTO activation_codes (code, plan_id, expires_at)
                        VALUES (:code, :plan_id, :expires_at)
                        """),
                        {
                            "code": code,
                            "plan_id": plan_id,
                            "expires_at": expires_at
                        }
                    )
                    generated_codes.append(code)

                session.commit()
                return generated_codes

        except Exception as e:
            logger.error(f"Errore nella generazione del codice: {str(e)}")
            return []

    def activate_subscription(self, code: str, user_id: int) -> bool:
        """Attiva un abbonamento con un codice"""
        try:
            with next(get_db()) as session:
                # Verifica il codice
                result = session.execute(
                    text("""
                    SELECT ac.id, ac.expires_at, sp.duration_months 
                    FROM activation_codes ac
                    JOIN subscription_plans sp ON ac.plan_id = sp.id
                    WHERE ac.code = :code AND ac.is_used = FALSE
                    """),
                    {"code": code}
                ).fetchone()

                if not result:
                    return False

                code_id, expires_at, duration_months = result

                # Aggiorna il codice come utilizzato
                session.execute(
                    text("""
                    UPDATE activation_codes 
                    SET is_used = TRUE, used_by = :user_id, used_at = CURRENT_TIMESTAMP
                    WHERE id = :code_id
                    """),
                    {"user_id": user_id, "code_id": code_id}
                )

                # Aggiorna la scadenza dell'abbonamento dell'utente
                new_expiry = datetime.now() + timedelta(days=30 * duration_months)
                session.execute(
                    text("""
                    UPDATE users 
                    SET subscription_expires_at = :expires_at
                    WHERE id = :user_id
                    """),
                    {"expires_at": new_expiry, "user_id": user_id}
                )

                session.commit()
                return True

        except Exception as e:
            logger.error(f"Errore nell'attivazione dell'abbonamento: {str(e)}")
            return False

    def check_subscription(self, user_id: int) -> bool:
        """Verifica se l'abbonamento è attivo"""
        try:
            with next(get_db()) as session:
                result = session.execute(
                    text("""
                    SELECT subscription_expires_at
                    FROM users
                    WHERE id = :user_id
                    """),
                    {"user_id": user_id}
                ).fetchone()

                if not result or not result[0]:
                    return False

                return result[0] > datetime.now()

        except Exception as e:
            logger.error(f"Errore nella verifica dell'abbonamento: {str(e)}")
            return False

    def get_subscription_info(self, user_id: int) -> Optional[Dict]:
        """Ottiene le informazioni sull'abbonamento dell'utente"""
        try:
            with next(get_db()) as session:
                result = session.execute(
                    text("""
                    SELECT u.subscription_expires_at, ac.used_at, sp.name, sp.duration_months
                    FROM users u
                    LEFT JOIN activation_codes ac ON ac.used_by = u.id
                    LEFT JOIN subscription_plans sp ON ac.plan_id = sp.id
                    WHERE u.id = :user_id
                    ORDER BY ac.used_at DESC
                    LIMIT 1
                    """),
                    {"user_id": user_id}
                ).fetchone()

                if not result:
                    return None

                expires_at, activated_at, plan_name, duration = result

                return {
                    "expires_at": expires_at,
                    "activated_at": activated_at,
                    "plan_name": plan_name,
                    "duration_months": duration,
                    "is_active": expires_at > datetime.now() if expires_at else False
                }

        except Exception as e:
            logger.error(f"Errore nel recupero delle informazioni sull'abbonamento: {str(e)}")
            return None

    def get_available_plans(self) -> List[Dict]:
        """Ottiene la lista dei piani disponibili"""
        try:
            with next(get_db()) as session:
                results = session.execute(
                    text("SELECT id, name, duration_months, price, description FROM subscription_plans")
                ).fetchall()

                return [
                    {
                        "id": row[0],
                        "name": row[1],
                        "duration_months": row[2],
                        "price": float(row[3]),
                        "description": row[4]
                    }
                    for row in results
                ]

        except Exception as e:
            logger.error(f"Errore nel recupero dei piani: {str(e)}")
            return []

    def generate_activation_code(self, plan_id: int) -> str:
        """Genera un nuovo codice di attivazione per un piano"""
        try:
            # Genera un codice casuale
            alphabet = string.ascii_uppercase + string.digits
            code = ''.join(secrets.choice(alphabet) for _ in range(self.code_length))

            with next(get_db()) as session:
                # Ottieni la durata del piano
                plan = session.execute(
                    text("SELECT duration_months FROM subscription_plans WHERE id = :plan_id"),
                    {"plan_id": plan_id}
                ).fetchone()

                if not plan:
                    raise ValueError("Piano non valido")

                # Calcola la data di scadenza
                expires_at = datetime.now() + timedelta(days=30 * plan[0])

                # Inserisci il codice nel database
                session.execute(
                    text("""
                    INSERT INTO activation_codes (code, plan_id, expires_at)
                    VALUES (:code, :plan_id, :expires_at)
                    """),
                    {
                        "code": code,
                        "plan_id": plan_id,
                        "expires_at": expires_at
                    }
                )
                session.commit()
                return code

        except Exception as e:
            logger.error(f"Errore nella generazione del codice: {str(e)}")
            return None