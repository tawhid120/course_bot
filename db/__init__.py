# db/__init__.py
# Copyright @YourChannel

from .database import get_db, init_db

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
    set_course_group,
    update_course_group_verified,
    get_courses_with_group,
)

# User operations
from .database import (
    upsert_user,
    get_user,
    get_all_users,
    get_total_users,
)

# Order operations
from .database import (
    create_order,
    get_order_by_id,
    get_orders_by_user,
    get_all_pending_orders,
    update_order_status,
    update_order_membership,
    update_order_invite_link,
    get_orders_by_course,
    check_user_owns_course,
    get_full_stats,
)

# Payment Proof operations
from .database import (
    save_payment_proof,
    get_proof_by_id,
    get_pending_proofs,
    update_proof_status,
    get_user_proofs,
    get_pending_proof_for_course,
)

# Membership
from .database import (
    get_unique_membership_id,
    generate_membership_id,
)
