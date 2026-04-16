# db/database.py
# Copyright @YourChannel

import random
import string
from datetime import datetime
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from config import DATABASE_NAME, MONGO_URI

_client: Optional[AsyncIOMotorClient] = None


def _get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URI)
    return _client


def get_db():
    return _get_client()[DATABASE_NAME]


# ════════════════════════════════════════════════════════════
#  MEMBERSHIP ID GENERATOR
# ════════════════════════════════════════════════════════════

def generate_membership_id() -> str:
    year   = datetime.utcnow().year
    chars  = string.ascii_uppercase + string.digits
    suffix = "".join(random.choices(chars, k=5))
    return f"FCBD-{year}-{suffix}"


async def get_unique_membership_id() -> str:
    db = get_db()
    while True:
        mid = generate_membership_id()
        exists = await db.orders.find_one({"membership_id": mid})
        if not exists:
            return mid


# ════════════════════════════════════════════════════════════
#  DB INIT
# ════════════════════════════════════════════════════════════

async def init_db() -> None:
    db = get_db()

    await db.courses.create_index("brand")
    await db.courses.create_index("is_active")
    await db.courses.create_index([("brand", 1), ("batch", 1)])
    await db.courses.create_index([("brand", 1), ("batch", 1), ("category", 1)])
    await db.courses.create_index(
        [("brand", 1), ("batch", 1), ("category", 1), ("subject", 1)]
    )
    await db.courses.create_index("group_id")
    await db.courses.create_index("course_code", sparse=True)

    await db.users.create_index("user_id", unique=True)

    await db.orders.create_index("user_id")
    await db.orders.create_index("status")
    await db.orders.create_index("course_id")
    await db.orders.create_index("membership_id")
    await db.orders.create_index("created_at")

    await db.payment_proofs.create_index("user_id")
    await db.payment_proofs.create_index("status")
    await db.payment_proofs.create_index("created_at")
    await db.payment_proofs.create_index([("user_id", 1), ("course_id", 1)])

    # Dynamic buttons collection
    await db.dynamic_buttons.create_index("button_id", unique=True)
    await db.dynamic_buttons.create_index("position")

    # Settings collection (helpline, etc.)
    await db.settings.create_index("key", unique=True)

    # Banned users
    await db.banned_users.create_index("user_id", unique=True)

    from utils import LOGGER
    LOGGER.info("✅ Database indexes initialized.")


# ════════════════════════════════════════════════════════════
#  COURSE OPERATIONS
# ════════════════════════════════════════════════════════════

async def add_course(data: Dict[str, Any]) -> str:
    db = get_db()
    data.setdefault("created_at",     datetime.utcnow())
    data.setdefault("is_active",      True)
    data.setdefault("file_id",        None)
    data.setdefault("group_id",       None)
    data.setdefault("group_username", None)
    data.setdefault("group_checked",  False)
    data.setdefault("course_code",    None)
    result = await db.courses.insert_one(data)
    return str(result.inserted_id)


async def get_brands() -> List[str]:
    db = get_db()
    return await db.courses.distinct("brand", {"is_active": True})


async def get_batches(brand: str) -> List[str]:
    db = get_db()
    return await db.courses.distinct(
        "batch", {"brand": brand, "is_active": True}
    )


async def get_categories(brand: str, batch: str) -> List[str]:
    db = get_db()
    return await db.courses.distinct(
        "category", {"brand": brand, "batch": batch, "is_active": True}
    )


async def get_subjects(brand: str, batch: str, category: str) -> List[str]:
    db = get_db()
    return await db.courses.distinct(
        "subject",
        {"brand": brand, "batch": batch, "category": category, "is_active": True},
    )


async def get_courses(
    brand: str, batch: str, category: str, subject: str
) -> List[Dict[str, Any]]:
    db = get_db()
    cursor = db.courses.find(
        {
            "brand":    brand,
            "batch":    batch,
            "category": category,
            "subject":  subject,
            "is_active": True,
        }
    )
    return await cursor.to_list(length=None)


