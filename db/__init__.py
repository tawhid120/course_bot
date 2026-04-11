# db/__init__.py
# Copyright @YourChannel
# ─────────────────────────────────────────────────────────────
# নতুন db function যোগ করলে:
#   1. database.py তে function লিখো
#   2. এখানে import লাইন যোগ করো
#   main.py ছোঁয়ার দরকার নেই।
# ─────────────────────────────────────────────────────────────

# ── Core ──────────────────────────────────────────────────────
from .database import get_db
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
    set_course_group,
    update_course_group_verified,
    get_courses_with_group,
    search_courses,
)

# ── User operations ───────────────────────────────────────────
from .database import (
    upsert_user,
    get_user,
    get_all_users,
    get_total_users,
    update_user_purchase_count,
)

# ── Order operations ──────────────────────────────────────────
from .database import (
    create_order,
    get_order_by_id,
    get_orders_by_user,
    get_all_pending_orders,
    get_all_orders_admin,
    update_order_status,
    update_order_invite_link,
    get_orders_by_course,
    get_approved_orders_count,
    get_pending_orders_count,
    check_user_owns_course,
)

# ── Stats operations ──────────────────────────────────────────
from .database import (
    get_full_stats,
)

# ════════════════════════════════════════════════════════════
# ▼▼▼ নতুন db ফাইল/function যোগ করলে এখানে import দাও ▼▼▼
# ════════════════════════════════════════════════════════════

# from .analytics import log_event, get_daily_stats
# from .cache     import get_cached, set_cached

# ════════════════════════════════════════════════════════════
