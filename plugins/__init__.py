# plugins/__init__.py
# Copyright @YourChannel
# Channel t.me/YourChannel
# ─────────────────────────────────────────────────────────────
# নতুন plugin যোগ করার নিয়ম:
#
#   ধরো নতুন ফাইল:  plugins/new_feature.py
#   সেই ফাইলে আছে: def setup(app): ...
#
#   তাহলে এখানে শুধু এই দুই লাইন যোগ করো:
#
#       from .new_feature import setup as setup_new_feature
#       (setup_new_feature আপনাআপনি setup_plugins_handlers এ call হবে)
#
#   অথবা যদি আলাদা নাম হয়:
#       from .new_feature import my_setup_func
#   এবং নিচের _PLUGIN_SETUPS list এ যোগ করো:
#       setup_new_feature,
#
#   main.py ছোঁয়ার দরকার নেই।
# ─────────────────────────────────────────────────────────────

from pyrogram import Client

# ── Plugin setup functions import ────────────────────────────
from .start       import setup as setup_start
from .admin_panel import setup as setup_admin
from .course_flow import setup as setup_course_flow

# ════════════════════════════════════════════════════════════
# ▼▼▼ নতুন plugin যোগ করলে শুধু এই list এ এক লাইন দাও ▼▼▼
# ════════════════════════════════════════════════════════════

_PLUGIN_SETUPS = [
    setup_start,
    setup_admin,
    setup_course_flow,
    # setup_new_feature,   ← নতুন plugin এখানে
]

# ════════════════════════════════════════════════════════════


def setup_plugins_handlers(app: Client) -> None:
    """
    main.py থেকে একবার call করা হয়।
    সব plugin handler একসাথে register করে।
    """
    for setup_func in _PLUGIN_SETUPS:
        setup_func(app)
