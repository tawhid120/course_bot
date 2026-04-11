# plugins/start.py
# Copyright @YourChannel

"""
Handles:
  /start   → Welcome + main menu + reply keyboard
  /cancel  → Cancel FSM
  /help    → Help text
  /admin   → Admin panel
  Callbacks: back:main | help | browse_courses (entry) | my_orders
"""

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, Message

import db
from auth.admin_check import is_admin
from config import BOT_NAME, SUPPORT_USERNAME
from misc.keyboards import (
    admin_panel_inline,
    brands_inline,
    main_menu_inline,
    main_reply_keyboard,
    my_orders_inline,
)
from misc.states import States, clear_state, get_state, set_state
from utils import LOGGER


# ════════════════════════════════════════════════════════════════════════════
#  /start
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("start") & filters.private)
async def cmd_start(client: Client, message: Message):
    user = message.from_user

    await db.upsert_user(
        user.id,
        {
            "username":   user.username,
            "first_name": user.first_name,
            "last_name":  user.last_name,
        },
    )
    clear_state(user.id)

    admin_hint = ""
    if is_admin(user.id):
        admin_hint = (
            "\n\n🔑 *You are an admin.*  "
            "Use /admin or tap **🛠 Admin Panel** button."
        )

    LOGGER.info(f"[/start] user={user.id} ({user.username})")

    # Send reply keyboard first
    await message.reply_text(
        "_Keyboard loaded._",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_reply_keyboard(),
    )

    # Send welcome with inline menu
    await message.reply_text(
        f"👋 Welcome to **{BOT_NAME}**, {user.first_name}!\n\n"
        f"🎓 Browse and purchase premium courses easily.\n"
        f"Tap a button below to get started.{admin_hint}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_inline(),
        disable_web_page_preview=True,
    )


# ════════════════════════════════════════════════════════════════════════════
#  /admin
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("admin") & filters.private)
async def cmd_admin(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text(
            "⛔ You are not authorised to use this command.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    clear_state(message.from_user.id)
    LOGGER.info(f"[/admin] user={message.from_user.id}")
    await message.reply_text(
        "🛠 **Admin Panel**\n\nChoose an action:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_panel_inline(),
    )


# ════════════════════════════════════════════════════════════════════════════
#  /cancel
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("cancel") & filters.private)
async def cmd_cancel(client: Client, message: Message):
    uid   = message.from_user.id
    state = get_state(uid)
    if state == States.IDLE:
        await message.reply_text(
            "ℹ️ Nothing to cancel.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_inline(),
        )
        return
    clear_state(uid)
    await message.reply_text(
        "✅ Cancelled. Back to main menu.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_inline(),
    )


# ════════════════════════════════════════════════════════════════════════════
#  /help
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("help") & filters.private)
async def cmd_help(client: Client, message: Message):
    await message.reply_text(
        f"❓ **Help & Support**\n\n"
        f"• Browse courses with 📚 **Courses** button.\n"
        f"• After selecting, tap **🛒 Buy Now**.\n"
        f"• Pay → tap **✅ I Have Paid**.\n"
        f"• Admin verifies and activates your access.\n\n"
        f"📞 Support: {SUPPORT_USERNAME}\n\n"
        f"`/start` — Main menu\n"
        f"`/cancel` — Cancel current action",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_inline(),
    )


# ════════════════════════════════════════════════════════════════════════════
#  CALLBACKS — Navigation
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^back:main$"))
async def cb_back_main(client: Client, callback: CallbackQuery):
    clear_state(callback.from_user.id)
    await callback.message.edit_text(
        "🏠 **Main Menu**\n\nWhat would you like to do?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_inline(),
    )
    await callback.answer()


@Client.on_callback_query(filters.regex(r"^help$"))
async def cb_help(client: Client, callback: CallbackQuery):
    await callback.message.edit_text(
        f"❓ **Help & Support**\n\n"
        f"• Browse courses → 📚 Browse Courses\n"
        f"• Buy a course → 🛒 Buy Now\n"
        f"• Pay → ✅ I Have Paid\n\n"
        f"📞 Support: {SUPPORT_USERNAME}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_inline(),
    )
    await callback.answer()


@Client.on_callback_query(filters.regex(r"^my_orders$"))
async def cb_my_orders(client: Client, callback: CallbackQuery):
    uid    = callback.from_user.id
    orders = await db.get_orders_by_user(uid)

    if not orders:
        text = "🛒 **My Orders**\n\nYou haven't purchased anything yet."
    else:
        lines = ["🛒 **My Orders**\n"]
        for i, o in enumerate(orders, 1):
            course = await db.get_course_by_id(str(o.get("course_id", "")))
            cname  = course["name"] if course else "Unknown"
            emoji  = {
                "pending":  "⏳",
                "approved": "✅",
                "rejected": "❌",
            }.get(o.get("status", ""), "❓")
            lines.append(
                f"{i}. **{cname}**\n"
                f"   {emoji} {o.get('status','?').title()}"
            )
        text = "\n".join(lines)

    await callback.message.edit_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=my_orders_inline(),
    )
    await callback.answer()
