import logging
import os
from typing import Optional, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from utils.models import Base, TradingData

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return

        self.engine = None
        self.Session = None
        self.initialized = True

    def initialize(self) -> bool:
        try:
            db_url = os.getenv('DATABASE_URL', 'sqlite:///trading.db')

            self.engine = create_engine(
                db_url,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800
            )

            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            logger.info("Database initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            return False

    def save_trading_data(self, data: Dict[str, Any]) -> bool:
        try:
            if not self.Session:
                if not self.initialize():
                    return False

            session = self.Session()
            try:
                trading_data = TradingData(**data)
                session.add(trading_data)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                logger.error(f"Error saving trading data: {str(e)}")
                return False
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Database operation error: {str(e)}")
            return False