async def get_course_by_id(course_id: str) -> Optional[Dict[str, Any]]:
    from bson import ObjectId
    db = get_db()
    try:
        return await db.courses.find_one({"_id": ObjectId(course_id)})
    except Exception:
        return None


async def get_course_by_code(course_code: str) -> Optional[Dict[str, Any]]:
    """Course Code দিয়ে course খোঁজো।"""
    db = get_db()
    return await db.courses.find_one(
        {"course_code": course_code.upper().strip(), "is_active": True}
    )


async def deactivate_course(course_id: str) -> bool:
    from bson import ObjectId
    db = get_db()
    try:
        result = await db.courses.update_one(
            {"_id": ObjectId(course_id)},
            {"$set": {"is_active": False}},
        )
        return result.modified_count > 0
    except Exception:
        return False


async def get_all_courses_admin() -> List[Dict[str, Any]]:
    db = get_db()
    return await db.courses.find({}).to_list(length=None)


async def set_course_group(
    course_id: str,
    group_id: int,
    group_username: Optional[str] = None,
    group_checked: bool = False,
) -> bool:
    from bson import ObjectId
    db = get_db()
    try:
        result = await db.courses.update_one(
            {"_id": ObjectId(course_id)},
            {
                "$set": {
                    "group_id":         group_id,
                    "group_username":   group_username,
                    "group_checked":    group_checked,
                    "group_updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0
    except Exception:
        return False


async def set_course_code(course_id: str, course_code: str) -> bool:
    """Course এ একটা unique Course Code সেট করো।"""
    from bson import ObjectId
    db = get_db()
    try:
        result = await db.courses.update_one(
            {"_id": ObjectId(course_id)},
            {"$set": {"course_code": course_code.upper().strip()}},
        )
        return result.modified_count > 0
    except Exception:
        return False


async def update_course_group_verified(course_id: str, verified: bool) -> bool:
    from bson import ObjectId
    db = get_db()
    try:
        result = await db.courses.update_one(
            {"_id": ObjectId(course_id)},
            {"$set": {"group_checked": verified}},
        )
        return result.modified_count > 0
    except Exception:
        return False


async def get_courses_with_group() -> List[Dict[str, Any]]:
    db = get_db()
    return await db.courses.find(
        {"group_id": {"$ne": None}, "is_active": True}
    ).to_list(length=None)


# ════════════════════════════════════════════════════════════
#  USER OPERATIONS
# ════════════════════════════════════════════════════════════

async def upsert_user(user_id: int, data: Dict[str, Any]) -> None:
    db = get_db()
    await db.users.update_one(
        {"user_id": user_id},
        {
            "$set": data,
            "$setOnInsert": {
                "joined_at":       datetime.utcnow(),
                "total_purchases": 0,
            },
        },
        upsert=True,
    )


async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    db = get_db()
    return await db.users.find_one({"user_id": user_id})


async def get_all_users() -> List[Dict[str, Any]]:
    db = get_db()
    return await db.users.find({}).to_list(length=None)


async def get_total_users() -> int:
    db = get_db()
    return await db.users.count_documents({})


# ════════════════════════════════════════════════════════════
#  BAN SYSTEM
# ════════════════════════════════════════════════════════════

async def ban_user(user_id: int, reason: str = "No reason given") -> bool:
    db = get_db()
    try:
        await db.banned_users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id":   user_id,
                    "reason":    reason,
                    "banned_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )
        return True
    except Exception:
        return False


async def unban_user(user_id: int) -> bool:
    db = get_db()
    try:
        result = await db.banned_users.delete_one({"user_id": user_id})
        return result.deleted_count > 0
    except Exception:
        return False


async def is_banned(user_id: int) -> bool:
    db = get_db()
    doc = await db.banned_users.find_one({"user_id": user_id})
    return doc is not None


async def get_all_banned() -> List[Dict[str, Any]]:
    db = get_db()
    return await db.banned_users.find({}).to_list(length=None)


# ════════════════════════════════════════════════════════════
#  ORDER OPERATIONS
# ════════════════════════════════════════════════════════════

async def create_order(order_data: Dict[str, Any]) -> str:
    db = get_db()
    order_data.setdefault("created_at",    datetime.utcnow())
    order_data.setdefault("status",        "pending")
    order_data.setdefault("method",        "manual")
    order_data.setdefault("invite_link",   None)
    order_data.setdefault("tx_id",         None)
    order_data.setdefault("membership_id", None)
    order_data.setdefault("phone_number",  None)
    result = await db.orders.insert_one(order_data)
    return str(result.inserted_id)


async def get_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
    from bson import ObjectId
    db = get_db()
    try:
        return await db.orders.find_one({"_id": ObjectId(order_id)})
    except Exception:
        return None


async def get_orders_by_user(user_id: int) -> List[Dict[str, Any]]:
    db = get_db()
    return (
        await db.orders.find({"user_id": user_id})
        .sort("created_at", -1)
        .to_list(length=None)
    )


async def get_all_pending_orders() -> List[Dict[str, Any]]:
    db = get_db()
    return (
        await db.orders.find({"status": "pending"})
        .sort("created_at", 1)
        .to_list(length=None)
    )


async def update_order_status(order_id: str, status: str) -> bool:
    from bson import ObjectId
    db = get_db()
    try:
        result = await db.orders.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}},
        )
        return result.modified_count > 0
    except Exception:
        return False


