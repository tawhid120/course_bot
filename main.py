# main.py
# Copyright @YourChannel
# Channel t.me/YourChannel
# ─────────────────────────────────────────────────────────────
# এই ফাইলটা আর কখনো পরিবর্তন করতে হবে না।
# নতুন plugin/auth/misc ফাইল যোগ করলে শুধু
# সেই ফোল্ডারের __init__.py তে এক লাইন যোগ করো।
# ─────────────────────────────────────────────────────────────

import asyncio

# ── uvloop: Linux এ event loop 2-4x দ্রুত করে ────────────────
try:
    import uvloop
    uvloop.install()
    print("✅ uvloop installed — event loop boosted!")
except ImportError:
    print("⚠️ uvloop not available, using default asyncio loop")

from utils import LOGGER

# ── Database init ──────────────────────────────────────────────
from db import init_db

# ── Handler setup functions ────────────────────────────────────
from plugins import setup_plugins_handlers
from auth    import setup_auth_handlers
from misc    import handle_callback_query, setup_misc_handlers

# ── Reply Keyboard button router (সবার শেষে register হয়) ─────
from misc.button_router import setup_button_router

# ── Pyrogram Client ────────────────────────────────────────────
from app import app

# ── Startup: DB initialize ─────────────────────────────────────
asyncio.get_event_loop().run_until_complete(init_db())

# ── সব handler register করো ───────────────────────────────────
# ক্রম গুরুত্বপূর্ণ:
#   1. plugins  (course flow, admin panel, start)
#   2. auth     (login, logout, session)
#   3. misc     (settings, referral, etc.)
#   4. button_router (সবার শেষে — reply keyboard)

setup_plugins_handlers(app)
setup_auth_handlers(app)
setup_misc_handlers(app)
setup_button_router(app)


# ── Global Callback Query handler ──────────────────────────────
@app.on_callback_query()
async def handle_callback(client, callback_query):
    await handle_callback_query(client, callback_query)


LOGGER.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
LOGGER.info("   Bot Successfully Started! 💥    ")
LOGGER.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
app.run()
