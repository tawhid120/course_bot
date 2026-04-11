# auth/__init__.py
# Copyright @YourChannel
# Channel t.me/YourChannel
# ─────────────────────────────────────────────────────────────
# নতুন auth ফাইল যোগ করার নিয়ম:
#
#   ধরো নতুন ফাইল: auth/otp_verify.py
#   সেই ফাইলে:     def setup(app): ...
#
#   এখানে যোগ করো:
#       from .otp_verify import setup as setup_otp
#   এবং _AUTH_SETUPS list এ:
#       setup_otp,
#
#   main.py ছোঁয়ার দরকার নেই।
# ─────────────────────────────────────────────────────────────

from pyrogram import Client

# ── Auth utility (decorator, is_admin) ── সরাসরি export ──────
from .admin_check import (
    is_admin,
    admin_required,
    admin_callback_required,
)

# ── Auth handler setup functions ─────────────────────────────
from .admin_check import setup as setup_admin_check

# ════════════════════════════════════════════════════════════
# ▼▼▼ নতুন auth ফাইল যোগ করলে শুধু এই list এ এক লাইন ▼▼▼
# ════════════════════════════════════════════════════════════

_AUTH_SETUPS = [
    setup_admin_check,
    # setup_otp_verify,   ← নতুন auth handler এখানে
]

# ════════════════════════════════════════════════════════════


def setup_auth_handlers(app: Client) -> None:
    """
    main.py থেকে একবার call করা হয়।
    সব auth handler একসাথে register করে।
    """
    for setup_func in _AUTH_SETUPS:
        setup_func(app)
