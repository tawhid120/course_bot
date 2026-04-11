# db/database.py
# Copyright @YourChannel
# ─────────────────────────────────────────────────────────────
# init_db() → main.py startup এ একবার call হয়
# get_db()  → সব জায়গায় collection access এর জন্য
# ─────────────────────────────────────────────────────────────

from datetime import datetime
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient

from config import DATABASE_NAME, MONGO_URI

# ── Singleton client ──────────────────────────────────────────
_client: Optional[AsyncIOMotorClient] = None


def _get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URI)
    return _client


def get_db():
    return _get_client()[DATABASE_NAME]


async def init_db() -> None:
    """
    Startup এ একবার call হয়।
    Index তৈরি করে, connection test করে।
    নতুন collection এর index এখানে যোগ করো।
    """
    db = get_db()

    # ── courses indexes ───────────────────────────────────────
    await db.courses.create_index("brand")
    await db.courses.create_index("is_active")
    await db.courses.create_index([("brand", 1), ("batch", 1)])
    await db.courses.create_index(
        [("brand", 1), ("batch", 1), ("category", 1), ("subject", 1)]
    )

    # ── users indexes ─────────────────────────────────────────
    await db.users.create_index("user_id", unique=True)

    # ── orders indexes ────────────────────────────────────────
    await db.orders.create_index("user_id")
    await db.orders.create_index("status")
    await db.orders.create_index("created_at")

    from utils import LOGGER
    LOGGER.info("✅ Database indexes initialized.")


# ════════════════════════════════════════════════════════════
#  COURSE OPERATIONS
# ════════════════════════════════════════════════════════════

async def add_course(data: Dict[str, Any]) -> str:
    db = get_db()
    data.setdefault("created_at", datetime.utcnow())
    data.setdefault("is_active", True)
    data.setdefault("file_id", None)
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
        "category",
        {"brand": brand, "batch": batch, "is_active": True},
    )


async def get_subjects(brand: str, batch: str, category: str) -> List[str]:
    db = get_db()
    return await db.courses.distinct(
        "subject",
        {
            "brand": brand,
            "batch": batch,
            "category": category,
            "is_active": True,
        },
    )


async def get_courses(
    brand: str, batch: str, category: str, subject: str
) -> List[Dict[str, Any]]:
    db = get_db()
    cursor = db.courses.find(
        {
            "brand": brand,
            "batch": batch,
            "category": category,
            "subject": subject,
            "is_active": True,
        }
    )
    return await cursor.to_list(length=None)


async def get_course_by_id(course_id: str) -> Optional[Dict[str, Any]]:
    from bson import ObjectId
    db = get_db()
    return await db.courses.find_one({"_id": ObjectId(course_id)})


async def deactivate_course(course_id: str) -> bool:
    from bson import ObjectId
    db = get_db()
    result = await db.courses.update_one(
        {"_id": ObjectId(course_id)},
        {"$set": {"is_active": False}},
    )
    return result.modified_count > 0


async def get_all_courses_admin() -> List[Dict[str, Any]]:
    db = get_db()
    return await db.courses.find({}).to_list(length=None)


# ════════════════════════════════════════════════════════════
#  USER OPERATIONS
# ════════════════════════════════════════════════════════════

async def upsert_user(user_id: int, data: Dict[str, Any]) -> None:
    db = get_db()
    await db.users.update_one(
        {"user_id": user_id},
        {
            "$set": data,
            "$setOnInsert": {"joined_at": datetime.utcnow()},
        },
        upsert=True,
    )


async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    db = get_db()
    return await db.users.find_one({"user_id": user_id})


async def get_all_users() -> List[Dict[str, Any]]:
    db = get_db()
    return await db.users.find({}).to_list(length=None)


# ════════════════════════════════════════════════════════════
#  ORDER OPERATIONS
# ════════════════════════════════════════════════════════════

async def create_order(order_data: Dict[str, Any]) -> str:
    db = get_db()
    order_data.setdefault("created_at", datetime.utcnow())
    order_data.setdefault("status", "pending")
    result = await db.orders.insert_one(order_data)
    return str(result.inserted_id)


async def get_orders_by_user(user_id: int) -> List[Dict[str, Any]]:
    db = get_db()
    return await db.orders.find({"user_id": user_id}).to_list(length=None)


async def get_all_pending_orders() -> List[Dict[str, Any]]:
    db = get_db()
    return await db.orders.find({"status": "pending"}).to_list(length=None)


async def update_order_status(order_id: str, status: str) -> bool:
    from bson import ObjectId
    db = get_db()
    result = await db.orders.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": status}},
    )
    return result.modified_count > 0
