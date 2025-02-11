from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError
import os
from datetime import datetime
import time

# Improved database connection handling with retry mechanism
def get_db():
    """Generator function per ottenere una sessione del database"""
    db = Database(os.getenv('DATABASE_URL'))
    try:
        yield db.session
    except Exception as e:
        print(f"Database connection error: {e}")
        raise
    finally:
        if db.session:
            db.session.close()

class Database:
    def __init__(self, connection_string, max_retries=5):
        self.connection_string = connection_string
        self.max_retries = max_retries
        self.engine = None
        self.session = None
        self.connect()

    def connect(self):
        retry_count = 0
        retry_delay = 1

        while retry_count < self.max_retries:
            try:
                self.engine = create_engine(self.connection_string)
                Session = sessionmaker(bind=self.engine)
                self.session = Session()
                print("Database connection established")
                return True
            except SQLAlchemyError as e:
                print(f"Database connection attempt {retry_count + 1} failed: {e}")
                retry_count += 1
                time.sleep(retry_delay)
                retry_delay *= 2

        raise Exception("Failed to connect to database after multiple attempts")

    def get_session(self):
        if not self.session:
            self.connect()
        return self.session


Base = declarative_base()

class TradingStrategy(Base):
    __tablename__ = "trading_strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    parameters = Column(String)  # JSON string of strategy parameters
    created_at = Column(DateTime, default=datetime.utcnow)
    simulations = relationship("SimulationResult", back_populates="strategy")

class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("trading_strategies.id"))
    symbol = Column(String, index=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    initial_balance = Column(Float)
    final_balance = Column(Float)
    total_trades = Column(Integer)
    win_rate = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    strategy = relationship("TradingStrategy", back_populates="simulations")

# Ensure all tables exist
def init_db():
    # Create tables
    Base.metadata.create_all(bind=create_engine(os.getenv('DATABASE_URL')))

    # Create subscription plans if they don't exist
    with next(get_db()) as session:
        session.execute(text("""
        CREATE TABLE IF NOT EXISTS subscription_plans (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            duration_months INTEGER NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            description TEXT
        );
        """))

        session.execute(text("""
        CREATE TABLE IF NOT EXISTS activation_codes (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) UNIQUE NOT NULL,
            plan_id INTEGER REFERENCES subscription_plans(id),
            expires_at TIMESTAMP NOT NULL,
            is_used BOOLEAN DEFAULT FALSE,
            used_by INTEGER,
            used_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """))

        session.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255),
            password_hash VARCHAR(255),
            subscription_expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """))

        session.commit()

# Initialize tables
init_db()