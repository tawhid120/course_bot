# plugins/course_flow.py
# Copyright @YourChannel

"""
Full multi-level course navigation:
  browse_courses
    → brand:<name>
      → batch:<brand>|<name>
        → category:<brand>|<batch>|<name>
          → subject:<brand>|<batch>|<category>|<name>
            → course:<id>  (detail)
              → buy:<id>
                → payment_done:<id>
"""

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery

import db
from config import ADMIN_IDS, PAYMENT_INFO
from misc.keyboards import (
    batches_inline,
    brands_inline,
    categories_inline,
    course_detail_inline,
    courses_inline,
    main_menu_inline,
    payment_inline,
    subjects_inline,
    admin_order_actions_inline,
)
from misc.states import States, clear_state, set_state
from utils import LOGGER


# ════════════════════════════════════════════════════════════════════════════
#  ENTRY — Browse Courses
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^browse_courses$"))
async def cb_browse(client: Client, callback: CallbackQuery):
    brands = await db.get_brands()
    if not brands:
        await callback.message.edit_text(
            "😔 **No courses available yet.**\n\nPlease check back later!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_inline(),
        )
        await callback.answer()
        return

    set_state(callback.from_user.id, States.SELECT_BRAND)
    await callback.message.edit_text(
        "🏷 **Select a Brand**\n\n"
        "Choose the brand / institute you want to explore:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=brands_inline(brands),
    )
    await callback.answer()


# ════════════════════════════════════════════════════════════════════════════
#  LEVEL 1 → 2 : Brand → Batch
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^brand:(.+)$"))
async def cb_brand(client: Client, callback: CallbackQuery):
    brand   = callback.matches[0].group(1)
    batches = await db.get_batches(brand)

    if not batches:
        await callback.answer(
            "⚠️ No batches found for this brand.", show_alert=True
        )
        return

    set_state(callback.from_user.id, States.SELECT_BATCH, {"brand": brand})
    await callback.message.edit_text(
        f"📦 **Select a Batch**\n\n"
        f"*Brand:* `{brand}`\n\nChoose a batch:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=batches_inline(brand, batches),
    )
    await callback.answer()


# ════════════════════════════════════════════════════════════════════════════
#  LEVEL 2 → 3 : Batch → Category
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^batch:(.+)\|(.+)$"))
async def cb_batch(client: Client, callback: CallbackQuery):
    brand      = callback.matches[0].group(1)
    batch      = callback.matches[0].group(2)
    categories = await db.get_categories(brand, batch)

    if not categories:
        await callback.answer(
            "⚠️ No categories found for this batch.", show_alert=True
        )
        return

    set_state(
        callback.from_user.id,
        States.SELECT_CATEGORY,
        {"brand": brand, "batch": batch},
    )
    await callback.message.edit_text(
        f"📂 **Select a Category**\n\n"
        f"*Brand:* `{brand}` › *Batch:* `{batch}`\n\nChoose a category:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=categories_inline(brand, batch, categories),
    )
    await callback.answer()


# ════════════════════════════════════════════════════════════════════════════
#  LEVEL 3 → 4 : Category → Subject
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^category:(.+)\|(.+)\|(.+)$"))
async def cb_category(client: Client, callback: CallbackQuery):
    brand    = callback.matches[0].group(1)
    batch    = callback.matches[0].group(2)
    category = callback.matches[0].group(3)
    subjects = await db.get_subjects(brand, batch, category)

    if not subjects:
        await callback.answer(
            "⚠️ No subjects found for this category.", show_alert=True
        )
        return

    set_state(
        callback.from_user.id,
        States.SELECT_SUBJECT,
        {"brand": brand, "batch": batch, "category": category},
    )
    await callback.message.edit_text(
        f"📖 **Select a Subject**\n\n"
        f"*Brand:* `{brand}` › *Batch:* `{batch}` "
        f"› *Category:* `{category}`\n\nChoose a subject:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=subjects_inline(brand, batch, category, subjects),
    )
    await callback.answer()


# ════════════════════════════════════════════════════════════════════════════
#  LEVEL 4 → 5 : Subject → Course List
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(
    filters.regex(r"^subject:(.+)\|(.+)\|(.+)\|(.+)$")
)
async def cb_subject(client: Client, callback: CallbackQuery):
    brand    = callback.matches[0].group(1)
    batch    = callback.matches[0].group(2)
    category = callback.matches[0].group(3)
    subject  = callback.matches[0].group(4)
    courses  = await db.get_courses(brand, batch, category, subject)

    if not courses:
        await callback.answer(
            "⚠️ No courses found for this subject.", show_alert=True
        )
        return

    set_state(
        callback.from_user.id,
        States.SELECT_COURSE,
        {
            "brand":    brand,
            "batch":    batch,
            "category": category,
            "subject":  subject,
        },
    )
    await callback.message.edit_text(
        f"🎓 **Available Courses**\n\n"
        f"*{brand}* › *{batch}* › *{category}* › *{subject}*\n\n"
        f"Select a course to view details:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=courses_inline(brand, batch, category, subject, courses),
    )
    await callback.answer()


