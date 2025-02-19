from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
import os
from typing import Optional

Base = declarative_base()

class TradingData(Base):
    __tablename__ = 'trading_data'

    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False, index=True)
    price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<TradingData(symbol='{self.symbol}', price={self.price}, volume={self.volume})>"

    @property
    def as_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'price': self.price,
            'volume': self.volume,
            'timestamp': self.timestamp.isoformat()
        }

def get_database_session() -> scoped_session:
    """Create database session with connection pooling and proper error handling"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")

    # Remove SSL parameter if present
    if 'sslmode=' in db_url:
        db_url = db_url.replace('?sslmode=require', '')

    engine = create_engine(
        db_url,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_pre_ping=True,
        pool_recycle=3600
    )

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)