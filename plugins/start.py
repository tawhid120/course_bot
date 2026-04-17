# plugins/start.py
# Copyright @YourChannel

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

import db
from auth import is_admin
from config import BOT_NAME, SUPPORT_USERNAME, FORCE_SUB_CHANNEL
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
from misc.handlers import courses, orders, profile, helpline, admin
from utils import LOGGER


# ════════════════════════════════════════════════════════════
#  Reply Keyboard Builder
#  স্ক্রিনশট অনুযায়ী:
#    Row 1: FREE COURSE | PAID COURSE
#    Row 2: ACCOUNT DETAILS | SUPPORT
#    Row 3: ADMIN PANEL (শুধু admin দেখবে)
# ════════════════════════════════════════════════════════════

def build_reply_keyboard(is_admin_user: bool = False) -> ReplyKeyboardMarkup:
    if is_admin_user:
        keyboard = [
            [KeyboardButton("📚 COURSES"), KeyboardButton("📦 MY ORDERS")],
            [KeyboardButton("👤 MY PROFILE"), KeyboardButton("📞 HELPLINE")],
            [KeyboardButton("🛠️ ADMIN PANEL")],
        ]
    else:
        keyboard = [
            [KeyboardButton("📚 COURSES"), KeyboardButton("📦 MY ORDERS")],
            [KeyboardButton("👤 MY PROFILE"), KeyboardButton("📞 HELPLINE")],
        ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


# ════════════════════════════════════════════════════════════
#  Welcome Inline Keyboard
# ════════════════════════════════════════════════════════════

def _fcbd_community_kb() -> InlineKeyboardMarkup:
    """স্ক্রিনশটের মতো — FCBD COMMUNITY বাটন।"""
    channel_link = ""
    if FORCE_SUB_CHANNEL:
        _raw = str(FORCE_SUB_CHANNEL).strip()
        if _raw.startswith("-100"):
            channel_link = f"https://t.me/c/{_raw.lstrip('-100')}"
        elif _raw.startswith("@"):
            channel_link = f"https://t.me/{_raw.lstrip('@')}"
        else:
            channel_link = f"https://t.me/{_raw}"

    if channel_link:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 FCBD COMMUNITY", url=channel_link)],
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 FCBD COMMUNITY", callback_data="back:main")],
    ])


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

        is_admin_user = is_admin(user.id)
        reply_kb      = build_reply_keyboard(is_admin_user)

        # ── Step 1: Reply Keyboard load message ───────────────
        await message.reply_text(
            MSG.KEYBOARD_LOADED,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_kb,
        )

        # ── Step 2: Welcome message (স্ক্রিনশটের মতো) ────────
        welcome_text = (
            f"🎉 **Free Course Bangladesh Bot-এ আপনাকে স্বাগতম** 🎉\n\n"
            f"আমাদের চ্যানেলে যুক্ত হওয়ার জন্য অসংখ্য ধন্যবাদ।\n\n"
            f"এই বটটি ব্যবহার করতে ছবিতে দেখানো আইকনে ক্লিক করুন। এরপর আপনার "
            f"কিবোর্ডে প্রয়োজনীয় সকল বাটন দেখতে পাবেন, যা ব্যবহার করে আপনি "
            f"সহজেই পরবর্তী ধাপে এগিয়ে যেতে পারবেন।\n\n"
            f"আমাদের সাথে আপনার যাত্রা সুন্দর ও সফল হোক — এই কামনা রইলো। 😊"
        )

        await message.reply_photo(
            photo="assets/welcome.jpg",
            caption=welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_fcbd_community_kb(),
        )

    # ══════════════════════════════════════════════════════════
    #  Register Modular Handlers
    # ══════════════════════════════════════════════════════════
    courses.register_handlers(app)
    orders.register_handlers(app)
    profile.register_handlers(app)
    helpline.register_handlers(app)
    admin.register_handlers(app)

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