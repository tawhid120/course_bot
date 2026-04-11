# db/database.py
"""
Central database layer.
Collections:
  - courses   : all course documents
  - users     : registered users
  - orders    : purchase orders / payment records

Course document schema:
{
    "_id"        : ObjectId,
    "brand"      : str,          # Level 1
    "batch"      : str,          # Level 2
    "category"   : str,          # Level 3
    "subject"    : str,          # Level 4
    "name"       : str,          # Level 5  (course name)
    "description": str,
    "price"      : float,
    "currency"   : str,          # e.g. "INR"
    "file_id"    : str | None,   # Telegram file_id for preview
    "created_at" : datetime,
    "is_active"  : bool,
}
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient

from config import DATABASE_NAME, MONGO_URI

# ─── Singleton Client ────────────────────────────────────────────────────────
_client: Optional[AsyncIOMotorClient] = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URI)
    return _client


def get_db():
    return get_client()[DATABASE_NAME]


# ════════════════════════════════════════════════════════════════════════════
#  COURSE HELPERS
# ════════════════════════════════════════════════════════════════════════════

async def add_course(data: Dict[str, Any]) -> str:
    """Insert a new course document. Returns the inserted _id as string."""
    db = get_db()
    data.setdefault("created_at", datetime.utcnow())
    data.setdefault("is_active", True)
    data.setdefault("file_id", None)
    result = await db.courses.insert_one(data)
    return str(result.inserted_id)


async def get_brands() -> List[str]:
    """Return distinct active brand names (Level 1)."""
    db = get_db()
    return await db.courses.distinct("brand", {"is_active": True})


async def get_batches(brand: str) -> List[str]:
    """Return distinct active batch names for a brand (Level 2)."""
    db = get_db()
    return await db.courses.distinct(
        "batch", {"brand": brand, "is_active": True}
    )


async def get_categories(brand: str, batch: str) -> List[str]:
    """Return distinct active categories (Level 3)."""
    db = get_db()
    return await db.courses.distinct(
        "category", {"brand": brand, "batch": batch, "is_active": True}
    )


async def get_subjects(brand: str, batch: str, category: str) -> List[str]:
    """Return distinct active subjects (Level 4)."""
    db = get_db()
    return await db.courses.distinct(
        "subject",
        {"brand": brand, "batch": batch, "category": category, "is_active": True},
    )


async def get_courses(
    brand: str, batch: str, category: str, subject: str
) -> List[Dict[str, Any]]:
    """Return all active courses at Level 5."""
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
    """Fetch a single course by its string _id."""
    from bson import ObjectId

    db = get_db()
    return await db.courses.find_one({"_id": ObjectId(course_id)})


async def deactivate_course(course_id: str) -> bool:
    """Soft-delete: set is_active=False."""
    from bson import ObjectId

    db = get_db()
    result = await db.courses.update_one(
        {"_id": ObjectId(course_id)}, {"$set": {"is_active": False}}
    )
    return result.modified_count > 0


async def delete_course_hard(course_id: str) -> bool:
    """Hard delete a course document."""
    from bson import ObjectId

    db = get_db()
    result = await db.courses.delete_one({"_id": ObjectId(course_id)})
    return result.deleted_count > 0


async def get_all_courses_admin() -> List[Dict[str, Any]]:
    """Admin: return ALL courses (active + inactive)."""
    db = get_db()
    return await db.courses.find({}).to_list(length=None)


# ════════════════════════════════════════════════════════════════════════════
#  USER HELPERS
# ════════════════════════════════════════════════════════════════════════════

async def upsert_user(user_id: int, data: Dict[str, Any]) -> None:
    db = get_db()
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": data, "$setOnInsert": {"joined_at": datetime.utcnow()}},
        upsert=True,
    )


async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    db = get_db()
    return await db.users.find_one({"user_id": user_id})


async def get_all_users() -> List[Dict[str, Any]]:
    db = get_db()
    return await db.users.find({}).to_list(length=None)


# ════════════════════════════════════════════════════════════════════════════
#  ORDER HELPERS
# ════════════════════════════════════════════════════════════════════════════

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
        {"_id": ObjectId(order_id)}, {"$set": {"status": status}}
    )
    return result.modified_count > 0