# ════════════════════════════════════════════════════════════════════════════
#  COURSE DETAIL
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^course:([a-f0-9]{24})$"))
async def cb_course_detail(client: Client, callback: CallbackQuery):
    course_id = callback.matches[0].group(1)
    course    = await db.get_course_by_id(course_id)

    if not course:
        await callback.answer("⚠️ Course not found.", show_alert=True)
        return

    set_state(
        callback.from_user.id,
        States.VIEW_COURSE,
        {"course_id": course_id},
    )

    text = (
        f"🎓 **{course['name']}**\n\n"
        f"🏷 *Brand:*    `{course['brand']}`\n"
        f"📦 *Batch:*    `{course['batch']}`\n"
        f"📂 *Category:* `{course['category']}`\n"
        f"📖 *Subject:*  `{course['subject']}`\n\n"
        f"📝 **Description:**\n{course.get('description', 'N/A')}\n\n"
        f"💰 **Price:** {course['currency']} {course['price']}"
    )

    if course.get("file_id"):
        try:
            await callback.message.reply_photo(
                photo=course["file_id"],
                caption=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=course_detail_inline(course_id),
            )
            await callback.message.delete()
        except Exception:
            await callback.message.edit_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=course_detail_inline(course_id),
            )
    else:
        await callback.message.edit_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=course_detail_inline(course_id),
        )

    await callback.answer()


# ════════════════════════════════════════════════════════════════════════════
#  BUY NOW
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^buy:([a-f0-9]{24})$"))
async def cb_buy(client: Client, callback: CallbackQuery):
    course_id = callback.matches[0].group(1)
    course    = await db.get_course_by_id(course_id)

    if not course:
        await callback.answer("⚠️ Course not found.", show_alert=True)
        return

    set_state(
        callback.from_user.id,
        States.PAYMENT,
        {"course_id": course_id},
    )

    await callback.message.edit_text(
        f"💳 **Payment Instructions**\n\n"
        f"🎓 *Course:* **{course['name']}**\n"
        f"💰 *Amount:* **{course['currency']} {course['price']}**\n\n"
        f"{PAYMENT_INFO}\n\n"
        f"Once you have paid, tap **✅ I Have Paid** below.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=payment_inline(course_id),
    )
    await callback.answer()


# ════════════════════════════════════════════════════════════════════════════
#  PAYMENT DONE
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(
    filters.regex(r"^payment_done:([a-f0-9]{24})$")
)
async def cb_payment_done(client: Client, callback: CallbackQuery):
    course_id = callback.matches[0].group(1)
    course    = await db.get_course_by_id(course_id)

    if not course:
        await callback.answer("⚠️ Course not found.", show_alert=True)
        return

    uid = callback.from_user.id

    order_id = await db.create_order(
        {
            "user_id":     uid,
            "user_name":   callback.from_user.first_name,
            "username":    callback.from_user.username,
            "course_id":   course_id,
            "course_name": course["name"],
            "amount":      course["price"],
            "currency":    course["currency"],
        }
    )

    clear_state(uid)

    LOGGER.info(
        f"[Order] user={uid} course='{course['name']}' "
        f"order_id={order_id}"
    )

    await callback.message.edit_text(
        f"✅ **Payment Submitted!**\n\n"
        f"🎓 *Course:* **{course['name']}**\n"
        f"🆔 *Order ID:* `{order_id}`\n\n"
        f"Our team will verify your payment and activate your access shortly.\n"
        f"You will receive a confirmation message here. 🙏",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_inline(),
    )

    # Notify all admins
    admin_text = (
        f"🔔 **New Payment Received!**\n\n"
        f"👤 *User:* [{callback.from_user.first_name}]"
        f"(tg://user?id={uid}) (`{uid}`)\n"
        f"🎓 *Course:* {course['name']}\n"
        f"💰 *Amount:* {course['currency']} {course['price']}\n"
        f"🆔 *Order ID:* `{order_id}`"
    )
    for admin_id in ADMIN_IDS:
        try:
            await client.send_message(
                admin_id,
                admin_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_order_actions_inline(order_id),
            )
        except Exception as e:
            LOGGER.warning(f"Could not notify admin {admin_id}: {e}")

    await callback.answer("✅ Payment submitted for review!")
