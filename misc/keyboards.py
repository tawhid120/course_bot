# misc/keyboards.py
# Copyright @YourChannel

"""
All keyboards in one place.

Callback data conventions:
  brand:<name>
  batch:<brand>|<name>
  category:<brand>|<batch>|<name>
  subject:<brand>|<batch>|<category>|<name>
  course:<id>
  buy:<id>
  cpay:bkash:<id>  | cpay:nagad:<id>  | cpay:back:<id>
  proof:skip_phone:<id>  | proof:skip_screenshot:<id>
  proof:approve:<proof_id>  | proof:reject:<proof_id>
  back:main
  browse_courses | my_orders | help
  admin:panel | admin:add_course | admin:list_courses | ...
"""

from typing import Any, Dict, List

from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# ─── Reply Keyboard Button Labels & Command Map ───────────────────────────────

BUTTON_COMMAND_MAP: Dict[str, str] = {
    "🏠 Home":        "start",
    "📚 Courses":     "browse_courses",
    "🛒 My Orders":   "my_orders",
    "❓ Help":        "help",
    "👤 Profile":     "profile",
    "🛠 Admin Panel": "admin_panel",
}


def main_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("🏠 Home"),      KeyboardButton("📚 Courses")],
            [KeyboardButton("🛒 My Orders"), KeyboardButton("❓ Help")],
            [KeyboardButton("👤 Profile"),   KeyboardButton("🛠 Admin Panel")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


# ════════════════════════════════════════════════════════════════════════════
#  USER INLINE KEYBOARDS
# ════════════════════════════════════════════════════════════════════════════

def main_menu_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📚 Browse Courses", callback_data="browse_courses")],
            [
                InlineKeyboardButton("🛒 My Orders", callback_data="my_orders"),
                InlineKeyboardButton("❓ Help",      callback_data="help"),
            ],
        ]
    )


def brands_inline(brands: List[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"🏷 {b}", callback_data=f"brand:{b}")] for b in brands]
    rows.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back:main")])
    return InlineKeyboardMarkup(rows)


def batches_inline(brand: str, batches: List[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"📦 {b}", callback_data=f"batch:{brand}|{b}")] for b in batches]
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="browse_courses")])
    return InlineKeyboardMarkup(rows)


def categories_inline(brand: str, batch: str, categories: List[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"📂 {c}", callback_data=f"category:{brand}|{batch}|{c}")] for c in categories]
    rows.append([InlineKeyboardButton("🔙 Back", callback_data=f"brand:{brand}")])
    return InlineKeyboardMarkup(rows)


def subjects_inline(brand: str, batch: str, category: str, subjects: List[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"📖 {s}", callback_data=f"subject:{brand}|{batch}|{category}|{s}")] for s in subjects]
    rows.append([InlineKeyboardButton("🔙 Back", callback_data=f"category:{brand}|{batch}|{category}")])
    return InlineKeyboardMarkup(rows)


def courses_inline(brand, batch, category, subject, courses: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            f"🎓 {c['name']}  —  {c['currency']} {c['price']}",
            callback_data=f"course:{str(c['_id'])}",
        )]
        for c in courses
    ]
    rows.append([InlineKeyboardButton("🔙 Back", callback_data=f"subject:{brand}|{batch}|{category}|{subject}")])
    return InlineKeyboardMarkup(rows)


def course_detail_inline(course_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🛒 Buy Now",       callback_data=f"buy:{course_id}")],
            [InlineKeyboardButton("🔙 Back to Menu",  callback_data="back:main")],
        ]
    )


# ════════════════════════════════════════════════════════════════════════════
#  PAYMENT KEYBOARDS  (বিকাশ, নগদ এবং ফোন নম্বর মডিউল)
# ════════════════════════════════════════════════════════════════════════════

def payment_methods_kb(course_id: str) -> InlineKeyboardMarkup:
    """Payment method selection — শুধু bKash ও Nagad।"""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📲 bKash",  callback_data=f"cpay:bkash:{course_id}")],
            [InlineKeyboardButton("📲 Nagad",  callback_data=f"cpay:nagad:{course_id}")],
            [InlineKeyboardButton("🔙 Back",   callback_data=f"course:{course_id}")],
        ]
    )


