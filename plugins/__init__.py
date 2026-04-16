# plugins/__init__.py
# Copyright @YourChannel

from pyrogram import Client

from .start            import setup as setup_start
from .admin_panel      import setup as setup_admin
from .course_flow      import setup as setup_course_flow
from .payment          import setup as setup_payment
from .group_manager    import setup as setup_group_manager
from .payment_request  import setup as setup_payment_request  # ← নতুন
from .dynamic_buttons  import setup as setup_dynamic_buttons  # ← নতুন
from .user_profile     import setup as setup_user_profile     # ← নতুন

_PLUGIN_SETUPS = [
    setup_payment,            # buy: callback override — FIRST
    setup_payment_request,    # 💸 PAYMENT REQUEST flow ← নতুন
    setup_dynamic_buttons,    # Dynamic button editor ← নতুন
    setup_user_profile,       # 👤 Profile, Orders, Helpline ← নতুন
    setup_group_manager,
    setup_start,
    setup_admin,
    setup_course_flow,
]


def setup_plugins_handlers(app: Client) -> None:
    for setup_func in _PLUGIN_SETUPS:
        setup_func(app)