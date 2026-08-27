import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from config import Config
from database import init_db, Session, User
from game_logic import GameLogic
import json
import os

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize database
try:
    init_db()
    logger.info("✅ Database initialized successfully")
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")

# Mini App URL
MINI_APP_URL = "https://tycoonapp.netlify.app/"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - shows welcome with Mini App launch button"""
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
/app - Launch Mini App

💡 *Start trading now!* Click the button below or use /trade
"""
    
    # Create Mini App button
    keyboard = [
        [InlineKeyboardButton(
            "🚀 Launch Crypto Tycoon App",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )],
        [InlineKeyboardButton("📊 Quick Trade", callback_data="quick_trade")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def app_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Launch the Mini App directly"""
    keyboard = [[
        InlineKeyboardButton(
            "🚀 Open Crypto Tycoon",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📱 *Click the button below to launch the Crypto Tycoon Mini App!*\n\n"
        "Experience the full trading experience with real-time prices, "
        "portfolio tracking, and more!",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View portfolio"""
    user_id = update.effective_user.id
    game_user = GameLogic.get_user(user_id)
    
    prices = GameLogic.get_current_prices()
    portfolio = json.loads(game_user.portfolio)
    
    portfolio_text = f"📊 *YOUR PORTFOLIO*\n\n"
    portfolio_text += f"💵 *Cash:* {game_user.coins:.2f} CRED\n\n"
    
    total_value = game_user.coins
    for crypto, amount in portfolio.items():
        if amount > 0:
            current_price = prices[crypto]
            value = amount * current_price
            total_value += value
            portfolio_text += f"{Config.CRYPTO[crypto]['icon']} *{crypto}*: {amount:.6f} (${current_price:.2f})\n"
    
    portfolio_text += f"\n💰 *Total Value:* ${total_value:.2f}"
    portfolio_text += f"\n📈 *Total Invested:* ${game_user.total_invested:.2f}"
    
    # Add Mini App button
    keyboard = [[
        InlineKeyboardButton(
            "📱 Open in App",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        portfolio_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current prices"""
    prices = GameLogic.get_current_prices()
    
    price_text = "📈 *CURRENT MARKET PRICES*\n\n"
    for crypto, price in prices.items():
        price_text += f"{Config.CRYPTO[crypto]['icon']} *{crypto}*: ${price:.2f}\n"
    
    # Add Mini App button for better trading experience
    keyboard = [[
        InlineKeyboardButton(
            "📱 Trade in App",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        price_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claim daily bonus"""
    user_id = update.effective_user.id
    success, message = GameLogic.claim_daily(user_id)
    await update.message.reply_text(message)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leaderboard"""
    session = Session()
    try:
        users = session.query(User).order_by(User.coins.desc()).limit(10).all()
    except Exception as e:
        await update.message.reply_text("❌ Error fetching leaderboard")
        logger.error(f"Leaderboard error: {e}")
        return
    
    leaderboard_text = "🏆 *TOP TRADERS* 🏆\n\n"
    
    for i, user in enumerate(users, 1):
        # Calculate total portfolio value
        portfolio = json.loads(user.portfolio)
        prices = GameLogic.get_current_prices()
        total_value = user.coins
        
        for crypto, amount in portfolio.items():
            if amount > 0:
                total_value += amount * prices[crypto]
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        username = user.username or f"Player_{user.telegram_id}"
        leaderboard_text += f"{medal} *{username}*: ${total_value:.2f}\n"
    
    # Add Mini App button
    keyboard = [[
        InlineKeyboardButton(
            "📱 View Full Leaderboard",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        leaderboard_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def trade_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show trade menu with Mini App option"""
    keyboard = [
        [
            InlineKeyboardButton(
                "📱 Trade in App (Recommended)",
                web_app=WebAppInfo(url=MINI_APP_URL)
            )
        ],
        [InlineKeyboardButton("💰 Buy", callback_data="trade_buy"),
         InlineKeyboardButton("💵 Sell", callback_data="trade_sell")],
        [InlineKeyboardButton("🔙 Back", callback_data="trade_back")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🔄 *Select trading option:*\n\n"
        "For the best experience, use the Mini App!",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def trade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle trade callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "trade_back":
        await query.edit_message_text(
            "Main menu - use /trade to start trading again or /start for the main menu",
            parse_mode='Markdown'
        )
        return
    
    if data == "trade_buy" or data == "trade_sell":
        # Direct users to Mini App for better experience
        keyboard = [[
            InlineKeyboardButton(
                "📱 Open App to Trade",
                web_app=WebAppInfo(url=MINI_APP_URL)
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📱 *For buying and selling, please use the Mini App!*\n\n"
            f"The app provides real-time prices, better UI, and instant trades.\n\n"
            f"Click the button below to launch the app.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    help_text = """
📚 *CRYPTO TYCOON - HELP*

🎮 *GAME OVERVIEW*
Build your virtual crypto empire by trading 5 cryptocurrencies. Start with 1000 CRED coins and grow your wealth!

📋 *COMMANDS*
/start - Start the game
/portfolio - View your holdings
/trade - Buy or sell crypto
/prices - Check market prices
/daily - Claim daily bonus (100 CRED)
/leaderboard - See top players
/app - Launch Mini App
/help - Show this help
/stats - View your statistics

📱 *MINI APP*
For the best experience, use the /app command to launch the full Crypto Tycoon Mini App!
The app features:
• Real-time price updates
• Beautiful trading interface
• Portfolio visualization
• Leaderboard
• Daily bonuses
• And much more!

💡 *TIPS*
• Buy when prices are low, sell when high
• Check prices regularly for opportunities
• Claim daily bonus every 24 hours
• Diversify your portfolio

⚠️ *DISCLAIMER*
This is a *virtual trading game* only. No real money is involved. All prices are simulated for entertainment purposes.

🔒 *PRIVACY*
Your data is stored securely. We only track game progress and username.

*Enjoy the game!* 🚀
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    user_id = update.effective_user.id
    game_user = GameLogic.get_user(user_id)
    
    session = Session()
    try:
        total_players = session.query(User).count()
    except Exception as e:
        total_players = "Error"
        logger.error(f"Stats error: {e}")
    
    portfolio = json.loads(game_user.portfolio)
    prices = GameLogic.get_current_prices()
    total_value = game_user.coins
    
    for crypto, amount in portfolio.items():
        if amount > 0:
            total_value += amount * prices[crypto]
    
    stats_text = f"""
📊 *YOUR STATISTICS*

👤 Username: @{game_user.username or 'N/A'}
💰 Balance: {game_user.coins:.2f} CRED
💎 Total Portfolio: ${total_value:.2f}
📈 Total Invested: ${game_user.total_invested:.2f}
🎯 Holdings: {sum(1 for v in portfolio.values() if v > 0)} assets
🎮 Players: {total_players}

*Keep trading!* 🚀
"""
    
    # Add Mini App button
    keyboard = [[
        InlineKeyboardButton(
            "📱 Open in App",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        stats_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

def main():
    """Start the bot"""
    if not Config.TOKEN:
        logger.error("❌ BOT_TOKEN not set in environment variables!")
        return
    
    try:
        application = Application.builder().token(Config.TOKEN).build()
        logger.info("✅ Bot application created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create bot application: {e}")
        return

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("app", app_command))
    application.add_handler(CommandHandler("portfolio", portfolio))
    application.add_handler(CommandHandler("prices", prices))
    application.add_handler(CommandHandler("daily", daily))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("trade", trade_menu))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(trade_callback, pattern="^trade_"))
    application.add_handler(CallbackQueryHandler(leaderboard_callback, pattern="^leaderboard$"))
    application.add_handler(CallbackQueryHandler(quick_trade_callback, pattern="^quick_trade$"))
    
    # Start the Bot
    logger.info("🚀 Bot is starting...")
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")

# Additional callback handlers
async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle leaderboard button press"""
    query = update.callback_query
    await query.answer()
    await leaderboard(update, context)

async def quick_trade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quick trade button press"""
    query = update.callback_query
    await query.answer()
    keyboard = [[
        InlineKeyboardButton(
            "📱 Open App to Trade",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "📱 *Launch the Crypto Tycoon Mini App for the best trading experience!*\n\n"
        "• Real-time prices\n"
        "• Beautiful UI\n"
        "• Instant trades\n"
        "• Portfolio tracking\n\n"
        "Click below to launch!",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

if __name__ == '__main__':
    main()
