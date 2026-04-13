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
SUPPORT_USERNAME = "@FCBD_HELPLINE_BOT"
ADMIN_USERNAME   = "@FCBD_HELPLINE_BOT"

# ─── Force Subscribe ──────────────────────────────────────────
# চ্যানেল username — @ ছাড়া দাও
# None বা খালি হলে Force Sub disabled
_raw_fsub         = os.getenv("FORCE_SUB_CHANNEL", "FCBD_OFFICIAL")
FORCE_SUB_CHANNEL = _raw_fsub.strip() if _raw_fsub.strip() else None

# ─── Payment Config (শুধু bKash ও Nagad) ─────────────────────
BKASH_NUMBER = os.getenv("BKASH_NUMBER", "01XXXXXXXXX")
NAGAD_NUMBER = os.getenv("NAGAD_NUMBER", "01XXXXXXXXX")

# ─── Payment Info ─────────────────────────────────────────────
PAYMENT_INFO = (
    "📲 **bKash:** `{bkash}`\n"
    "📲 **Nagad:** `{nagad}`\n\n"
    "💬 **Support:** {admin}"
).format(
    bkash = BKASH_NUMBER,
    nagad = NAGAD_NUMBER,
    admin = ADMIN_USERNAME,
)
