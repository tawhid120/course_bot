# db/__init__.py
# Copyright @YourChannel
# Channel t.me/YourChannel
# ─────────────────────────────────────────────────────────────
# নতুন db ফাইল যোগ করার নিয়ম:
#
#   ধরো নতুন ফাইল: db/analytics.py
#   সেই ফাইলে:     async def log_event(...): ...
#
#   এখানে যোগ করো:
#       from .analytics import log_event, get_stats
#
#   main.py ছোঁয়ার দরকার নেই।
# ─────────────────────────────────────────────────────────────

# ── Core DB client ────────────────────────────────────────────
from .database import get_db

# ── DB init (main.py এ asyncio.run করে call হয়) ─────────────
from .database import init_db

# ── Course operations ─────────────────────────────────────────
from .database import (
    add_course,
    get_brands,
    get_batches,
    get_categories,
    get_subjects,
    get_courses,
    get_course_by_id,
    deactivate_course,
    get_all_courses_admin,
)

# ── User operations ───────────────────────────────────────────
from .database import (
    upsert_user,
    get_user,
    get_all_users,
)

# ── Order operations ──────────────────────────────────────────
from .database import (
    create_order,
    get_orders_by_user,
    get_all_pending_orders,
    update_order_status,
)

# ════════════════════════════════════════════════════════════
# ▼▼▼ নতুন db ফাইল যোগ করলে শুধু এখানে import দাও ▼▼▼
# ════════════════════════════════════════════════════════════

# from .analytics import log_event, get_daily_stats
# from .cache     import get_cached, set_cached

# ════════════════════════════════════════════════════════════
