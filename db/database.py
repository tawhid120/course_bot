# db/database.py
# Copyright @YourChannel
# ─────────────────────────────────────────────────────────────
# MongoDB async database layer using motor.
#
# Collections:
#   courses  → সব course document
#   users    → registered users
#   orders   → purchase orders
#
# Course document schema:
# {
#     "_id"           : ObjectId,
#     "brand"         : str,
#     "batch"         : str,
#     "category"      : str,
#     "subject"       : str,
#     "name"          : str,
#     "description"   : str,
#     "price"         : float,
#     "currency"      : str,
#     "file_id"       : str | None,
#     "group_id"      : int | None,
#     "group_username": str | None,
#     "group_checked" : bool,
#     "created_at"    : datetime,
#     "is_active"     : bool,
# }
# ─────────────────────────────────────────────────────────────

from datetime import datetime
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient

from config import DATABASE_NAME, MONGO_URI

# ─────────────────────────────────────────────────────────────
#  Singleton Client
# ─────────────────────────────────────────────────────────────

_client: Optional[AsyncIOMotorClient] = None


def _get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URI)
    return _client


def get_db():
    """যেকোনো জায়গা থেকে DB instance পাওয়ার জন্য।"""
    return _get_client()[DATABASE_NAME]


# ─────────────────────────────────────────────────────────────
#  DB INIT — main.py startup এ একবার call হয়
# ─────────────────────────────────────────────────────────────

async def init_db() -> None:
    """
    Startup এ একবার call হয়।
    সব collection এর index তৈরি করে।
    নতুন collection এর index এখানে যোগ করো।
    """
    db = get_db()

    # ── courses indexes ───────────────────────────────────────
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

    # ── users indexes ─────────────────────────────────────────
    await db.users.create_index("user_id", unique=True)

    # ── orders indexes ────────────────────────────────────────
    await db.orders.create_index("user_id")
    await db.orders.create_index("status")
    await db.orders.create_index("course_id")
    await db.orders.create_index("created_at")

    from utils import LOGGER
    LOGGER.info("✅ Database indexes initialized successfully.")


# ═════════════════════════════════════════════════════════════
#  COURSE OPERATIONS
# ═════════════════════════════════════════════════════════════

async def add_course(data: Dict[str, Any]) -> str:
    """
    নতুন course insert করে।
    Returns inserted _id as string.

    Required fields in data:
      brand, batch, category, subject, name,
      description, price, currency

    Optional fields:
      file_id, group_id, group_username, group_checked
    """
    db = get_db()

    # Default values set করো
    data.setdefault("created_at",    datetime.utcnow())
    data.setdefault("is_active",     True)
    data.setdefault("file_id",       None)
    data.setdefault("group_id",      None)
    data.setdefault("group_username", None)
    data.setdefault("group_checked", False)

    result = await db.courses.insert_one(data)
    return str(result.inserted_id)


async def get_brands() -> List[str]:
    """
    সব active course এর distinct brand name list।
    User menu Level-1 এ দেখায়।
    """
    db = get_db()
    return await db.courses.distinct(
        "brand",
        {"is_active": True},
    )


async def get_batches(brand: str) -> List[str]:
    """
    একটা brand এর সব active batch list।
    User menu Level-2 এ দেখায়।
    """
    db = get_db()
    return await db.courses.distinct(
        "batch",
        {"brand": brand, "is_active": True},
    )


async def get_categories(
    brand: str, batch: str
) -> List[str]:
    """
    একটা brand+batch এর সব active category list।
    User menu Level-3 এ দেখায়।
    """
    db = get_db()
    return await db.courses.distinct(
        "category",
        {
            "brand":     brand,
            "batch":     batch,
            "is_active": True,
        },
    )


async def get_subjects(
    brand: str, batch: str, category: str
) -> List[str]:
    """
    একটা brand+batch+category এর সব active subject list।
    User menu Level-4 এ দেখায়।
    """
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
    brand: str,
    batch: str,
    category: str,
    subject: str,
) -> List[Dict[str, Any]]:
    """
    একটা brand+batch+category+subject এর
    সব active course list।
    User menu Level-5 এ দেখায়।
    """
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
    """
    _id দিয়ে একটা course fetch করে।
    course_id string হিসেবে দিতে হবে।
    """
    from bson import ObjectId
    db = get_db()
    try:
        return await db.courses.find_one(
            {"_id": ObjectId(course_id)}
        )
    except Exception:
        return None


