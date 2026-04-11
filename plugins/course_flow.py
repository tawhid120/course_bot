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
from config import SUPPORT_USERNAME
from misc.messages import MSG
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


def setup(app: Client) -> None:
    """
    plugins/__init__.py এর _PLUGIN_SETUPS list থেকে call হয়।
    সব handler এখানে register হয়।
    """

    # ════════════════════════════════════════════════════════════════════════════
    #  ENTRY — Browse Courses
    # ════════════════════════════════════════════════════════════════════════════

    @app.on_callback_query(filters.regex(r"^browse_courses$"))
    async def cb_browse(client: Client, callback: CallbackQuery):
        brands = await db.get_brands()
        if not brands:
            await callback.message.edit_text(
                MSG.NO_COURSES_AVAILABLE.format(support=SUPPORT_USERNAME),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu_inline(),
            )
            await callback.answer()
            return

        set_state(callback.from_user.id, States.SELECT_BRAND)
        await callback.message.edit_text(
            MSG.SELECT_BRAND,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=brands_inline(brands),
        )
        await callback.answer()


    # ════════════════════════════════════════════════════════════════════════════
    #  LEVEL 1 → 2 : Brand → Batch
    # ════════════════════════════════════════════════════════════════════════════

    @app.on_callback_query(filters.regex(r"^brand:(.+)$"))
    async def cb_brand(client: Client, callback: CallbackQuery):
        brand   = callback.matches[0].group(1)
        batches = await db.get_batches(brand)

        if not batches:
            await callback.answer(
                MSG.NO_BATCHES, show_alert=True
            )
            return

        set_state(callback.from_user.id, States.SELECT_BATCH, {"brand": brand})
        await callback.message.edit_text(
            MSG.SELECT_BATCH.format(brand=brand),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=batches_inline(brand, batches),
        )
        await callback.answer()


    # ════════════════════════════════════════════════════════════════════════════
    #  LEVEL 2 → 3 : Batch → Category
    # ════════════════════════════════════════════════════════════════════════════

    @app.on_callback_query(filters.regex(r"^batch:(.+)\|(.+)$"))
    async def cb_batch(client: Client, callback: CallbackQuery):
        brand      = callback.matches[0].group(1)
        batch      = callback.matches[0].group(2)
        categories = await db.get_categories(brand, batch)

        if not categories:
            await callback.answer(
                MSG.NO_CATEGORIES, show_alert=True
            )
            return

        set_state(
            callback.from_user.id,
            States.SELECT_CATEGORY,
            {"brand": brand, "batch": batch},
        )
        await callback.message.edit_text(
            MSG.SELECT_CATEGORY.format(brand=brand, batch=batch),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=categories_inline(brand, batch, categories),
        )
        await callback.answer()


    # ════════════════════════════════════════════════════════════════════════════
    #  LEVEL 3 → 4 : Category → Subject
    # ════════════════════════════════════════════════════════════════════════════

    @app.on_callback_query(filters.regex(r"^category:(.+)\|(.+)\|(.+)$"))
    async def cb_category(client: Client, callback: CallbackQuery):
        brand    = callback.matches[0].group(1)
        batch    = callback.matches[0].group(2)
        category = callback.matches[0].group(3)
        subjects = await db.get_subjects(brand, batch, category)

        if not subjects:
            await callback.answer(
                MSG.NO_SUBJECTS, show_alert=True
            )
            return

        set_state(
            callback.from_user.id,
            States.SELECT_SUBJECT,
            {"brand": brand, "batch": batch, "category": category},
        )
        await callback.message.edit_text(
            MSG.SELECT_SUBJECT.format(
                brand=brand, batch=batch, category=category
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=subjects_inline(brand, batch, category, subjects),
        )
        await callback.answer()


    # ════════════════════════════════════════════════════════════════════════════
    #  LEVEL 4 → 5 : Subject → Course List
    # ════════════════════════════════════════════════════════════════════════════

    @app.on_callback_query(
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
                MSG.NO_COURSES, show_alert=True
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
            MSG.SELECT_COURSE.format(
                brand=brand, batch=batch,
                category=category, subject=subject
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=courses_inline(brand, batch, category, subject, courses),
        )
        await callback.answer()


    # ════════════════════════════════════════════════════════════════════════════
    #  COURSE DETAIL
    # ════════════════════════════════════════════════════════════════════════════

    @app.on_callback_query(filters.regex(r"^course:([a-f0-9]{24})$"))
    async def cb_course_detail(client: Client, callback: CallbackQuery):
        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)

        if not course:
            await callback.answer(MSG.ERROR_COURSE_NOT_FOUND, show_alert=True)
            return

        set_state(
            callback.from_user.id,
            States.VIEW_COURSE,
            {"course_id": course_id},
        )

        text = MSG.COURSE_DETAIL.format(
            name=course["name"],
            brand=course["brand"],
            batch=course["batch"],
            category=course["category"],
            subject=course["subject"],
            description=course.get("description", "N/A"),
            currency=course["currency"],
            price=course["price"],
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

    @app.on_callback_query(filters.regex(r"^buy:([a-f0-9]{24})$"))
    async def cb_buy(client: Client, callback: CallbackQuery):
        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)

        if not course:
            await callback.answer(
                MSG.ERROR_COURSE_NOT_FOUND, show_alert=True
            )
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

    @app.on_callback_query(
        filters.regex(r"^payment_done:([a-f0-9]{24})$")
    )
    async def cb_payment_done(client: Client, callback: CallbackQuery):
        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)

        if not course:
            await callback.answer(
                MSG.ERROR_COURSE_NOT_FOUND, show_alert=True
            )
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
