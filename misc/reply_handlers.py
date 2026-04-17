# misc/reply_handlers.py
# Copyright @YourChannel

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import db
from auth import is_admin
from config import SUPPORT_USERNAME
from misc.messages import MSG
from misc.keyboards import main_menu_inline
from misc import clear_state, get_state, set_state, States

async def register_reply_handlers(app: Client):
    # ── 📚 COURSES ──────────────────────────────────────────
    @app.on_message(
        filters.private & filters.regex(r"^📚 COURSES$"),
        group=30,
    )
    async def btn_courses(client: Client, message: Message):
        uid    = message.from_user.id
        brands = await db.get_brands()
        if not brands:
            await message.reply_text(
                MSG.NO_COURSES_AVAILABLE.format(support=SUPPORT_USERNAME),
                parse_mode="markdown",
                reply_markup=main_menu_inline(),
            )
            return
        from misc.keyboards import brands_inline as _brands_inline
        set_state(uid, States.SELECT_BRAND)
        await message.reply_text(
            "📚 **Courses**\n\n"
            "কোন Brand এর Course দেখতে চান?",
            parse_mode="markdown",
            reply_markup=_brands_inline(brands),
        )

    # ── 📦 MY ORDERS ─────────────────────────────────────────
    @app.on_message(
        filters.private & filters.regex(r"^📦 MY ORDERS$"),
        group=30,
    )
    async def btn_my_orders(client: Client, message: Message):
        uid    = message.from_user.id
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

        await message.reply_text(
            text,
            parse_mode="markdown",
            reply_markup=main_menu_inline(),
        )

    # ── 👤 MY PROFILE ──────────────────────────────────────
    @app.on_message(
        filters.private & filters.regex(r"^👤 MY PROFILE$"),
        group=30,
    )
    async def btn_my_profile(client: Client, message: Message):
        uid    = message.from_user.id
        user   = message.from_user
        orders = await db.get_orders_by_user(uid)

        approved = [o for o in orders if o.get("status") == "approved"]
        pending  = [o for o in orders if o.get("status") == "pending"]
        rejected = [o for o in orders if o.get("status") == "rejected"]
        username = f"@{user.username}" if user.username else "নেই"
        fullname = f"{user.first_name} {user.last_name or ''}".strip()

        await message.reply_text(
            f"👤 **Account Details**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 **User ID:** `{uid}`\n"
            f"📛 **নাম:** {fullname}\n"
            f"🔖 **Username:** {username}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎓 **কেনা Courses:** {len(approved)}\n"
            f"⏳ **Pending:** {len(pending)}\n"
            f"❌ **Rejected:** {len(rejected)}\n"
            f"🧾 **মোট Orders:** {len(orders)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="markdown",
            reply_markup=main_menu_inline(),
        )

    # ── 📞 HELPLINE ─────────────────────────────────────────────
    @app.on_message(
        filters.private & filters.regex(r"^📞 HELPLINE$"),
        group=30,
    )
    async def btn_helpline(client: Client, message: Message):
        helpline_text = await db.get_setting(
            "helpline_message",
            default=(
                "🛠 **FCBD SUPPORT CENTER** 🛠\n\n"
                "আপনার সমস্যার ধরন অনুযায়ী নিচের সাপোর্টে যোগাযোগ করুন 👇\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📚 **Class / Document Issue**\n"
                "কোর্সের কোনো ক্লাস বা ডকুমেন্টে সমস্যা হলে এখানে মেসেজ করুন:\n\n"
                "👉 @FCBD_HELPLINE_BOT\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "💳 **Payment Issue**\n"
                "পেমেন্ট সংক্রান্ত কোনো সমস্যা হলে এখানে যোগাযোগ করুন:\n\n"
                "👉 @PCBD_HELPLINE_BOT\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🎥 **How to Buy Course**\n"
                "কিভাবে কোর্স কিনবেন বুঝতে সমস্যা হলে নিচের ভিডিওটি দেখুন 👇\n\n"
                "▶️ (ভিডিও লিংক)\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "⚡ দ্রুত সমাধানের জন্য সঠিক সাপোর্টে মেসেজ করুন"
            ),
        )

        support = await db.get_setting("support_username", default=SUPPORT_USERNAME)

        await message.reply_text(
            helpline_text,
            parse_mode="markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    f"💬 {support}",
                    url=f"https://t.me/{support.lstrip('@')}",
                )],
            ]),
            disable_web_page_preview=True,
        )

    # ── 🛠️ ADMIN PANEL ────────────────────────────────────────
    @app.on_message(
        filters.private & filters.regex(r"^🛠️ ADMIN PANEL$"),
        group=30,
    )
    async def btn_admin_panel(client: Client, message: Message):
        uid = message.from_user.id

        if not is_admin(uid):
            await message.reply_text(
                "⛔ **Access Denied**\n\n"
                "এই বাটনটি শুধুমাত্র Admin দের জন্য।",
                parse_mode="markdown",
            )
            return

        clear_state(uid)
        from plugins.admin_panel import _admin_panel_kb
        await message.reply_text(
            "🛠 **Admin Panel**\n\nChoose an action:",
            parse_mode="markdown",
            reply_markup=_admin_panel_kb(),
        )
