# plugins/__init__.py
# Copyright @YourChannel

from pyrogram import Client

from .start         import setup as setup_start
from .admin_panel   import setup as setup_admin
from .course_flow   import setup as setup_course_flow
from .payment       import setup as setup_payment
from .group_manager import setup as setup_group_manager  # ← নতুন

_PLUGIN_SETUPS = [
    setup_payment,        # buy: callback override — FIRST
    setup_group_manager,  # ← নতুন
    setup_start,
    setup_admin,
    setup_course_flow,
]


def setup_plugins_handlers(app: Client) -> None:
    for setup_func in _PLUGIN_SETUPS:
        setup_func(app)
