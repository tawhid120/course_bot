# db/database.py এ এই functions যোগ করো
# (বাকি সব আগের মতোই থাকবে)

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
    """
    Unique Membership ID তৈরি করে।
    Format: SQ-2024-XXXXX
    e.g. SQ-2024-A7K9M
    """
    year    = datetime.utcnow().year
    chars   = string.ascii_uppercase + string.digits
    suffix  = "".join(random.choices(chars, k=5))
    return f"SQ-{year}-{suffix}"


async def get_unique_membership_id() -> str:
    """
    DB তে already exist করে না এমন unique ID তৈরি করে।
    """
    db = get_db()
    while True:
        mid = generate_membership_id()
        exists = await db.orders.find_one(
            {"membership_id": mid}
        )
        if not exists:
            return mid


# ════════════════════════════════════════════════════════════
#  PAYMENT PROOF OPERATIONS
# ════════════════════════════════════════════════════════════

async def save_payment_proof(
    proof_data: Dict[str, Any]
) -> str:
    """
    Payment proof document save করে।
    Returns inserted _id as string.

    Fields:
      user_id, user_name, username,
      course_id, course_name,
      amount, currency,
      method,           (bkash/nagad/crypto)
      phone_number,     (optional — user দেবে)
      proof_file_id,    (screenshot file_id)
      proof_caption,    (user এর note)
      status,           (pending/approved/rejected)
      created_at
    """
    db = get_db()
    proof_data.setdefault("created_at", datetime.utcnow())
    proof_data.setdefault("status",     "pending")
    proof_data.setdefault("phone_number", None)
    proof_data.setdefault("proof_caption", None)
    result = await db.payment_proofs.insert_one(proof_data)
    return str(result.inserted_id)


async def get_proof_by_id(
    proof_id: str,
) -> Optional[Dict[str, Any]]:
    from bson import ObjectId
    db = get_db()
    try:
        return await db.payment_proofs.find_one(
            {"_id": ObjectId(proof_id)}
        )
    except Exception:
        return None


async def get_pending_proofs() -> List[Dict[str, Any]]:
    db = get_db()
    return await db.payment_proofs.find(
        {"status": "pending"}
    ).sort("created_at", 1).to_list(length=None)


