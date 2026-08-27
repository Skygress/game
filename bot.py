import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_ID = os.getenv('ADMIN_ID')
    
    # Game settings
    STARTING_COINS = 1000
    DAILY_BONUS = 100
    TRANSACTION_FEE = 0.01
    
    # Cryptocurrencies in game
    CRYPTO = {
        'BTC': {'name': 'Bitcoin', 'icon': '🟡'},
        'ETH': {'name': 'Ethereum', 'icon': '🔷'},
        'SOL': {'name': 'Solana', 'icon': '🟣'},
        'ADA': {'name': 'Cardano', 'icon': '🔴'},
        'DOT': {'name': 'Polkadot', 'icon': '🟠'}
    }
    
    # Initial prices (will be updated by mock market)
    INITIAL_PRICES = {
        'BTC': 42000,
        'ETH': 2800,
        'SOL': 150,
        'ADA': 0.45,
        'DOT': 7.50
    }
