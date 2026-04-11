# app.py
# Copyright @YourChannel
# ─────────────────────────────────────────────────────────────
# Pyrogram Client instance।
# main.py এবং সব plugin এই module থেকে `app` import করে।
# ─────────────────────────────────────────────────────────────

from pyrogram import Client

from config import API_HASH, API_ID, BOT_TOKEN

app = Client(
    name="course_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)