def payment_inline(course_id: str) -> InlineKeyboardMarkup:
    """Legacy — course_flow.py এ ব্যবহার হয়।"""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ I Have Paid", callback_data=f"payment_done:{course_id}")],
            [InlineKeyboardButton("❌ Cancel",      callback_data=f"course:{course_id}")],
        ]
    )


def proof_phone_kb(course_id: str) -> InlineKeyboardMarkup:
    """Phone number input screen — Skip বাটনটি সরানো হয়েছে (Mandatory)।"""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("❌ Cancel", callback_data=f"cpay:back:{course_id}")],
        ]
    )


def proof_screenshot_kb(course_id: str) -> InlineKeyboardMarkup:
    """Screenshot input screen — এখনো Skip করা যাবে।"""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⏭ Screenshot Skip করুন", callback_data=f"proof:skip_screenshot:{course_id}")],
            [InlineKeyboardButton("❌ Cancel",               callback_data=f"cpay:back:{course_id}")],
        ]
    )


def proof_cancel_kb(course_id: str) -> InlineKeyboardMarkup:
    """Screenshot step এ cancel + skip।"""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⏭ Screenshot ছাড়াই জমা দিন", callback_data=f"proof:skip_screenshot:{course_id}")],
            [InlineKeyboardButton("❌ Cancel",                    callback_data=f"cpay:back:{course_id}")],
        ]
    )


def admin_proof_actions_kb(proof_id: str) -> InlineKeyboardMarkup:
    """Admin proof approve/reject keyboard।"""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"proof:approve:{proof_id}"),
                InlineKeyboardButton("❌ Reject",  callback_data=f"proof:reject:{proof_id}"),
            ]
        ]
    )


def my_orders_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back:main")]]
    )


# ════════════════════════════════════════════════════════════════════════════
#  ADMIN INLINE KEYBOARDS
# ════════════════════════════════════════════════════════════════════════════

def admin_panel_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("➕ Add Course",    callback_data="admin:add_course"),
                InlineKeyboardButton("📋 List Courses",  callback_data="admin:list_courses"),
            ],
            [
                InlineKeyboardButton("🧾 Pending Orders", callback_data="admin:orders"),
                InlineKeyboardButton("📊 Stats",          callback_data="admin:stats"),
            ],
            [InlineKeyboardButton("📢 Broadcast", callback_data="admin:broadcast")],
            [InlineKeyboardButton("❌ Close",      callback_data="admin:close")],
        ]
    )


def admin_cancel_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("❌ Cancel", callback_data="admin:cancel")]]
    )


def admin_skip_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏭ Skip",    callback_data="admin:skip_file"),
                InlineKeyboardButton("❌ Cancel",  callback_data="admin:cancel"),
            ]
        ]
    )


def admin_course_list_inline(courses: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    rows = []
    for c in courses:
        cid    = str(c["_id"])
        status = "✅" if c.get("is_active") else "❌"
        label  = f"{status} {c['brand']} › {c['name']}"
        rows.append([
            InlineKeyboardButton(label,       callback_data=f"admin:view:{cid}"),
            InlineKeyboardButton("🗑 Remove", callback_data=f"admin:remove:{cid}"),
        ])
    rows.append([InlineKeyboardButton("🔙 Back to Panel", callback_data="admin:panel")])
    return InlineKeyboardMarkup(rows)


def admin_confirm_remove_inline(course_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Yes, Remove", callback_data=f"admin:confirm_remove:{course_id}"),
                InlineKeyboardButton("❌ Keep It",     callback_data="admin:list_courses"),
            ]
        ]
    )


def admin_order_actions_inline(order_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"admin:approve_order:{order_id}"),
                InlineKeyboardButton("❌ Reject",  callback_data=f"admin:reject_order:{order_id}"),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="admin:orders")],
        ]
    )


def admin_back_panel_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔙 Back to Panel", callback_data="admin:panel")]]
    )


def support_only_kb(support: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"💬 {support}", url=f"https://t.me/{support.lstrip('@')}")]]
    )
