# config.py
# Copyright @YourChannel

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Telegram Credentials ─────────────────────────────────────
API_ID      = int(os.getenv("API_ID", "0"))
API_HASH    = os.getenv("API_HASH", "")
BOT_TOKEN   = os.getenv("BOT_TOKEN", "")

# ─── Admin Config ─────────────────────────────────────────────
_raw      = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [
    int(x.strip())
    for x in _raw.split(",")
    if x.strip().isdigit()
]

# ─── MongoDB ──────────────────────────────────────────────────
MONGO_URI     = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "course_bot_db")

# ─── Bot Meta ─────────────────────────────────────────────────
BOT_NAME         = os.getenv("BOT_NAME", "EduCourse Bot")
SUPPORT_USERNAME = "@studyqoro"

# ─── Payment Config ───────────────────────────────────────────
ADMIN_USERNAME = "@studyqoro"

# bKash
BKASH_NUMBER = os.getenv("BKASH_NUMBER", "01XXXXXXXXX")

# Nagad
NAGAD_NUMBER = os.getenv("NAGAD_NUMBER", "01XXXXXXXXX")

# Binance USDT TRC20
BINANCE_UID     = os.getenv("BINANCE_UID", "YOUR_BINANCE_UID")
BINANCE_ADDRESS = os.getenv(
    "BINANCE_ADDRESS",
    "YOUR_TRC20_WALLET_ADDRESS",
)

# ─── Payment Info (course_flow.py এ use হয়) ──────────────────
PAYMENT_INFO = (
    "📲 **bKash:** `{bkash}`\n"
    "📲 **Nagad:** `{nagad}`\n"
    "🪙 **Binance USDT (TRC20):** `{binance}`\n\n"
    "💬 **Support:** {admin}"
).format(
    bkash   = BKASH_NUMBER,
    nagad   = NAGAD_NUMBER,
    binance = BINANCE_ADDRESS,
    admin   = ADMIN_USERNAME,
)
