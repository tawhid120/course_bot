# plugins/__init__.py
# Copyright @YourChannel

from pyrogram import Client

from .start       import setup as setup_start
from .admin_panel import setup as setup_admin
from .course_flow import setup as setup_course_flow
from .payment     import setup as setup_payment

# ════════════════════════════════════════════════════════════
# ▼▼▼ নতুন plugin যোগ করলে এখানে দুই লাইন দাও ▼▼▼
# ════════════════════════════════════════════════════════════

_PLUGIN_SETUPS = [
    setup_payment,      # ← payment FIRST (buy: callback override)
    setup_start,
    setup_admin,
    setup_course_flow,
    # setup_new_plugin,
]

# ════════════════════════════════════════════════════════════


def setup_plugins_handlers(app: Client) -> None:
    """
    main.py থেকে একবার call হয়।
    সব plugin handler একসাথে register করে।
    """
    for setup_func in _PLUGIN_SETUPS:
        setup_func(app)
