from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
import db
from auth import is_admin
from config import SUPPORT_USERNAME
from misc import (
    States,
    set_state,
    clear_state,
    main_menu_inline,
)
from misc.messages import MSG
from misc.keyboards import brands_inline

async def btn_courses(client: Client, message: Message):
    uid    = message.from_user.id
    brands = await db.get_brands()
    if not brands:
        await message.reply_text(
            MSG.NO_COURSES_AVAILABLE.format(support=SUPPORT_USERNAME),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_inline(),
        )
        return
    set_state(uid, States.SELECT_BRAND)
    await message.reply_text(
        "📚 **Courses**\n\n"
        "কোন Brand এর Course দেখতে চান?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=brands_inline(brands),
    )

def register_handlers(app: Client):
    @app.on_message(
        filters.private & filters.regex(r"^📚 COURSES$"),
        group=30,
    )
    async def handler(client, message):
        await btn_courses(client, message)
