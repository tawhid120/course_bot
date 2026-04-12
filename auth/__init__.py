# auth/__init__.py
# Copyright @YourChannel

from pyrogram import Client

from .admin_check import (
    is_admin,
    admin_required,
    admin_callback_required,
    setup,
)

# ── Force Subscribe ────────────────────────────────────────────
from .force_sub import (
    setup_force_sub_handler,
    check_subscription,
)

# ════════════════════════════════════════════════════════════
_AUTH_SETUPS = [
    setup,
    # setup_otp,
]
# ════════════════════════════════════════════════════════════


def setup_auth_handlers(app: Client) -> None:
    for setup_func in _AUTH_SETUPS:
        setup_func(app)
