from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
import db
from misc import (
    main_menu_inline,
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
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_inline(),
    )

def register_handlers(app: Client):
    @app.on_message(
        filters.private & filters.regex(r"^👤 MY PROFILE$"),
        group=30,
    )
    async def handler(client, message):
        await btn_my_profile(client, message)
