# app.py
# Creates the shared Pyrogram Client instance used throughout the bot.

from pyrogram import Client

from config import API_ID, API_HASH, BOT_TOKEN

app = Client(
    "course_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)
