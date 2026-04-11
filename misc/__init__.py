# misc/__init__.py
# Copyright @YourChannel
# Channel t.me/YourChannel
# ─────────────────────────────────────────────────────────────
# নতুন misc ফাইল যোগ করার নিয়ম:
#
#   ধরো নতুন ফাইল: misc/notifications.py
#   সেই ফাইলে:     def setup(app): ...
#
#   এখানে যোগ করো:
#       from .notifications import setup as setup_notifications
#   এবং _MISC_SETUPS list এ:
#       setup_notifications,
#
#   main.py ছোঁয়ার দরকার নেই।
# ─────────────────────────────────────────────────────────────

from pyrogram import Client

# ── Callback query handler ── main.py সরাসরি use করে ────────
from .callback import handle_callback_query

# ── Keyboard functions ── সরাসরি export (অন্যরা import করে) ─
from .keyboards import (
    BUTTON_COMMAND_MAP,
    main_reply_keyboard,
    main_menu_inline,
    brands_inline,
    batches_inline,
    categories_inline,
    subjects_inline,
    courses_inline,
    course_detail_inline,
    payment_inline,
    admin_panel_inline,
    admin_cancel_inline,
    admin_skip_inline,
    admin_course_list_inline,
    admin_confirm_remove_inline,
    admin_order_actions_inline,
    admin_back_panel_inline,
    my_orders_inline,
)

# ── States ── সরাসরি export ───────────────────────────────────
from .states import (
    States,
    set_state,
    get_state,
    get_data,
    update_data,
    clear_state,
)

# ── Misc handler setup functions ─────────────────────────────
# button_router আলাদাভাবে main.py তে setup হয় (circular import এড়াতে)
# তাই এখানে নেই — এটা ইচ্ছাকৃত।

# ════════════════════════════════════════════════════════════
# ▼▼▼ নতুন misc ফাইল যোগ করলে শুধু এই list এ এক লাইন ▼▼▼
# ════════════════════════════════════════════════════════════

_MISC_SETUPS = [
    # setup_notifications,   ← নতুন misc handler এখানে
    # setup_analytics,
]

# ════════════════════════════════════════════════════════════


def setup_misc_handlers(app: Client) -> None:
    """
    main.py থেকে একবার call করা হয়।
    সব misc handler একসাথে register করে।
    """
    for setup_func in _MISC_SETUPS:
        setup_func(app)
