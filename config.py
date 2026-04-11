# config.py
# Copyright @YourChannel

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Telegram Credentials ────────────────────────────────────────────────────
API_ID      = int(os.getenv("API_ID", "0"))
API_HASH    = os.getenv("API_HASH", "")
BOT_TOKEN   = os.getenv("BOT_TOKEN", "")

# ─── Admin IDs ───────────────────────────────────────────────────────────────
# Comma separated: ADMIN_IDS=123456,789012
_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [
    int(x.strip())
    for x in _raw.split(",")
    if x.strip().isdigit()
]

# ─── MongoDB ─────────────────────────────────────────────────────────────────
MONGO_URI      = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME  = os.getenv("DATABASE_NAME", "course_bot_db")

# ─── Payment Info ─────────────────────────────────────────────────────────────
PAYMENT_INFO = os.getenv(
    "PAYMENT_INFO",
    "💳 Send payment to:\n"
    "📱 **UPI:** yourpayment@upi\n\n"
    "After payment tap **✅ I Have Paid** below.",
)

# ─── Bot Meta ─────────────────────────────────────────────────────────────────
BOT_NAME         = os.getenv("BOT_NAME", "EduCourse Bot")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@support")