async def update_order_membership(order_id: str, membership_id: str) -> bool:
    from bson import ObjectId
    db = get_db()
    try:
        result = await db.orders.update_one(
            {"_id": ObjectId(order_id)},
            {
                "$set": {
                    "membership_id": membership_id,
                    "approved_at":   datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0
    except Exception:
        return False


async def update_order_invite_link(order_id: str, invite_link: str) -> bool:
    from bson import ObjectId
    db = get_db()
    try:
        result = await db.orders.update_one(
            {"_id": ObjectId(order_id)},
            {
                "$set": {
                    "invite_link":  invite_link,
                    "link_sent_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0
    except Exception:
        return False


async def get_orders_by_course(course_id: str) -> List[Dict[str, Any]]:
    db = get_db()
    return await db.orders.find({"course_id": course_id}).to_list(length=None)


async def check_user_owns_course(user_id: int, course_id: str) -> bool:
    db = get_db()
    order = await db.orders.find_one(
        {"user_id": user_id, "course_id": course_id, "status": "approved"}
    )
    return order is not None


async def get_full_stats() -> Dict[str, Any]:
    db = get_db()
    total_users     = await db.users.count_documents({})
    total_courses   = await db.courses.count_documents({})
    active_courses  = await db.courses.count_documents({"is_active": True})
    courses_w_grp   = await db.courses.count_documents(
        {"group_id": {"$ne": None}, "is_active": True}
    )
    total_orders    = await db.orders.count_documents({})
    pending_orders  = await db.orders.count_documents({"status": "pending"})
    approved_orders = await db.orders.count_documents({"status": "approved"})
    rejected_orders = await db.orders.count_documents({"status": "rejected"})
    pending_proofs  = await db.payment_proofs.count_documents({"status": "pending"})
    banned_count    = await db.banned_users.count_documents({})

    return {
        "total_users":     total_users,
        "total_courses":   total_courses,
        "active_courses":  active_courses,
        "courses_w_group": courses_w_grp,
        "total_orders":    total_orders,
        "pending_orders":  pending_orders,
        "approved_orders": approved_orders,
        "rejected_orders": rejected_orders,
        "pending_proofs":  pending_proofs,
        "banned_users":    banned_count,
    }


# ════════════════════════════════════════════════════════════
#  PAYMENT PROOF OPERATIONS
# ════════════════════════════════════════════════════════════

async def save_payment_proof(proof_data: Dict[str, Any]) -> str:
    db = get_db()
    proof_data.setdefault("created_at",    datetime.utcnow())
    proof_data.setdefault("status",        "pending")
    proof_data.setdefault("phone_number",  None)
    proof_data.setdefault("proof_caption", None)
    result = await db.payment_proofs.insert_one(proof_data)
    return str(result.inserted_id)


async def get_proof_by_id(proof_id: str) -> Optional[Dict[str, Any]]:
    from bson import ObjectId
    db = get_db()
    try:
        return await db.payment_proofs.find_one({"_id": ObjectId(proof_id)})
    except Exception:
        return None


async def get_pending_proofs() -> List[Dict[str, Any]]:
    db = get_db()
    return (
        await db.payment_proofs.find({"status": "pending"})
        .sort("created_at", 1)
        .to_list(length=None)
    )


async def update_proof_status(proof_id: str, status: str) -> bool:
    from bson import ObjectId
    db = get_db()
    try:
        result = await db.payment_proofs.update_one(
            {"_id": ObjectId(proof_id)},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}},
        )
        return result.modified_count > 0
    except Exception:
        return False


async def get_user_proofs(user_id: int) -> List[Dict[str, Any]]:
    db = get_db()
    try:
        return (
            await db.payment_proofs.find({"user_id": user_id})
            .sort("created_at", -1)
            .to_list(length=None)
        )
    except Exception:
        return []


async def get_pending_proof_for_course(
    user_id: int, course_id: str
) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        return await db.payment_proofs.find_one(
            {"user_id": user_id, "course_id": course_id, "status": "pending"}
        )
    except Exception:
        return None


# ════════════════════════════════════════════════════════════
#  DYNAMIC BUTTONS
# ════════════════════════════════════════════════════════════

async def get_dynamic_buttons() -> List[Dict[str, Any]]:
    """সব dynamic buttons ক্রম অনুযায়ী আনো।"""
    db = get_db()
    return (
        await db.dynamic_buttons.find({})
        .sort("position", 1)
        .to_list(length=None)
    )


async def add_dynamic_button(
    button_id: str,
    label: str,
    content: str,
    position: int,
) -> bool:
    """নতুন dynamic button যোগ করো।"""
    db = get_db()
    try:
        await db.dynamic_buttons.insert_one(
            {
                "button_id":  button_id,
                "label":      label,
                "content":    content,
                "position":   position,
                "created_at": datetime.utcnow(),
            }
        )
        return True
    except Exception:
        return False


async def update_dynamic_button(
    button_id: str, label: str = None, content: str = None
) -> bool:
    """Dynamic button আপডেট করো।"""
    db = get_db()
    update_fields: Dict[str, Any] = {"updated_at": datetime.utcnow()}
    if label   is not None:
        update_fields["label"]   = label
    if content is not None:
        update_fields["content"] = content
    try:
        result = await db.dynamic_buttons.update_one(
            {"button_id": button_id}, {"$set": update_fields}
        )
        return result.modified_count > 0
    except Exception:
        return False


async def delete_dynamic_button(button_id: str) -> bool:
    """Dynamic button মুছে ফেলো।"""
    db = get_db()
    try:
        result = await db.dynamic_buttons.delete_one({"button_id": button_id})
        return result.deleted_count > 0
    except Exception:
        return False


async def get_dynamic_button(button_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    return await db.dynamic_buttons.find_one({"button_id": button_id})


# ════════════════════════════════════════════════════════════
#  SETTINGS (Helpline, etc.)
# ════════════════════════════════════════════════════════════

async def get_setting(key: str, default: str = "") -> str:
    db = get_db()
    doc = await db.settings.find_one({"key": key})
    return doc["value"] if doc else default


async def set_setting(key: str, value: str) -> bool:
    db = get_db()
    try:
        await db.settings.update_one(
            {"key": key},
            {"$set": {"key": key, "value": value, "updated_at": datetime.utcnow()}},
            upsert=True,
        )
        return True
    except Exception:
        return False
