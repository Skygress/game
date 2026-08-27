import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - shows welcome message"""
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
/help - Get help
/stats - View your stats

💡 *Start trading now!* Use /trade to make your first move.
"""
    
    # Quick action buttons
    keyboard = [
        [InlineKeyboardButton("📊 Quick Trade", callback_data="quick_trade")],
        [InlineKeyboardButton("💰 Portfolio", callback_data="view_portfolio")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="view_leaderboard")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
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
    has_assets = False
    
    for crypto, amount in portfolio.items():
        if amount > 0:
            has_assets = True
            current_price = prices[crypto]
            value = amount * current_price
            total_value += value
            portfolio_text += f"{Config.CRYPTO[crypto]['icon']} *{crypto}*: {amount:.6f} (${current_price:.2f})\n"
    
    if not has_assets:
        portfolio_text += "📭 *No assets yet!* Start trading with /trade\n"
    
    portfolio_text += f"\n💰 *Total Value:* ${total_value:.2f}"
    portfolio_text += f"\n📈 *Total Invested:* ${game_user.total_invested:.2f}"
    
    # Action buttons
    keyboard = [
        [InlineKeyboardButton("🔄 Trade Now", callback_data="quick_trade")],
        [InlineKeyboardButton("📈 View Prices", callback_data="view_prices")]
    ]
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
    
    price_text += "\n💡 *Want to trade?* Use /trade"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Trade Now", callback_data="quick_trade")],
        [InlineKeyboardButton("💰 View Portfolio", callback_data="view_portfolio")]
    ]
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
    
    if not users:
        await update.message.reply_text("📭 No players yet! Be the first to start trading!")
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
    
    keyboard = [
        [InlineKeyboardButton("🔄 Trade Now", callback_data="quick_trade")],
        [InlineKeyboardButton("📊 View Stats", callback_data="view_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        leaderboard_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def trade_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show trade menu"""
    keyboard = []
    for crypto in Config.CRYPTO:
        keyboard.append([InlineKeyboardButton(
            f"{Config.CRYPTO[crypto]['icon']} {crypto}",
            callback_data=f"trade_{crypto}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="trade_back")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🔄 *Select cryptocurrency to trade:*\n\n"
        "💰 *Your Balance:* Use /portfolio to check",
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
            "🔙 *Main Menu*\n\n"
            "Use these commands to navigate:\n"
            "/trade - Start trading\n"
            "/portfolio - View holdings\n"
            "/prices - Check prices\n"
            "/daily - Claim bonus\n"
            "/leaderboard - Top players\n"
            "/help - Get help",
            parse_mode='Markdown'
        )
        return
    
    # Handle quick actions
    if data == "quick_trade":
        await query.edit_message_text(
            "🔄 *Quick Trade*\n\n"
            "Use /trade to select a cryptocurrency to buy or sell.\n\n"
            "💡 *Tip:* Check /prices first to see current market rates!",
            parse_mode='Markdown'
        )
        return
    
    if data == "view_portfolio":
        await query.edit_message_text(
            "📊 *Viewing Portfolio*\n\n"
            "Use /portfolio to see your complete holdings and total value.",
            parse_mode='Markdown'
        )
        return
    
    if data == "view_leaderboard":
        await query.edit_message_text(
            "🏆 *Viewing Leaderboard*\n\n"
            "Use /leaderboard to see the top traders!",
            parse_mode='Markdown'
        )
        return
    
    if data == "view_prices":
        await query.edit_message_text(
            "📈 *Viewing Prices*\n\n"
            "Use /prices to see current market prices.",
            parse_mode='Markdown'
        )
        return
    
    if data == "view_stats":
        await query.edit_message_text(
            "📊 *Viewing Stats*\n\n"
            "Use /stats to see your personal statistics.",
            parse_mode='Markdown'
        )
        return
    
    # Handle crypto selection
    _, crypto = data.split('_')
    context.user_data['trading_crypto'] = crypto
    
    # Show current price and balance
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
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"{Config.CRYPTO[crypto]['icon']} *{crypto} Trading*\n\n"
        f"💰 Current Price: ${price:.2f}\n"
        f"📊 Your Holdings: {holding:.6f}\n"
        f"💵 Your Balance: {game_user.coins:.2f} CRED\n\n"
        f"*Select action:*\n"
        f"💡 *Tip:* Enter the amount in the next step",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def trade_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle buy/sell actions"""
    query = update.callback_query
    await query.answer()
    
    action, crypto = query.data.split('_')
    user_id = update.effective_user.id
    
    # Ask for amount
    context.user_data['action'] = action
    context.user_data['crypto'] = crypto
    context.user_data['awaiting_amount'] = True
    
    await query.edit_message_text(
        f"💹 *Enter the amount of {crypto} you want to {action}*\n\n"
        f"Example: 0.5 (for buying/selling 0.5 {crypto})\n\n"
        f"Send a number like: 0.5, 1.25, or 10",
        parse_mode='Markdown'
    )

async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle amount input from user"""
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
        
        # Reset state
        context.user_data['awaiting_amount'] = False
        context.user_data['action'] = None
        context.user_data['crypto'] = None
        
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        logger.error(f"Trade error: {e}")

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
/help - Show this help
/stats - View your statistics

💡 *TIPS*
• Buy when prices are low, sell when high
• Check prices regularly for opportunities
• Claim daily bonus every 24 hours
• Diversify your portfolio
• Use inline buttons for quick actions

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
    
    keyboard = [
        [InlineKeyboardButton("🔄 Trade Now", callback_data="quick_trade")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="view_leaderboard")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        stats_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Handle quick action buttons
    if data == "quick_trade":
        await trade_menu(update, context)
    elif data == "view_portfolio":
        await portfolio(update, context)
    elif data == "view_leaderboard":
        await leaderboard(update, context)
    elif data == "view_prices":
        await prices(update, context)
    elif data == "view_stats":
        await stats(update, context)
    elif data == "trade_back":
        # Handle trade back
        await query.edit_message_text(
            "🔙 *Main Menu*\n\n"
            "Use these commands to navigate:\n"
            "/trade - Start trading\n"
            "/portfolio - View holdings\n"
            "/prices - Check prices\n"
            "/daily - Claim bonus\n"
            "/leaderboard - Top players\n"
            "/help - Get help",
            parse_mode='Markdown'
        )
    elif data.startswith("trade_"):
        await trade_callback(update, context)
    elif data.startswith("buy_") or data.startswith("sell_"):
        await trade_action(update, context)

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
    application.add_handler(CommandHandler("portfolio", portfolio))
    application.add_handler(CommandHandler("prices", prices))
    application.add_handler(CommandHandler("daily", daily))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("trade", trade_menu))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Message handler for amount input
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount))

    # Start the Bot
    logger.info("🚀 Bot is starting...")
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")

if __name__ == '__main__':
    main()
