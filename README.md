# Crypto Tycoon Bot 🚀

A virtual cryptocurrency trading game for Telegram. Build your crypto empire with virtual money!

## Features
- 💰 Virtual crypto trading with 5 cryptocurrencies
- 📊 Real-time simulated price updates
- 🎯 Daily bonus system
- 🏆 Leaderboard competition
- 📈 Portfolio tracking
- 💵 No real money involved
- 🗄️ SQLite database (no PostgreSQL needed)

## Setup

### 1. Create Telegram Bot
- Talk to @BotFather on Telegram
- Use `/newbot` to create your bot
- Copy the bot token

### 2. Deploy on Railway
- Fork this repository
- Create a new project on Railway
- Connect your GitHub repository
- Add environment variable:
  - `BOT_TOKEN`: Your bot token

### 3. Deploy
Railway will automatically deploy your bot!

## Commands
- `/start` - Start the game
- `/portfolio` - View your holdings
- `/trade` - Buy or sell crypto
- `/prices` - Check market prices
- `/daily` - Claim daily bonus
- `/leaderboard` - See top players
- `/help` - Get help
- `/stats` - View statistics

## Technologies
- Python 3.9+
- python-telegram-bot
- SQLAlchemy
- SQLite
- Railway

## Disclaimer
This is a virtual trading game only. No real money is involved. All prices are simulated.
