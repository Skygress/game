import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_ID = os.getenv('ADMIN_ID')
    
    STARTING_COINS = 1000
    DAILY_BONUS = 100
    TRANSACTION_FEE = 0.01
    
    CRYPTO = {
        'BTC': {'name': 'Bitcoin', 'icon': '🟡'},
        'ETH': {'name': 'Ethereum', 'icon': '🔷'},
        'SOL': {'name': 'Solana', 'icon': '🟣'},
        'ADA': {'name': 'Cardano', 'icon': '🔴'},
        'DOT': {'name': 'Polkadot', 'icon': '🟠'}
    }
    
    INITIAL_PRICES = {
        'BTC': 42000,
        'ETH': 2800,
        'SOL': 150,
        'ADA': 0.45,
        'DOT': 7.50
    }
