from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class TradingData(Base):
    __tablename__ = 'trading_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TradingData(symbol='{self.symbol}', price={self.price}, volume={self.volume})>"

def init_db(engine):
    Base.metadata.create_all(engine)
