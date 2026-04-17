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

# ── Default Helpline Message (স্ক্রিনশটের মতো) ──────────────────
_DEFAULT_HELPLINE = (
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
)


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

    # ── ☎️ HELPLINE (পুরনো বাটন label — backward compat) ──────
    @app.on_message(
        filters.private & filters.regex(r"^☎️ HELPLINE$"),
        group=20,
    )
    async def btn_helpline_old(client: Client, message: Message):
        await _send_helpline(message)

    # ── 🧑‍💼 SUPPORT (নতুন বাটন label) ───────────────────────────
    @app.on_message(
        filters.private & filters.regex(r"^🧑‍💼 SUPPORT 🧑‍💼$"),
        group=20,
    )
    async def btn_helpline_new(client: Client, message: Message):
        await _send_helpline(message)

    LOGGER.info("[UserProfile] Plugin loaded ✅")


# ════════════════════════════════════════════════════════════
#  Helper — Helpline message পাঠানো
# ════════════════════════════════════════════════════════════

async def _send_helpline(message: Message) -> None:
    """Helpline message পাঠানো।"""
    helpline_text = await db.get_setting(
        "helpline_message",
        default=_DEFAULT_HELPLINE,
    )
    support = await db.get_setting("support_username", default=SUPPORT_USERNAME)

    await message.reply_text(
        helpline_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"💬 {support}",
                url=f"https://t.me/{support.lstrip('@')}",
            )],
        ]),
        disable_web_page_preview=True,
    )