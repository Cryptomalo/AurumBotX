"""
Database models for AurumBotX trading platform
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class TradingData(Base):
    """Model for storing trading data and signals"""
    __tablename__ = 'trading_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    symbol = Column(String(20), nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Float)
    signal = Column(String(10))  # BUY, SELL, HOLD
    confidence = Column(Float)
    strategy = Column(String(50))
    metadata_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class TradeExecution(Base):
    """Model for storing executed trades"""
    __tablename__ = 'trade_executions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    order_id = Column(String(100))
    status = Column(String(20))  # FILLED, PARTIAL, CANCELLED
    strategy = Column(String(50))
    profit_loss = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class MarketData(Base):
    """Model for storing market data"""
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    symbol = Column(String(20), nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    interval = Column(String(10), nullable=False)  # 1m, 5m, 1h, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

