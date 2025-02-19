from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
import os
from typing import Optional

Base = declarative_base()

class TradingData(Base):
    __tablename__ = 'trading_data'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    symbol = Column(String)
    price = Column(Float)
    volume = Column(Float)
    side = Column(String)  # buy/sell
    strategy = Column(String)
    profit_loss = Column(Float, default=0.0)
    metadata = Column(JSON)

    def __repr__(self):
        return f"<TradingData(symbol='{self.symbol}', price={self.price}, volume={self.volume}, side='{self.side}', strategy='{self.strategy}', profit_loss={self.profit_loss}, metadata={self.metadata})>"

    @property
    def as_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'price': self.price,
            'volume': self.volume,
            'timestamp': self.timestamp.isoformat(),
            'side': self.side,
            'strategy': self.strategy,
            'profit_loss': self.profit_loss,
            'metadata': self.metadata
        }

class TradingStrategy(Base):
    __tablename__ = 'trading_strategies'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    parameters = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


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