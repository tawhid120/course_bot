# config.py
# Copyright @YourChannel

import os
from typing import List

# ── Bot Credentials ────────────────────────────────────────────
API_ID:    int = int(os.getenv("API_ID", "0"))
API_HASH:  str = os.getenv("API_HASH", "")
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# ── MongoDB ────────────────────────────────────────────────────
MONGO_URI:     str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME: str = os.getenv("DATABASE_NAME", "coursebot")

# ── Admin Config ───────────────────────────────────────────────
# ADMIN_IDS: comma-separated list of admin user IDs
_raw_admins = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: List[int] = [
    int(x.strip()) for x in _raw_admins.split(",") if x.strip().isdigit()
]

ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "@admin")

# ── Bot Info ───────────────────────────────────────────────────
BOT_NAME:        str = os.getenv("BOT_NAME", "Course Bot")
SUPPORT_USERNAME: str = os.getenv("SUPPORT_USERNAME", "@support")

# ── Force Subscribe ────────────────────────────────────────────
# Set to channel username (e.g. @mychannel) or numeric ID (e.g. -1001234567890)
FORCE_SUB_CHANNEL: str = os.getenv("FORCE_SUB_CHANNEL", "")

# ── Payment Info ───────────────────────────────────────────────
BKASH_NUMBER: str = os.getenv("BKASH_NUMBER", "01XXXXXXXXX")
NAGAD_NUMBER: str = os.getenv("NAGAD_NUMBER", "01XXXXXXXXX")

# Legacy — used by old course_flow.py (can be empty)
PAYMENT_INFO: str = os.getenv("PAYMENT_INFO", "")
