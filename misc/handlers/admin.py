from pyrogram import Client, filters
from pyrogram.types import Message
from auth import is_admin
from misc import (
    clear_state,
)
from plugins.admin_panel import _admin_panel_kb

async def btn_admin_panel(client: Client, message: Message):
    uid = message.from_user.id

    # Admin না হলে ভদ্রভাবে deny করো
    if not is_admin(uid):
        await message.reply_text(
            "⛔ **Access Denied**\n\n"
            "এই বাটনটি শুধুমাত্র Admin দের জন্য।",
            parse_mode="md",
        )
        return

    clear_state(uid)
    await message.reply_text(
        "🛠 **Admin Panel**\n\nChoose an action:",
        parse_mode="md",
        reply_markup=_admin_panel_kb(),
    )

def register_handlers(app: Client):
    @app.on_message(
        filters.private & filters.regex(r"^🛠.*ADMIN PANEL$"),
        group=30,
    )
    async def handler(client, message):
        await btn_admin_panel(client, message)
