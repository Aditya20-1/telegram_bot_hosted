import os
import sqlite3
import logging
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_LINK = os.getenv("CHANNEL_LINK")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise ValueError("BOT_TOKEN is missing")
if not CHANNEL_LINK:
    raise ValueError("CHANNEL_LINK is missing")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL is missing")

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")
conn.commit()

def save_user(user_id: int) -> None:
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

def get_main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("❓ Help", callback_data="help")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context) -> None:
    user = update.effective_user
    if user:
        save_user(user.id)

    welcome_text = (
        "🚀 *Welcome to Viral AI Hub*\n\n"
        "📈 Grow faster with AI and automation\n\n"
        "Use the buttons below or commands:\n"
        "/start - Start the bot\n"
        "/help - Help section\n"
        "/tools - Show AI tools\n"
        "/channel - Join our channel"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

async def help_command(update: Update, context) -> None:
    help_text = (
        "❓ *Help Section*\n\n"
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show help\n"
        "/tools - Show AI tools\n"
        "/channel - Get channel link\n\n"
        "You can also use the buttons in the main menu."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def tools_command(update: Update, context) -> None:
    tools_text = (
        "🧠 *Top AI Tools*\n\n"
        "1. ChatGPT - AI assistant\n"
        "2. Canva AI - Design tools\n"
        "3. Notion AI - Smart notes and writing\n"
        "4. Midjourney - AI image generation\n"
        "5. Runway ML - AI video tools\n\n"
        "More tools coming soon 🚀"
    )
    await update.message.reply_text(tools_text, parse_mode="Markdown")

async def channel_command(update: Update, context) -> None:
    channel_text = f"📢 *Join our channel:*\n{CHANNEL_LINK}"
    await update.message.reply_text(channel_text, parse_mode="Markdown")

async def button_handler(update: Update, context) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "help":
        text = (
            "❓ *Help Section*\n\n"
            "Available commands:\n"
            "/start - Start the bot\n"
            "/help - Show help\n"
            "/tools - Show AI tools\n"
            "/channel - Get channel link\n\n"
            "Use /start anytime to return to the main menu."
        )
        await query.edit_message_text(text=text, parse_mode="Markdown")

telegram_app = Application.builder().token(TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(CommandHandler("tools", tools_command))
telegram_app.add_handler(CommandHandler("channel", channel_command))
telegram_app.add_handler(CallbackQueryHandler(button_handler))

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Bot is running"

@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "ok"

async def init_bot():
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

if __name__ == "__main__":
    asyncio.run(init_bot())
    port = int(os.getenv("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)