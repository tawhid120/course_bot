# db/__init__.py
# Copyright @YourChannel

from .database import get_db
from .database import init_db

# Course operations
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
    set_course_group,        # ← নতুন
)

# User operations
from .database import (
    upsert_user,
    get_user,
    get_all_users,
)

# Order operations
from .database import (
    create_order,
    get_orders_by_user,
    get_all_pending_orders,
    update_order_status,
)
