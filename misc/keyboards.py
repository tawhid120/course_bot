# misc/keyboards.py
# Copyright @YourChannel

"""
All keyboards in one place.

Reply Keyboard  → main_reply_keyboard()
Inline Keyboards → everything else

Callback data conventions:
  brand:<name>
  batch:<brand>|<name>
  category:<brand>|<batch>|<name>
  subject:<brand>|<batch>|<category>|<name>
  course:<id>
  buy:<id>
  payment_done:<id>
  back:main
  browse_courses
  my_orders
  help
  admin:panel | admin:add_course | admin:list_courses
  admin:view:<id> | admin:remove:<id> | admin:confirm_remove:<id>
  admin:orders | admin:order_detail:<id>
  admin:approve_order:<id> | admin:reject_order:<id>
  admin:stats | admin:broadcast | admin:cancel | admin:close
  admin:skip_file
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
    "🏠 Home":          "start",
    "📚 Courses":       "browse_courses",
    "🛒 My Orders":     "my_orders",
    "❓ Help":          "help",
    "👤 Profile":       "profile",
    "🛠 Admin Panel":   "admin_panel",
}


def main_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    Persistent reply keyboard shown at the bottom.
    Two buttons per row.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton("🏠 Home"),
                KeyboardButton("📚 Courses"),
            ],
            [
                KeyboardButton("🛒 My Orders"),
                KeyboardButton("❓ Help"),
            ],
            [
                KeyboardButton("👤 Profile"),
                KeyboardButton("🛠 Admin Panel"),
            ],
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
            [
                InlineKeyboardButton(
                    "📚 Browse Courses", callback_data="browse_courses"
                )
            ],
            [
                InlineKeyboardButton(
                    "🛒 My Orders", callback_data="my_orders"
                ),
                InlineKeyboardButton(
                    "❓ Help", callback_data="help"
                ),
            ],
        ]
    )


def brands_inline(brands: List[str]) -> InlineKeyboardMarkup:
    """Level-1 : Brand selection."""
    rows = [
        [InlineKeyboardButton(f"🏷 {b}", callback_data=f"brand:{b}")]
        for b in brands
    ]
    rows.append(
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back:main")]
    )
    return InlineKeyboardMarkup(rows)


def batches_inline(brand: str, batches: List[str]) -> InlineKeyboardMarkup:
    """Level-2 : Batch selection."""
    rows = [
        [
            InlineKeyboardButton(
                f"📦 {b}", callback_data=f"batch:{brand}|{b}"
            )
        ]
        for b in batches
    ]
    rows.append(
        [InlineKeyboardButton("🔙 Back", callback_data="browse_courses")]
    )
    return InlineKeyboardMarkup(rows)


def categories_inline(
    brand: str, batch: str, categories: List[str]
) -> InlineKeyboardMarkup:
    """Level-3 : Category selection."""
    rows = [
        [
            InlineKeyboardButton(
                f"📂 {c}", callback_data=f"category:{brand}|{batch}|{c}"
            )
        ]
        for c in categories
    ]
    rows.append(
        [InlineKeyboardButton("🔙 Back", callback_data=f"brand:{brand}")]
    )
    return InlineKeyboardMarkup(rows)


def subjects_inline(
    brand: str, batch: str, category: str, subjects: List[str]
) -> InlineKeyboardMarkup:
    """Level-4 : Subject selection."""
    rows = [
        [
            InlineKeyboardButton(
                f"📖 {s}",
                callback_data=f"subject:{brand}|{batch}|{category}|{s}",
            )
        ]
        for s in subjects
    ]
    rows.append(
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data=f"category:{brand}|{batch}|{category}",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def courses_inline(
    brand: str,
    batch: str,
    category: str,
    subject: str,
    courses: List[Dict[str, Any]],
) -> InlineKeyboardMarkup:
    """Level-5 : Course list."""
    rows = [
        [
            InlineKeyboardButton(
                f"🎓 {c['name']}  —  {c['currency']} {c['price']}",
                callback_data=f"course:{str(c['_id'])}",
            )
        ]
        for c in courses
    ]
    rows.append(
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data=f"subject:{brand}|{batch}|{category}|{subject}",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def course_detail_inline(course_id: str) -> InlineKeyboardMarkup:
    """Course detail view — Buy Now button."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🛒 Buy Now", callback_data=f"buy:{course_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back to Menu", callback_data="back:main"
                )
            ],
        ]
    )


def payment_inline(course_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ I Have Paid",
                    callback_data=f"payment_done:{course_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Cancel", callback_data=f"course:{course_id}"
                )
            ],
        ]
    )


def my_orders_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔙 Back to Menu", callback_data="back:main"
                )
            ]
        ]
    )


# ════════════════════════════════════════════════════════════════════════════
#  ADMIN INLINE KEYBOARDS
# ════════════════════════════════════════════════════════════════════════════

def admin_panel_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➕ Add Course", callback_data="admin:add_course"
                ),
                InlineKeyboardButton(
                    "📋 List Courses", callback_data="admin:list_courses"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🧾 Pending Orders", callback_data="admin:orders"
                ),
                InlineKeyboardButton(
                    "📊 Stats", callback_data="admin:stats"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📢 Broadcast", callback_data="admin:broadcast"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Close", callback_data="admin:close"
                )
            ],
        ]
    )


def admin_cancel_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "❌ Cancel", callback_data="admin:cancel"
                )
            ]
        ]
    )


def admin_skip_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⏭ Skip", callback_data="admin:skip_file"
                ),
                InlineKeyboardButton(
                    "❌ Cancel", callback_data="admin:cancel"
                ),
            ]
        ]
    )


def admin_course_list_inline(
    courses: List[Dict[str, Any]],
) -> InlineKeyboardMarkup:
    rows = []
    for c in courses:
        cid    = str(c["_id"])
        status = "✅" if c.get("is_active") else "❌"
        label  = f"{status} {c['brand']} › {c['name']}"
        rows.append(
            [
                InlineKeyboardButton(
                    label, callback_data=f"admin:view:{cid}"
                ),
                InlineKeyboardButton(
                    "🗑 Remove",
                    callback_data=f"admin:remove:{cid}",
                ),
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                "🔙 Back to Panel", callback_data="admin:panel"
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def admin_confirm_remove_inline(course_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Yes, Remove",
                    callback_data=f"admin:confirm_remove:{course_id}",
                ),
                InlineKeyboardButton(
                    "❌ Keep It",
                    callback_data="admin:list_courses",
                ),
            ]
        ]
    )


def admin_order_actions_inline(order_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Approve",
                    callback_data=f"admin:approve_order:{order_id}",
                ),
                InlineKeyboardButton(
                    "❌ Reject",
                    callback_data=f"admin:reject_order:{order_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back", callback_data="admin:orders"
                )
            ],
        ]
    )


def admin_back_panel_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔙 Back to Panel", callback_data="admin:panel"
                )
            ]
        ]
    )
