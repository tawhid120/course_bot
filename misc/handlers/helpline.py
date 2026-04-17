from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import db
from config import SUPPORT_USERNAME
from misc import (
    main_menu_inline,
)

async def btn_helpline(client: Client, message: Message):
    # Helpline message DB থেকে আনো
    helpline_text = await db.get_setting(
        "helpline_message",
        default=(
            "🛠 **FCBD SUPPORT CENTER** 🛠\n\n"
            "আপনার সমস্যার ধরন অনুযায়ী নিচের সাপোর্টে যোগাযোগ করুন 👇\n\n"
            "📚 **Class / Document Issue**\n"
            "কোর্সের কোনো ক্লাস বা ডকুমেন্টে সমস্যা হলে এখানে মেসেজ করুন:\n\n"
            "👉 @FCBD_HELPLINE_BOT\n\n"
            "💳 **Payment Issue**\n"
            "পেমেন্ট সংক্রান্ত কোনো সমস্যা হলে এখানে যোগাযোগ করুন:\n\n"
            "👉 @PCBD_HELPLINE_BOT\n\n"
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
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"💬 {support}",
                url=f"https://t.me/{support.lstrip('@')}",
            )],
        ]),
        disable_web_page_preview=True,
    )

def register_handlers(app: Client):
    @app.on_message(
        filters.private & filters.regex(r"^📞 HELPLINE$"),
        group=30,
    )
    async def handler(client, message):
        await btn_helpline(client, message)
