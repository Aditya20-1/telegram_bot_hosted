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

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_LINK = os.getenv("CHANNEL_LINK")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing")
if not CHANNEL_LINK:
    raise ValueError("CHANNEL_LINK is missing")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL is missing")

app = Flask(__name__)

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")
conn.commit()

def save_user(user_id: int):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

telegram_app = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context):
    user = update.effective_user
    if user:
        save_user(user.id)

    text = (
        "🚀 *Welcome to Viral AI Hub*\n\n"
        "📈 Grow faster with AI and automation\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Help section\n"
        "/channel - Join our channel"
    )
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

async def help_command(update: Update, context):
    text = (
        "❓ *Help Section*\n\n"
        "/start - Start the bot\n"
        "/help - Show help\n"
        "/channel - Get channel link"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def channel_command(update: Update, context):
    await update.message.reply_text(
        f"📢 *Join our channel:*\n{CHANNEL_LINK}",
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "help":
        text = (
            "❓ *Help Section*\n\n"
            "/start - Start the bot\n"
            "/help - Show help\n"
            "/channel - Get channel link\n\n"
            "Use /start to go back."
        )
        await query.edit_message_text(text=text, parse_mode="Markdown")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(CommandHandler("channel", channel_command))
telegram_app.add_handler(CallbackQueryHandler(button_handler))

_initialized = False

async def init_telegram():
    global _initialized
    if not _initialized:
        await telegram_app.initialize()
        _initialized = True

@app.route("/")
def home():
    return "Bot is running"

@app.route("/set_webhook")
def set_webhook():
    async def _set():
        await init_telegram()
        await telegram_app.bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    asyncio.run(_set())
    return "Webhook set successfully"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)

    async def process():
        await init_telegram()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)

    asyncio.run(process())
    return "ok", 200