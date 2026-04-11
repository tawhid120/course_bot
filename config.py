# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Telegram Credentials ───────────────────────────────────────────────────
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ─── Admin Configuration ────────────────────────────────────────────────────
# Comma-separated Telegram user IDs of admins
# Example: ADMIN_IDS=123456789,987654321
_raw_admins = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [
    int(uid.strip())
    for uid in _raw_admins.split(",")
    if uid.strip().isdigit()
]

# ─── MongoDB Configuration ───────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "course_bot_db")

# ─── Payment Configuration ───────────────────────────────────────────────────
PAYMENT_INFO = os.getenv(
    "PAYMENT_INFO",
    "Please send payment to:\n"
    "📱 *UPI:* yourpayment@upi\n"
    "🏦 *Bank:* XXXX-XXXX-XXXX\n\n"
    "After payment, send screenshot to admin.",
)

# ─── Bot Settings ────────────────────────────────────────────────────────────
BOT_NAME = os.getenv("BOT_NAME", "EduCourse Bot")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@support")
