# plugins/start.py
# Copyright @YourChannel

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, Message

import db
from auth import is_admin
from config import BOT_NAME, SUPPORT_USERNAME
from misc.messages import MSG
from misc import (
    admin_panel_inline,
    brands_inline,
    main_menu_inline,
    my_orders_inline,
    clear_state,
    get_state,
    set_state,
    States,
)
from misc.keyboards import main_reply_keyboard
from utils import LOGGER


def setup(app: Client) -> None:

    # ══════════════════════════════════════════════════════════
    #  /start
    # ══════════════════════════════════════════════════════════

    @app.on_message(filters.command("start") & filters.private)
    async def cmd_start(client: Client, message: Message):
        user = message.from_user

        # Ban check
        if await db.is_banned(user.id):
            await message.reply_text(
                "🚫 **আপনাকে এই Bot থেকে Banned করা হয়েছে।**\n\n"
                f"সাহায্যের জন্য: {SUPPORT_USERNAME}",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        await db.upsert_user(
            user.id,
            {
                "username":   user.username,
                "first_name": user.first_name,
                "last_name":  user.last_name,
            },
        )
        clear_state(user.id)

        LOGGER.info(f"[/start] user={user.id} ({user.username})")

        # Dynamic Reply Keyboard পাঠাও
        try:
            from plugins.dynamic_buttons import build_dynamic_reply_keyboard
            reply_kb = await build_dynamic_reply_keyboard()
        except Exception:
            reply_kb = main_reply_keyboard()

        # Keyboard load message
        await message.reply_text(
            MSG.KEYBOARD_LOADED,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_kb,
        )

        # Welcome message
        if is_admin(user.id):
            welcome_text = MSG.WELCOME_ADMIN.format(
                bot_name=BOT_NAME,
                name=user.first_name,
            )
        else:
            welcome_text = MSG.WELCOME.format(
                bot_name=BOT_NAME,
                name=user.first_name,
            )

        await message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_inline(),
            disable_web_page_preview=True,
        )

    # ══════════════════════════════════════════════════════════
    #  /admin
    # ══════════════════════════════════════════════════════════

    @app.on_message(filters.command("admin") & filters.private)
    async def cmd_admin(client: Client, message: Message):
        if not is_admin(message.from_user.id):
            await message.reply_text(
                "⛔ You are not authorised to use this command.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        clear_state(message.from_user.id)
        LOGGER.info(f"[/admin] user={message.from_user.id}")
        from plugins.admin_panel import _admin_panel_kb
        await message.reply_text(
            "🛠 **Admin Panel**\n\nChoose an action:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_admin_panel_kb(),
        )

    # ══════════════════════════════════════════════════════════
    #  /cancel
    # ══════════════════════════════════════════════════════════

    @app.on_message(filters.command("cancel") & filters.private)
    async def cmd_cancel(client: Client, message: Message):
        uid   = message.from_user.id
        state = get_state(uid)
        if state == States.IDLE:
            await message.reply_text(
                MSG.NOTHING_TO_CANCEL,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu_inline(),
            )
            return
        clear_state(uid)

        # Also clear plugin states
        try:
            from plugins.payment_request import _pay_req_state
            _pay_req_state.pop(uid, None)
        except Exception:
            pass
        try:
            from plugins.dynamic_buttons import _btn_edit_state
            _btn_edit_state.pop(uid, None)
        except Exception:
            pass
        try:
            from plugins.admin_panel import _code_set_state, _helpline_edit_state
            _code_set_state.pop(uid, None)
            _helpline_edit_state.pop(uid, None)
        except Exception:
            pass

        await message.reply_text(
            MSG.CANCELLED,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_inline(),
        )

    # ══════════════════════════════════════════════════════════
    #  /help
    # ══════════════════════════════════════════════════════════

    @app.on_message(filters.command("help") & filters.private)
    async def cmd_help(client: Client, message: Message):
        await message.reply_text(
            MSG.HELP.format(support=SUPPORT_USERNAME),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_inline(),
        )

    # ══════════════════════════════════════════════════════════
    #  /ban & /unban commands
    # ══════════════════════════════════════════════════════════

    @app.on_message(filters.command("ban") & filters.private)
    async def cmd_ban(client: Client, message: Message):
        if not is_admin(message.from_user.id):
            return
        parts = message.command
        if len(parts) < 2:
            await message.reply_text("Usage: `/ban <user_id> [reason]`", parse_mode=ParseMode.MARKDOWN)
            return
        try:
            target_id = int(parts[1])
        except ValueError:
            await message.reply_text("❌ Valid User ID দিন।")
            return
        reason = " ".join(parts[2:]) if len(parts) > 2 else "No reason given"
        await db.ban_user(target_id, reason)
        try:
            await client.send_message(
                target_id,
                f"🚫 **আপনাকে এই Bot থেকে Banned করা হয়েছে।**\n\nকারণ: {reason}",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass
        await message.reply_text(f"🚫 User `{target_id}` banned!\nকারণ: {reason}", parse_mode=ParseMode.MARKDOWN)

    @app.on_message(filters.command("unban") & filters.private)
    async def cmd_unban(client: Client, message: Message):
        if not is_admin(message.from_user.id):
            return
        parts = message.command
        if len(parts) < 2:
            await message.reply_text("Usage: `/unban <user_id>`", parse_mode=ParseMode.MARKDOWN)
            return
        try:
            target_id = int(parts[1])
        except ValueError:
            await message.reply_text("❌ Valid User ID দিন।")
            return
        ok = await db.unban_user(target_id)
        if ok:
            try:
                await client.send_message(
                    target_id,
                    "✅ **আপনার Ban তুলে নেওয়া হয়েছে।**\n\nআবার Bot ব্যবহার করতে পারবেন।",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass
            await message.reply_text(f"✅ User `{target_id}` unbanned!", parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply_text(f"❌ User `{target_id}` banned তালিকায় নেই।", parse_mode=ParseMode.MARKDOWN)

    # ══════════════════════════════════════════════════════════
    #  Callbacks
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(filters.regex(r"^back:main$"))
    async def cb_back_main(client: Client, callback: CallbackQuery):
        clear_state(callback.from_user.id)
        await callback.message.edit_text(
            MSG.MAIN_MENU,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_inline(),
        )
        await callback.answer()

    @app.on_callback_query(filters.regex(r"^help$"))
    async def cb_help(client: Client, callback: CallbackQuery):
        await callback.message.edit_text(
            MSG.HELP.format(support=SUPPORT_USERNAME),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_inline(),
        )
        await callback.answer()

    @app.on_callback_query(filters.regex(r"^my_orders$"))
    async def cb_my_orders(client: Client, callback: CallbackQuery):
        uid    = callback.from_user.id
        orders = await db.get_orders_by_user(uid)

        if not orders:
            text = MSG.MY_ORDERS_EMPTY
        else:
            lines = [MSG.MY_ORDERS_HEADER]
            for i, o in enumerate(orders, 1):
                course = await db.get_course_by_id(str(o.get("course_id", "")))
                cname  = course["name"] if course else "Unknown"
                status_key  = o.get("status", "pending")
                status_text = MSG.ORDER_STATUS.get(status_key, "❓ Unknown")
                lines.append(
                    MSG.MY_ORDERS_ITEM.format(
                        index=i,
                        course_name=cname,
                        status_emoji={
                            "pending":  "⏳",
                            "approved": "✅",
                            "rejected": "❌",
                        }.get(status_key, "❓"),
                        status=status_text,
                        date=(
                            o.get("created_at", "").strftime("%d %b %Y")
                            if o.get("created_at")
                            else "N/A"
                        ),
                    )
                )
            text = "\n".join(lines)

        await callback.message.edit_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=my_orders_inline(),
        )
        await callback.answer()
