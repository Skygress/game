import random
from datetime import datetime, timedelta
from database import Session, User, Transaction
from config import Config
import json

class GameLogic:
    
    @staticmethod
    def get_user(telegram_id, username=None):
        session = Session()
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                portfolio=json.dumps({crypto: 0 for crypto in Config.CRYPTO.keys()})
            )
            session.add(user)
            session.commit()
        
        return user
    
    @staticmethod
    def get_current_prices():
        """Mock market prices with random fluctuations"""
        base_prices = Config.INITIAL_PRICES.copy()
        
        for crypto in base_prices:
            # Random fluctuation between -5% and +5%
            change = random.uniform(-0.05, 0.05)
            base_prices[crypto] = round(base_prices[crypto] * (1 + change), 2)
            
        return base_prices
    
    @staticmethod
    def buy_crypto(telegram_id, crypto_symbol, amount):
        if crypto_symbol not in Config.CRYPTO:
            return False, "Invalid cryptocurrency"
        
        prices = GameLogic.get_current_prices()
        price = prices[crypto_symbol]
        total_cost = amount * price * (1 + Config.TRANSACTION_FEE)
        
        session = Session()
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        
        if not user:
            return False, "User not found"
        
        if user.coins < total_cost:
            return False, f"Insufficient coins. You need {total_cost:.2f} CRED"
        
        # Update user
        portfolio = json.loads(user.portfolio)
        portfolio[crypto_symbol] = portfolio.get(crypto_symbol, 0) + amount
        
        user.coins -= total_cost
        user.portfolio = json.dumps(portfolio)
        user.total_invested += total_cost
        
        # Log transaction
        transaction = Transaction(
            user_id=telegram_id,
            crypto=crypto_symbol,
            amount=amount,
            price=price,
            action='buy'
        )
        session.add(transaction)
        session.commit()
        
        return True, f"✅ Bought {amount} {Config.CRYPTO[crypto_symbol]['name']} at ${price} each"
    
    @staticmethod
    def sell_crypto(telegram_id, crypto_symbol, amount):
        if crypto_symbol not in Config.CRYPTO:
            return False, "Invalid cryptocurrency"
        
        session = Session()
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        
        if not user:
            return False, "User not found"
        
        portfolio = json.loads(user.portfolio)
        current_holding = portfolio.get(crypto_symbol, 0)
        
        if current_holding < amount:
            return False, f"You only have {current_holding} {Config.CRYPTO[crypto_symbol]['name']}"
        
        prices = GameLogic.get_current_prices()
        price = prices[crypto_symbol]
        total_value = amount * price * (1 - Config.TRANSACTION_FEE)
        
        # Update user
        portfolio[crypto_symbol] = current_holding - amount
        user.portfolio = json.dumps(portfolio)
        user.coins += total_value
        
        # Log transaction
        transaction = Transaction(
            user_id=telegram_id,
            crypto=crypto_symbol,
            amount=amount,
            price=price,
            action='sell'
        )
        session.add(transaction)
        session.commit()
        
        return True, f"✅ Sold {amount} {Config.CRYPTO[crypto_symbol]['name']} at ${price} each"
    
    @staticmethod
    def claim_daily(telegram_id):
        session = Session()
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        
        if not user:
            return False, "User not found"
        
        now = datetime.utcnow()
        if user.last_daily and now - user.last_daily < timedelta(hours=24):
            remaining = timedelta(hours=24) - (now - user.last_daily)
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            return False, f"⏰ Already claimed today! Come back in {hours}h {minutes}m"
        
        user.coins += Config.DAILY_BONUS
        user.last_daily = now
        session.commit()
        
        return True, f"🎉 Daily bonus claimed! +{Config.DAILY_BONUS} CRED"
