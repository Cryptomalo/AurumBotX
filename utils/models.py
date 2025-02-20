from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
import os
from typing import Optional, Dict, Any

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
    trade_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TradingData(symbol='{self.symbol}', price={self.price}, volume={self.volume}, side='{self.side}', strategy='{self.strategy}', profit_loss={self.profit_loss})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'price': self.price,
            'volume': self.volume,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'side': self.side,
            'strategy': self.strategy,
            'profit_loss': self.profit_loss,
            'trade_metadata': self.trade_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @property
    def as_dict(self) -> Dict[str, Any]:
        """Alias for to_dict() for backward compatibility."""
        return self.to_dict()

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
    from sqlalchemy import create_engine

    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")

    # Remove SSL parameter if present
    if 'sslmode=' in db_url:
        db_url = db_url.split('?')[0]

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