# misc/states.py
# Copyright @YourChannel

from typing import Any, Dict, Optional

_store: Dict[int, Dict[str, Any]] = {}


class States:
    # ── User navigation ───────────────────────────────────────
    SELECT_BRAND    = "select_brand"
    SELECT_BATCH    = "select_batch"
    SELECT_CATEGORY = "select_category"
    SELECT_SUBJECT  = "select_subject"
    SELECT_COURSE   = "select_course"
    VIEW_COURSE     = "view_course"
    PAYMENT         = "payment"

    # ── Admin: Add Course (11 steps) ──────────────────────────
    ADMIN_ADD_BRAND       = "admin_add_brand"
    ADMIN_ADD_BATCH       = "admin_add_batch"
    ADMIN_ADD_CATEGORY    = "admin_add_category"
    ADMIN_ADD_SUBJECT     = "admin_add_subject"
    ADMIN_ADD_NAME        = "admin_add_name"
    ADMIN_ADD_DESC        = "admin_add_desc"
    ADMIN_ADD_PRICE       = "admin_add_price"
    ADMIN_ADD_CURRENCY    = "admin_add_currency"
    ADMIN_ADD_FILE        = "admin_add_file"
    ADMIN_ADD_GROUP       = "admin_add_group"
    ADMIN_ADD_COURSE_CODE = "admin_add_course_code"  # ← নতুন Step 11

    # ── Admin: Set group / code for existing course ───────────
    ADMIN_SET_GROUP = "admin_set_group"

    # ── Admin: Broadcast ──────────────────────────────────────
    ADMIN_BROADCAST = "admin_broadcast"

    IDLE = "idle"


def set_state(
    user_id: int,
    state: str,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    _store[user_id] = {
        "state": state,
        "data":  data if data is not None else {},
    }


def get_state(user_id: int) -> str:
    return _store.get(user_id, {}).get("state", States.IDLE)


def get_data(user_id: int) -> Dict[str, Any]:
    return _store.get(user_id, {}).get("data", {})


def update_data(user_id: int, **kwargs) -> None:
    if user_id not in _store:
        _store[user_id] = {"state": States.IDLE, "data": {}}
    _store[user_id]["data"].update(kwargs)


def clear_state(user_id: int) -> None:
    _store.pop(user_id, None)
