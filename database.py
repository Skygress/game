from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import Config
import json

Base = declarative_base()

# Create engine with SQLite support
if Config.DATABASE_URL.startswith('sqlite:///'):
    engine = create_engine(Config.DATABASE_URL, connect_args={'check_same_thread': False})
else:
    engine = create_engine(Config.DATABASE_URL)

Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    coins = Column(Float, default=Config.STARTING_COINS)
    portfolio = Column(String, default=json.dumps({crypto: 0 for crypto in Config.CRYPTO.keys()}))
    total_invested = Column(Float, default=0)
    last_daily = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    crypto = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    action = Column(String)  # 'buy' or 'sell'
    timestamp = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(engine)
