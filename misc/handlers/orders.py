from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import db
from config import SUPPORT_USERNAME
from misc import (
    main_menu_inline,
    my_orders_inline,
)
from misc.messages import MSG

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
        parse_mode="md",
        reply_markup=my_orders_inline(),
    )

def register_handlers(app: Client):
    @app.on_message(
        filters.private & filters.regex(r"^📦 MY ORDERS$"),
        group=30,
    )
    async def handler(client, message):
        await btn_my_orders(client, message)
