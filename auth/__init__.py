# auth/__init__.py

from pyrogram import Client

from .admin_check import (
    is_admin,
    admin_required,
    admin_callback_required,
    setup,
)

from .force_sub import (
    setup_force_sub_handler,
    check_subscription,
)

_AUTH_SETUPS = [
    setup,
    setup_force_sub_handler,  # ✅ এটা আগে missing ছিল!
]


def setup_auth_handlers(app: Client) -> None:
    for setup_func in _AUTH_SETUPS:
        setup_func(app)