async def deactivate_course(course_id: str) -> bool:
    """
    Course টাকে soft delete করে।
    is_active = False করে দেয়।
    User menu থেকে hide হয়ে যায়।
    Returns True যদি সফল হয়।
    """
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
    """
    Admin panel এর জন্য সব course fetch করে।
    Active এবং inactive দুটোই আসবে।
    """
    db = get_db()
    return await db.courses.find({}).to_list(length=None)


async def set_course_group(
    course_id: str,
    group_id: int,
    group_username: Optional[str] = None,
    group_checked: bool = False,
) -> bool:
    """
    Course এ private group/channel এর ID set করে।

    Args:
        course_id     : Course এর ObjectId string
        group_id      : Telegram group/channel ID (int)
        group_username: Group username (optional display)
        group_checked : Bot admin verified কিনা

    Returns True যদি সফল হয়।
    """
    from bson import ObjectId
    db = get_db()
    try:
        result = await db.courses.update_one(
            {"_id": ObjectId(course_id)},
            {
                "$set": {
                    "group_id":       group_id,
                    "group_username": group_username,
                    "group_checked":  group_checked,
                    "group_updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0
    except Exception:
        return False


async def update_course_group_verified(
    course_id: str,
    verified: bool,
) -> bool:
    """
    Course এর group_checked status update করে।
    Bot admin check এর পর call হয়।
    """
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
    """
    শুধু সেই courses যেগুলোতে group_id set আছে।
    Admin stats এর জন্য।
    """
    db = get_db()
    return await db.courses.find(
        {"group_id": {"$ne": None}, "is_active": True}
    ).to_list(length=None)


async def search_courses(query: str) -> List[Dict[str, Any]]:
    """
    Course name বা description এ text search করে।
    """
    db = get_db()
    cursor = db.courses.find(
        {
            "is_active": True,
            "$or": [
                {
                    "name": {
                        "$regex": query,
                        "$options": "i",
                    }
                },
                {
                    "description": {
                        "$regex": query,
                        "$options": "i",
                    }
                },
                {
                    "brand": {
                        "$regex": query,
                        "$options": "i",
                    }
                },
            ],
        }
    )
    return await cursor.to_list(length=None)


# ═════════════════════════════════════════════════════════════
#  USER OPERATIONS
# ═════════════════════════════════════════════════════════════

async def upsert_user(
    user_id: int,
    data: Dict[str, Any],
) -> None:
    """
    User upsert করে।
    নতুন user হলে insert, পুরনো হলে update।
    /start command এ call হয়।
    """
    db = get_db()
    await db.users.update_one(
        {"user_id": user_id},
        {
            "$set": data,
            "$setOnInsert": {
                "joined_at":        datetime.utcnow(),
                "total_purchases":  0,
            },
        },
        upsert=True,
    )


async def get_user(
    user_id: int,
) -> Optional[Dict[str, Any]]:
    """User ID দিয়ে একজন user fetch করে।"""
    db = get_db()
    return await db.users.find_one({"user_id": user_id})


async def get_all_users() -> List[Dict[str, Any]]:
    """
    সব registered user fetch করে।
    Broadcast এর সময় use হয়।
    """
    db = get_db()
    return await db.users.find({}).to_list(length=None)


async def get_total_users() -> int:
    """Total user count।"""
    db = get_db()
    return await db.users.count_documents({})


async def update_user_purchase_count(
    user_id: int,
) -> None:
    """
    User কোর্স কিনলে total_purchases বাড়ায়।
    Order approve হলে call হয়।
    """
    db = get_db()
    await db.users.update_one(
        {"user_id": user_id},
        {"$inc": {"total_purchases": 1}},
    )


# ═════════════════════════════════════════════════════════════
#  ORDER OPERATIONS
# ═════════════════════════════════════════════════════════════

async def create_order(
    order_data: Dict[str, Any],
) -> str:
    """
    নতুন order create করে।
    Returns inserted _id as string.

    Required fields:
      user_id, user_name, course_id, course_name,
      amount, currency

    Optional:
      username, method, tx_id, invite_link,
      status (default: pending)
    """
    db = get_db()
    order_data.setdefault("created_at",  datetime.utcnow())
    order_data.setdefault("status",      "pending")
    order_data.setdefault("method",      "manual")
    order_data.setdefault("invite_link", None)
    order_data.setdefault("tx_id",       None)

    result = await db.orders.insert_one(order_data)
    return str(result.inserted_id)


async def get_order_by_id(
    order_id: str,
) -> Optional[Dict[str, Any]]:
    """Order ID দিয়ে একটা order fetch করে।"""
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
    """
    একজন user এর সব order fetch করে।
    User এর 'My Orders' এ দেখায়।
    """
    db = get_db()
    return await db.orders.find(
        {"user_id": user_id}
    ).sort("created_at", -1).to_list(length=None)


async def get_all_pending_orders() -> List[Dict[str, Any]]:
    """
    সব pending order fetch করে।
    Admin panel এ দেখায়।
    """
    db = get_db()
    return await db.orders.find(
        {"status": "pending"}
    ).sort("created_at", 1).to_list(length=None)


async def get_all_orders_admin() -> List[Dict[str, Any]]:
    """
    Admin এর জন্য সব order (সব status)।
    """
    db = get_db()
    return await db.orders.find(
        {}
    ).sort("created_at", -1).to_list(length=None)


async def update_order_status(
    order_id: str,
    status: str,
) -> bool:
    """
    Order এর status update করে।
    status values: pending | approved | rejected

    Returns True যদি সফল হয়।
    """
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


async def update_order_invite_link(
    order_id: str,
    invite_link: str,
) -> bool:
    """
    Order এ One-Time Invite Link save করে।
    Link generate হওয়ার পর call হয়।
    """
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
    """
    একটা course এর সব order।
    Course remove করার আগে check করতে।
    """
    db = get_db()
    return await db.orders.find(
        {"course_id": course_id}
    ).to_list(length=None)


async def get_approved_orders_count() -> int:
    """Total approved order count। Stats এর জন্য।"""
    db = get_db()
    return await db.orders.count_documents(
        {"status": "approved"}
    )


async def get_pending_orders_count() -> int:
    """Total pending order count। Stats এর জন্য।"""
    db = get_db()
    return await db.orders.count_documents(
        {"status": "pending"}
    )


async def check_user_owns_course(
    user_id: int,
    course_id: str,
) -> bool:
    """
    User ইতিমধ্যে এই course কিনেছে কিনা check করে।
    Duplicate purchase prevent করতে।
    """
    db = get_db()
    order = await db.orders.find_one(
        {
            "user_id":   user_id,
            "course_id": course_id,
            "status":    "approved",
        }
    )
    return order is not None


# ═════════════════════════════════════════════════════════════
#  STATS OPERATIONS
# ═════════════════════════════════════════════════════════════

async def get_full_stats() -> Dict[str, Any]:
    """
    Admin stats panel এর জন্য সব statistics।
    একটা call এ সব data।
    """
    db = get_db()

    total_users    = await db.users.count_documents({})
    total_courses  = await db.courses.count_documents({})
    active_courses = await db.courses.count_documents(
        {"is_active": True}
    )
    courses_w_grp  = await db.courses.count_documents(
        {"group_id": {"$ne": None}, "is_active": True}
    )
    total_orders   = await db.orders.count_documents({})
    pending_orders = await db.orders.count_documents(
        {"status": "pending"}
    )
    approved_orders = await db.orders.count_documents(
        {"status": "approved"}
    )
    rejected_orders = await db.orders.count_documents(
        {"status": "rejected"}
    )

    return {
        "total_users":      total_users,
        "total_courses":    total_courses,
        "active_courses":   active_courses,
        "courses_w_group":  courses_w_grp,
        "total_orders":     total_orders,
        "pending_orders":   pending_orders,
        "approved_orders":  approved_orders,
        "rejected_orders":  rejected_orders,
    }