async def update_proof_status(
    proof_id: str,
    status: str,
) -> bool:
    from bson import ObjectId
    db = get_db()
    try:
        result = await db.payment_proofs.update_one(
            {"_id": ObjectId(proof_id)},
            {
                "$set": {
                    "status":     status,
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0
    except Exception:
        return False


async def get_user_proofs(
    user_id: int,
) -> List[Dict[str, Any]]:
    db = get_db()
    return await db.payment_proofs.find(
        {"user_id": user_id}
    ).sort("created_at", -1).to_list(length=None)


# ════════════════════════════════════════════════════════════
#  বাকি সব আগের functions (add_course, get_brands, etc.)
#  সেগুলো আগের মতোই রাখো — এখানে শুধু নতুন functions
# ════════════════════════════════════════════════════════════

async def init_db() -> None:
    db = get_db()

    await db.courses.create_index("brand")
    await db.courses.create_index("is_active")
    await db.courses.create_index(
        [("brand", 1), ("batch", 1)]
    )
    await db.courses.create_index(
        [("brand", 1), ("batch", 1), ("category", 1)]
    )
    await db.courses.create_index(
        [
            ("brand", 1),
            ("batch", 1),
            ("category", 1),
            ("subject", 1),
        ]
    )
    await db.courses.create_index("group_id")
    await db.users.create_index("user_id", unique=True)
    await db.orders.create_index("user_id")
    await db.orders.create_index("status")
    await db.orders.create_index("course_id")
    await db.orders.create_index("membership_id")    # ← নতুন
    await db.orders.create_index("created_at")

    # ── Payment Proofs indexes ── নতুন collection
    await db.payment_proofs.create_index("user_id")
    await db.payment_proofs.create_index("status")
    await db.payment_proofs.create_index("created_at")

    from utils import LOGGER
    LOGGER.info("✅ Database indexes initialized.")


async def add_course(data: Dict[str, Any]) -> str:
    db = get_db()
    data.setdefault("created_at",    datetime.utcnow())
    data.setdefault("is_active",     True)
    data.setdefault("file_id",       None)
    data.setdefault("group_id",      None)
    data.setdefault("group_username", None)
    data.setdefault("group_checked", False)
    result = await db.courses.insert_one(data)
    return str(result.inserted_id)


async def get_brands() -> List[str]:
    db = get_db()
    return await db.courses.distinct(
        "brand", {"is_active": True}
    )


async def get_batches(brand: str) -> List[str]:
    db = get_db()
    return await db.courses.distinct(
        "batch", {"brand": brand, "is_active": True}
    )


async def get_categories(
    brand: str, batch: str
) -> List[str]:
    db = get_db()
    return await db.courses.distinct(
        "category",
        {"brand": brand, "batch": batch, "is_active": True},
    )


async def get_subjects(
    brand: str, batch: str, category: str
) -> List[str]:
    db = get_db()
    return await db.courses.distinct(
        "subject",
        {
            "brand":     brand,
            "batch":     batch,
            "category":  category,
            "is_active": True,
        },
    )


async def get_courses(
    brand: str, batch: str, category: str, subject: str
) -> List[Dict[str, Any]]:
    db = get_db()
    cursor = db.courses.find(
        {
            "brand":     brand,
            "batch":     batch,
            "category":  category,
            "subject":   subject,
            "is_active": True,
        }
    )
    return await cursor.to_list(length=None)


async def get_course_by_id(
    course_id: str,
) -> Optional[Dict[str, Any]]:
    from bson import ObjectId
    db = get_db()
    try:
        return await db.courses.find_one(
            {"_id": ObjectId(course_id)}
        )
    except Exception:
        return None


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


async def update_course_group_verified(
    course_id: str, verified: bool
) -> bool:
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


async def upsert_user(
    user_id: int, data: Dict[str, Any]
) -> None:
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


async def get_user(
    user_id: int,
) -> Optional[Dict[str, Any]]:
    db = get_db()
    return await db.users.find_one({"user_id": user_id})


async def get_all_users() -> List[Dict[str, Any]]:
    db = get_db()
    return await db.users.find({}).to_list(length=None)


async def get_total_users() -> int:
    db = get_db()
    return await db.users.count_documents({})


async def create_order(
    order_data: Dict[str, Any],
) -> str:
    db = get_db()
    order_data.setdefault("created_at",   datetime.utcnow())
    order_data.setdefault("status",       "pending")
    order_data.setdefault("method",       "manual")
    order_data.setdefault("invite_link",  None)
    order_data.setdefault("tx_id",        None)
    order_data.setdefault("membership_id", None)   # ← নতুন
    order_data.setdefault("phone_number",  None)   # ← নতুন
    result = await db.orders.insert_one(order_data)
    return str(result.inserted_id)


async def get_order_by_id(
    order_id: str,
) -> Optional[Dict[str, Any]]:
    from bson import ObjectId
    db = get_db()
    try:
        return await db.orders.find_one(
            {"_id": ObjectId(order_id)}
        )
    except Exception:
        return None


async def get_orders_by_user(
    user_id: int,
) -> List[Dict[str, Any]]:
    db = get_db()
    return await db.orders.find(
        {"user_id": user_id}
    ).sort("created_at", -1).to_list(length=None)


async def get_all_pending_orders() -> List[Dict[str, Any]]:
    db = get_db()
    return await db.orders.find(
        {"status": "pending"}
    ).sort("created_at", 1).to_list(length=None)


async def update_order_status(
    order_id: str, status: str
) -> bool:
    from bson import ObjectId
    db = get_db()
    try:
        result = await db.orders.update_one(
            {"_id": ObjectId(order_id)},
            {
                "$set": {
                    "status":     status,
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0
    except Exception:
        return False


async def update_order_membership(
    order_id: str,
    membership_id: str,
) -> bool:
    """Order approve হলে Membership ID assign করো।"""
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


async def update_order_invite_link(
    order_id: str, invite_link: str
) -> bool:
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


async def get_orders_by_course(
    course_id: str,
) -> List[Dict[str, Any]]:
    db = get_db()
    return await db.orders.find(
        {"course_id": course_id}
    ).to_list(length=None)


async def check_user_owns_course(
    user_id: int, course_id: str
) -> bool:
    db = get_db()
    order = await db.orders.find_one(
        {
            "user_id":   user_id,
            "course_id": course_id,
            "status":    "approved",
        }
    )
    return order is not None


async def get_full_stats() -> Dict[str, Any]:
    db = get_db()
    total_users     = await db.users.count_documents({})
    total_courses   = await db.courses.count_documents({})
    active_courses  = await db.courses.count_documents(
        {"is_active": True}
    )
    courses_w_grp   = await db.courses.count_documents(
        {"group_id": {"$ne": None}, "is_active": True}
    )
    total_orders    = await db.orders.count_documents({})
    pending_orders  = await db.orders.count_documents(
        {"status": "pending"}
    )
    approved_orders = await db.orders.count_documents(
        {"status": "approved"}
    )
    rejected_orders = await db.orders.count_documents(
        {"status": "rejected"}
    )
    pending_proofs  = await db.payment_proofs.count_documents(
        {"status": "pending"}
    )

    return {
        "total_users":     total_users,
        "total_courses":   total_courses,
        "active_courses":  active_courses,
        "courses_w_group": courses_w_grp,
        "total_orders":    total_orders,
        "pending_orders":  pending_orders,
        "approved_orders": approved_orders,
        "rejected_orders": rejected_orders,
        "pending_proofs":  pending_proofs,    # ← নতুন
    }
