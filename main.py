# main.py
# Copyright @YourChannel

"""
Entry point.
Uses Pyrofork (Pyrogram fork) with standard polling via app.run().
Plugins are auto-loaded from the plugins/ directory.
button_router is set up manually after client creation.
"""

import logging

from pyrogram import Client
from pyrogram.enums import ParseMode

from config import API_HASH, API_ID, BOT_TOKEN
from utils import LOGGER


# ─── Client ───────────────────────────────────────────────────────────────────
app = Client(
    name="course_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins"),      # Auto-loads plugins/*.py
    parse_mode=ParseMode.MARKDOWN,
)


# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Register Reply Keyboard router AFTER plugins are loaded
    from misc.button_router import setup_button_router
    setup_button_router(app)

    LOGGER.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    LOGGER.info("   EduCourse Bot  —  Starting   ")
    LOGGER.info("   Mode: Polling (app.run())    ")
    LOGGER.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    app.run()

    LOGGER.info("Bot stopped.")
