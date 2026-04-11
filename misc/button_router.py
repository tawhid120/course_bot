# misc/button_router.py
# Copyright @YourChannel

"""
Registers a catch-all text handler that intercepts Reply Keyboard presses
and routes them to the correct plugin or inline response.

Call setup_button_router(app) once in main.py AFTER all plugins are loaded.
"""

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

import db
from auth.admin_check import is_admin
from misc.keyboards import BUTTON_COMMAND_MAP, main_reply_keyboard, main_menu_inline
from utils import LOGGER


def setup_button_router(app: Client) -> None:
    """Register Reply Keyboard router on the Client instance."""

    _labels = set(BUTTON_COMMAND_MAP.keys())

    # ── catch reply-keyboard button presses ──────────────────────────────────
    @app.on_message(
        filters.private
        & filters.text
        & filters.create(
            lambda _, __, msg: (
                msg.text is not None
                and msg.text.strip() in _labels
            )
        ),
        group=50,
    )
    async def _button_router(client: Client, message: Message):
        label   = message.text.strip()
        command = BUTTON_COMMAND_MAP.get(label)
        uid     = message.from_user.id

        LOGGER.info(
            f"[ButtonRouter] user={uid} "
            f"label='{label}' → command='{command}'"
        )

        if not command:
            return

        # ── 🏠 Home ──────────────────────────────────────────────────────────
        if command == "start":
            name = message.from_user.first_name
            await message.reply_text(
                f"🏠 **Main Menu** — Hello {name}!\n\n"
                f"Choose an option below 👇",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu_inline(),
            )

        # ── 📚 Browse Courses ─────────────────────────────────────────────────
        elif command == "browse_courses":
            brands = await db.get_brands()
            if not brands:
                await message.reply_text(
                    "😔 No courses available yet. Check back soon!",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=main_menu_inline(),
                )
                return
            from misc.keyboards import brands_inline
            from misc.states import States, set_state
            set_state(uid, States.SELECT_BRAND)
            await message.reply_text(
                "🏷 **Select a Brand**\n\n"
                "Choose the brand / institute you want to explore:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=brands_inline(brands),
            )

        # ── 🛒 My Orders ──────────────────────────────────────────────────────
        elif command == "my_orders":
            orders = await db.get_orders_by_user(uid)
            if not orders:
                text = (
                    "🛒 **My Orders**\n\n"
                    "You haven't purchased anything yet."
                )
            else:
                lines = ["🛒 **My Orders**\n"]
                for i, o in enumerate(orders, 1):
                    course = await db.get_course_by_id(
                        str(o.get("course_id", ""))
                    )
                    cname = course["name"] if course else "Unknown"
                    emoji = {
                        "pending":  "⏳",
                        "approved": "✅",
                        "rejected": "❌",
                    }.get(o.get("status", ""), "❓")
                    lines.append(
                        f"{i}. **{cname}**\n"
                        f"   {emoji} {o.get('status','?').title()}"
                    )
                text = "\n".join(lines)
            from misc.keyboards import my_orders_inline
            await message.reply_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=my_orders_inline(),
            )

        # ── ❓ Help ───────────────────────────────────────────────────────────
        elif command == "help":
            from config import SUPPORT_USERNAME
            await message.reply_text(
                "❓ **Help & Support**\n\n"
                "• Browse courses with 📚 **Courses** button.\n"
                "• After selecting a course tap **🛒 Buy Now**.\n"
                "• Complete payment → tap **✅ I Have Paid**.\n"
                "• Admin verifies and activates your access.\n\n"
                f"📞 Support: {SUPPORT_USERNAME}\n\n"
                "**Commands:**\n"
                "`/start` — Main menu\n"
                "`/cancel` — Cancel current action\n"
                "`/admin` — Admin panel _(admins only)_",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu_inline(),
            )

        # ── 👤 Profile ────────────────────────────────────────────────────────
        elif command == "profile":
            user    = message.from_user
            orders  = await db.get_orders_by_user(uid)
            approved = [o for o in orders if o.get("status") == "approved"]
            await message.reply_text(
                f"👤 **My Profile**\n\n"
                f"🆔 **ID:** `{user.id}`\n"
                f"📛 **Name:** {user.first_name} "
                f"{user.last_name or ''}\n"
                f"🔖 **Username:** "
                f"{'@' + user.username if user.username else 'N/A'}\n\n"
                f"🎓 **Purchased Courses:** {len(approved)}\n"
                f"🧾 **Total Orders:** {len(orders)}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu_inline(),
            )

        # ── 🛠 Admin Panel ────────────────────────────────────────────────────
        elif command == "admin_panel":
            if not is_admin(uid):
                await message.reply_text(
                    "⛔ **Access Denied**\n\n"
                    "This feature is for administrators only.",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
            from misc.keyboards import admin_panel_inline
            from misc.states import clear_state
            clear_state(uid)
            await message.reply_text(
                "🛠 **Admin Panel**\n\nChoose an action:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_panel_inline(),
            )

    # ── menu shortcut ─────────────────────────────────────────────────────────
    @app.on_message(
        filters.private
        & filters.regex(r"^(?i:menu|home)$"),
        group=49,
    )
    async def _menu_shortcut(client: Client, message: Message):
        name = message.from_user.first_name
        await message.reply_text(
            f"🏠 **Main Menu** — Hey {name}!\n\nChoose an option below 👇",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_inline(),
        )
        # Refresh reply keyboard
        await client.send_message(
            chat_id=message.chat.id,
            text="_Keyboard refreshed._",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_reply_keyboard(),
        )
