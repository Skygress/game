import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from config import Config
from database import init_db, Session, User
from game_logic import GameLogic
import json

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    init_db()
    logger.info("✅ Database initialized successfully")
except Exception as e:
    logger.error(f"❌ Database init error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    game_user = GameLogic.get_user(user.id, user.username)
    
    welcome_text = f"""
🚀 *WELCOME TO CRYPTO TYCOON!* 🚀

💰 Your virtual crypto trading empire starts now!
📈 You have *{game_user.coins:.2f} CRED* to start trading.

🎮 *HOW TO PLAY:*
• Buy low, sell high to grow your portfolio
• Check prices daily for market movements
• Claim daily bonus every 24 hours
• Compete on the leaderboard

⚡ *QUICK COMMANDS:*
/portfolio - View your holdings
/trade - Buy or sell crypto
/prices - Check current prices
/daily - Claim your bonus
/leaderboard - See top players

💡 *Start trading now!* Use /trade to make your first move.
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    game_user = GameLogic.get_user(user_id)
    prices = GameLogic.get_current_prices()
    portfolio = json.loads(game_user.portfolio)
    
    text = f"📊 *YOUR PORTFOLIO*\n\n💵 *Cash:* {game_user.coins:.2f} CRED\n\n"
    total_value = game_user.coins
    
    for crypto, amount in portfolio.items():
        if amount > 0:
            current_price = prices[crypto]
            value = amount * current_price
            total_value += value
            text += f"{Config.CRYPTO[crypto]['icon']} *{crypto}*: {amount:.6f} (${current_price:.2f})\n"
    
    text += f"\n💰 *Total Value:* ${total_value:.2f}"
    text += f"\n📈 *Total Invested:* ${game_user.total_invested:.2f}"
    await update.message.reply_text(text, parse_mode='Markdown')

async def prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prices = GameLogic.get_current_prices()
    text = "📈 *CURRENT MARKET PRICES*\n\n"
    for crypto, price in prices.items():
        text += f"{Config.CRYPTO[crypto]['icon']} *{crypto}*: ${price:.2f}\n"
    await update.message.reply_text(text, parse_mode='Markdown')

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    success, message = GameLogic.claim_daily(update.effective_user.id)
    await update.message.reply_text(message)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    users = session.query(User).order_by(User.coins.desc()).limit(10).all()
    
    text = "🏆 *TOP TRADERS* 🏆\n\n"
    for i, user in enumerate(users, 1):
        portfolio = json.loads(user.portfolio)
        prices = GameLogic.get_current_prices()
        total_value = user.coins
        
        for crypto, amount in portfolio.items():
            if amount > 0:
                total_value += amount * prices[crypto]
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        username = user.username or f"Player_{user.telegram_id}"
        text += f"{medal} *{username}*: ${total_value:.2f}\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def trade_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for crypto in Config.CRYPTO:
        keyboard.append([InlineKeyboardButton(f"{Config.CRYPTO[crypto]['icon']} {crypto}", callback_data=f"trade_{crypto}")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="trade_back")])
    
    await update.message.reply_text(
        "🔄 *Select cryptocurrency to trade:*",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def trade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "trade_back":
        await query.edit_message_text("Main menu - use /trade to start trading again")
        return
    
    _, crypto = query.data.split('_')
    prices = GameLogic.get_current_prices()
    price = prices[crypto]
    user_id = update.effective_user.id
    game_user = GameLogic.get_user(user_id)
    portfolio = json.loads(game_user.portfolio)
    holding = portfolio.get(crypto, 0)
    
    keyboard = [
        [InlineKeyboardButton("💰 Buy", callback_data=f"buy_{crypto}"),
         InlineKeyboardButton("💵 Sell", callback_data=f"sell_{crypto}")],
        [InlineKeyboardButton("🔙 Back", callback_data="trade_back")]
    ]
    
    await query.edit_message_text(
        f"{Config.CRYPTO[crypto]['icon']} *{crypto} Trading*\n\n"
        f"💰 Current Price: ${price:.2f}\n"
        f"📊 Your Holdings: {holding:.6f}\n"
        f"💵 Your Balance: {game_user.coins:.2f} CRED\n\n"
        f"*Select action:*",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def trade_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action, crypto = query.data.split('_')
    context.user_data['action'] = action
    context.user_data['crypto'] = crypto
    context.user_data['awaiting_amount'] = True
    
    await query.edit_message_text(
        f"💹 Enter the amount of {crypto} you want to {action}:\n\n"
        f"Example: 0.5 (for buying/selling 0.5 {crypto})",
        parse_mode='Markdown'
    )

async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_amount'):
        return
    
    try:
        amount = float(update.message.text)
        if amount <= 0:
            await update.message.reply_text("❌ Please enter a positive number!")
            return
        
        user_id = update.effective_user.id
        action = context.user_data['action']
        crypto = context.user_data['crypto']
        
        if action == 'buy':
            success, message = GameLogic.buy_crypto(user_id, crypto, amount)
        else:
            success, message = GameLogic.sell_crypto(user_id, crypto, amount)
        
        await update.message.reply_text(message)
        context.user_data['awaiting_amount'] = False
        
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📚 *CRYPTO TYCOON - HELP*

🎮 *GAME OVERVIEW*
Build your virtual crypto empire by trading 5 cryptocurrencies. Start with 1000 CRED coins!

📋 *COMMANDS*
/start - Start the game
/portfolio - View your holdings
/trade - Buy or sell crypto
/prices - Check market prices
/daily - Claim daily bonus (100 CRED)
/leaderboard - See top players
/help - Show this help
/stats - View your statistics

💡 *TIPS*
• Buy low, sell high
• Check prices regularly
• Claim daily bonus every 24 hours
• Diversify your portfolio

⚠️ *DISCLAIMER*
Virtual trading game only. No real money involved. All prices are simulated.

*Enjoy the game!* 🚀
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    game_user = GameLogic.get_user(user_id)
    session = Session()
    total_players = session.query(User).count()
    
    portfolio = json.loads(game_user.portfolio)
    prices = GameLogic.get_current_prices()
    total_value = game_user.coins
    
    for crypto, amount in portfolio.items():
        if amount > 0:
            total_value += amount * prices[crypto]
    
    text = f"""
📊 *YOUR STATISTICS*

👤 Username: @{game_user.username or 'N/A'}
💰 Balance: {game_user.coins:.2f} CRED
💎 Total Portfolio: ${total_value:.2f}
📈 Total Invested: ${game_user.total_invested:.2f}
🎯 Holdings: {sum(1 for v in portfolio.values() if v > 0)} assets
🎮 Players: {total_players}

*Keep trading!* 🚀
"""
    await update.message.reply_text(text, parse_mode='Markdown')

def main():
    if not Config.TOKEN:
        logger.error("❌ BOT_TOKEN not set!")
        return
    
    app = Application.builder().token(Config.TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("prices", prices))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("trade", trade_menu))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats))
    
    app.add_handler(CallbackQueryHandler(trade_callback, pattern="^trade_"))
    app.add_handler(CallbackQueryHandler(trade_action, pattern="^(buy|sell)_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount))
    
    logger.info("🚀 Bot is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
