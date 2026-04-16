# plugins/user_profile.py
# Copyright @YourChannel
# ─────────────────────────────────────────────────────────────
# User Profile, My Orders, Helpline
# ─────────────────────────────────────────────────────────────

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import db
from config import SUPPORT_USERNAME
from misc.keyboards import main_menu_inline
from utils import LOGGER


def setup(app: Client) -> None:

    # ── 👤 MY PROFILE ──────────────────────────────────────────
    @app.on_message(
        filters.private & filters.regex(r"^👤 MY PROFILE$"),
        group=20,
    )
    async def btn_my_profile(client: Client, message: Message):
        uid  = message.from_user.id
        user = message.from_user

        orders   = await db.get_orders_by_user(uid)
        approved = [o for o in orders if o.get("status") == "approved"]
        pending  = [o for o in orders if o.get("status") == "pending"]
        rejected = [o for o in orders if o.get("status") == "rejected"]

        username = f"@{user.username}" if user.username else "নেই"
        fullname = f"{user.first_name} {user.last_name or ''}".strip()

        await message.reply_text(
            f"👤 **আমার Profile**\n\n"
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
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_inline(),
        )

    # ── 🛒 MY ORDERS ───────────────────────────────────────────
    @app.on_message(
        filters.private & filters.regex(r"^🛒 MY ORDERS$"),
        group=20,
    )
    async def btn_my_orders(client: Client, message: Message):
        uid    = message.from_user.id
        orders = await db.get_orders_by_user(uid)

        if not orders:
            await message.reply_text(
                "🛒 **আমার Orders**\n\n"
                "আপনি এখনো কোনো Course কেনেননি।\n\n"
                "📚 Course কিনতে **💸 PAYMENT REQUEST** বাটনে ক্লিক করুন।",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu_inline(),
            )
            return

        lines = ["🛒 **আমার Orders**\n"]
        for i, o in enumerate(orders[:15], 1):
            status = o.get("status", "pending")
            emoji  = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(
                status, "❓"
            )
            date_str = ""
            if o.get("created_at"):
                try:
                    date_str = o["created_at"].strftime("%d %b %Y")
                except Exception:
                    pass

            membership = ""
            if status == "approved" and o.get("membership_id"):
                membership = f"\n   🎫 `{o['membership_id']}`"

            lines.append(
                f"{i}. **{o.get('course_name', 'Unknown')}**\n"
                f"   {emoji} {status.title()}"
                f"{membership}\n"
                f"   📅 {date_str}"
            )

        await message.reply_text(
            "\n\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Main Menu", callback_data="back:main")]]
            ),
        )

    # ── ☎️ HELPLINE ────────────────────────────────────────────
    @app.on_message(
        filters.private & filters.regex(r"^☎️ HELPLINE$"),
        group=20,
    )
    async def btn_helpline(client: Client, message: Message):
        # DB থেকে helpline message আনো (admin set করতে পারে)
        helpline_text = await db.get_setting(
            "helpline_message",
            default=(
                f"☎️ **Helpline**\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📞 **Support:** {SUPPORT_USERNAME}\n\n"
                f"সকাল ৯টা — রাত ১১টা\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"💬 যেকোনো সমস্যায় আমাদের সাথে যোগাযোগ করুন।"
            ),
        )

        support = await db.get_setting("support_username", default=SUPPORT_USERNAME)

        await message.reply_text(
            helpline_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            f"💬 {support}",
                            url=f"https://t.me/{support.lstrip('@')}",
                        )
                    ]
                ]
            ),
        )

    LOGGER.info("[UserProfile] Plugin loaded ✅")
