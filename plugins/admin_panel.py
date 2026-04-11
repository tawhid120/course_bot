# plugins/admin_panel.py
# Copyright @YourChannel

"""
Full Admin Panel plugin.

Handles:
  ─ admin:panel           → show panel
  ─ admin:add_course      → start 9-step FSM
  ─ admin:skip_file       → save course without image
  ─ admin:list_courses    → paginated course list with Remove buttons
  ─ admin:view:<id>       → single course detail (admin)
  ─ admin:remove:<id>     → confirm removal
  ─ admin:confirm_remove:<id> → deactivate course
  ─ admin:orders          → list pending orders
  ─ admin:order_detail:<id>   → order detail
  ─ admin:approve_order:<id>  → approve + notify user
  ─ admin:reject_order:<id>   → reject  + notify user
  ─ admin:stats           → bot statistics
  ─ admin:broadcast       → set FSM → broadcast message
  ─ admin:cancel          → cancel FSM
  ─ admin:close           → close panel

All text inputs in FSM are handled by the on_message handler
at the bottom of this file.
"""

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import db
from auth.admin_check import admin_callback_required, is_admin
from misc.keyboards import (
    admin_back_panel_inline,
    admin_cancel_inline,
    admin_confirm_remove_inline,
    admin_course_list_inline,
    admin_order_actions_inline,
    admin_panel_inline,
    admin_skip_inline,
    main_menu_inline,
)
from misc.states import (
    States,
    clear_state,
    get_data,
    get_state,
    set_state,
    update_data,
)
from utils import LOGGER


# ════════════════════════════════════════════════════════════════════════════
#  PANEL & CANCEL
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^admin:panel$"))
@admin_callback_required
async def cb_admin_panel(client: Client, callback: CallbackQuery):
    clear_state(callback.from_user.id)
    await callback.message.edit_text(
        "🛠 **Admin Panel**\n\nChoose an action:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_panel_inline(),
    )
    await callback.answer()


@Client.on_callback_query(filters.regex(r"^admin:close$"))
@admin_callback_required
async def cb_admin_close(client: Client, callback: CallbackQuery):
    clear_state(callback.from_user.id)
    await callback.message.edit_text(
        "✅ Admin panel closed.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_inline(),
    )
    await callback.answer("Panel closed.")


@Client.on_callback_query(filters.regex(r"^admin:cancel$"))
@admin_callback_required
async def cb_admin_cancel(client: Client, callback: CallbackQuery):
    clear_state(callback.from_user.id)
    await callback.message.edit_text(
        "❌ **Action cancelled.**\n\n🛠 **Admin Panel**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_panel_inline(),
    )
    await callback.answer("Cancelled.")


# ════════════════════════════════════════════════════════════════════════════
#  ADD COURSE — STEP 1 trigger
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^admin:add_course$"))
@admin_callback_required
async def cb_add_course_start(client: Client, callback: CallbackQuery):
    set_state(callback.from_user.id, States.ADMIN_ADD_BRAND)
    await callback.message.edit_text(
        "➕ **Add New Course** — Step 1 / 9\n\n"
        "Type the **Brand / Institute Name**:\n"
        "_e.g. Physics Wallah, Unacademy_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_cancel_inline(),
    )
    await callback.answer()


# ════════════════════════════════════════════════════════════════════════════
#  SKIP FILE
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^admin:skip_file$"))
@admin_callback_required
async def cb_skip_file(client: Client, callback: CallbackQuery):
    uid = callback.from_user.id
    if get_state(uid) != States.ADMIN_ADD_FILE:
        await callback.answer("Nothing to skip.", show_alert=True)
        return

    data = get_data(uid)
    data["file_id"] = None

    course_id = await _persist_course(data)
    clear_state(uid)

    await callback.message.edit_text(
        f"✅ **Course Added!** _(no preview image)_\n\n"
        f"🆔 ID: `{course_id}`\n"
        f"🏷 Brand: {data.get('brand')}\n"
        f"📦 Batch: {data.get('batch')}\n"
        f"📂 Category: {data.get('category')}\n"
        f"📖 Subject: {data.get('subject')}\n"
        f"🎓 Name: {data.get('name')}\n"
        f"💰 Price: {data.get('currency')} {data.get('price')}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_panel_inline(),
    )
    await callback.answer("Course saved!")

    LOGGER.info(f"[AddCourse] admin={uid} course_id={course_id} (no image)")


# ════════════════════════════════════════════════════════════════════════════
#  LIST COURSES
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^admin:list_courses$"))
@admin_callback_required
async def cb_list_courses(client: Client, callback: CallbackQuery):
    courses = await db.get_all_courses_admin()
    if not courses:
        await callback.message.edit_text(
            "📋 **All Courses**\n\nNo courses in the database yet.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_back_panel_inline(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"📋 **All Courses** ({len(courses)} total)\n\n"
        f"✅ = Active  |  ❌ = Deactivated\n"
        f"Tap 🗑 Remove to deactivate a course.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_course_list_inline(courses),
    )
    await callback.answer()


# ════════════════════════════════════════════════════════════════════════════
#  VIEW SINGLE COURSE (admin detail)
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^admin:view:([a-f0-9]{24})$"))
@admin_callback_required
async def cb_admin_view(client: Client, callback: CallbackQuery):
    course_id = callback.matches[0].group(1)
    course    = await db.get_course_by_id(course_id)

    if not course:
        await callback.answer("Course not found.", show_alert=True)
        return

    status = "✅ Active" if course.get("is_active") else "❌ Deactivated"

    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🗑 Remove Course",
                    callback_data=f"admin:remove:{course_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back to List",
                    callback_data="admin:list_courses",
                )
            ],
        ]
    )

    await callback.message.edit_text(
        f"🎓 **Course Details**\n\n"
        f"🆔 ID: `{course_id}`\n"
        f"🏷 Brand: {course['brand']}\n"
        f"📦 Batch: {course['batch']}\n"
        f"📂 Category: {course['category']}\n"
        f"📖 Subject: {course['subject']}\n"
        f"📛 Name: {course['name']}\n"
        f"📝 Description: {course.get('description', 'N/A')}\n"
        f"💰 Price: {course['currency']} {course['price']}\n"
        f"🖼 Preview: {'Yes ✅' if course.get('file_id') else 'No ❌'}\n"
        f"📌 Status: {status}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb,
    )
    await callback.answer()


# ════════════════════════════════════════════════════════════════════════════
#  REMOVE COURSE
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^admin:remove:([a-f0-9]{24})$"))
@admin_callback_required
async def cb_remove_course(client: Client, callback: CallbackQuery):
    course_id = callback.matches[0].group(1)
    course    = await db.get_course_by_id(course_id)

    if not course:
        await callback.answer("Course not found.", show_alert=True)
        return

    await callback.message.edit_text(
        f"⚠️ **Confirm Removal**\n\n"
        f"Are you sure you want to remove:\n"
        f"**{course['name']}**\n"
        f"_{course['brand']} › {course['batch']}_\n\n"
        f"This will deactivate the course immediately.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_confirm_remove_inline(course_id),
    )
    await callback.answer()


@Client.on_callback_query(
    filters.regex(r"^admin:confirm_remove:([a-f0-9]{24})$")
)
@admin_callback_required
async def cb_confirm_remove(client: Client, callback: CallbackQuery):
    course_id = callback.matches[0].group(1)
    ok        = await db.deactivate_course(course_id)

    if ok:
        LOGGER.info(
            f"[RemoveCourse] admin={callback.from_user.id} "
            f"course_id={course_id}"
        )
        await callback.message.edit_text(
            "✅ **Course removed successfully!**\n\n"
            "The course is now deactivated and will not appear "
            "in user menus.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_back_panel_inline(),
        )
        await callback.answer("Course removed!")
    else:
        await callback.answer(
            "❌ Failed to remove course.", show_alert=True
        )


# ════════════════════════════════════════════════════════════════════════════
#  PENDING ORDERS
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^admin:orders$"))
@admin_callback_required
async def cb_admin_orders(client: Client, callback: CallbackQuery):
    orders = await db.get_all_pending_orders()

    if not orders:
        await callback.message.edit_text(
            "🧾 **Pending Orders**\n\nNo pending orders right now! 🎉",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_back_panel_inline(),
        )
        await callback.answer()
        return

    rows = []
    for o in orders:
        oid   = str(o["_id"])
        label = (
            f"#{oid[-6:]} — "
            f"{o.get('course_name', '?')} — "
            f"{o.get('user_name', '?')}"
        )
        rows.append(
            [
                InlineKeyboardButton(
                    label,
                    callback_data=f"admin:order_detail:{oid}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                "🔙 Back to Panel", callback_data="admin:panel"
            )
        ]
    )

    await callback.message.edit_text(
        f"🧾 **Pending Orders** ({len(orders)})\n\n"
        f"Select an order to review:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(rows),
    )
    await callback.answer()


@Client.on_callback_query(
    filters.regex(r"^admin:order_detail:([a-f0-9]{24})$")
)
@admin_callback_required
async def cb_order_detail(client: Client, callback: CallbackQuery):
    order_id = callback.matches[0].group(1)
    from bson import ObjectId

    order = await db.get_db().orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    await callback.message.edit_text(
        f"🧾 **Order Details**\n\n"
        f"🆔 Order ID: `{order_id}`\n"
        f"👤 User: {order.get('user_name','?')} "
        f"(`{order.get('user_id','?')}`)\n"
        f"🎓 Course: {order.get('course_name','?')}\n"
        f"💰 Amount: {order.get('currency','')} "
        f"{order.get('amount','?')}\n"
        f"📌 Status: {order.get('status','?').title()}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_order_actions_inline(order_id),
    )
    await callback.answer()


@Client.on_callback_query(
    filters.regex(r"^admin:approve_order:([a-f0-9]{24})$")
)
@admin_callback_required
async def cb_approve_order(client: Client, callback: CallbackQuery):
    order_id = callback.matches[0].group(1)
    from bson import ObjectId

    order = await db.get_db().orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    await db.update_order_status(order_id, "approved")
    LOGGER.info(
        f"[ApproveOrder] admin={callback.from_user.id} "
        f"order={order_id}"
    )

    await callback.message.edit_text(
        f"✅ Order `{order_id[-6:]}` **approved** successfully!",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_back_panel_inline(),
    )

    # Notify user
    try:
        await client.send_message(
            order["user_id"],
            f"🎉 **Payment Approved!**\n\n"
            f"Your payment for **{order.get('course_name','your course')}** "
            f"has been verified!\n\n"
            f"🆔 Order ID: `{order_id}`\n\n"
            f"You now have access. Thank you! 🙏",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        LOGGER.warning(f"Could not notify user {order['user_id']}: {e}")

    await callback.answer("Order approved!")


@Client.on_callback_query(
    filters.regex(r"^admin:reject_order:([a-f0-9]{24})$")
)
@admin_callback_required
async def cb_reject_order(client: Client, callback: CallbackQuery):
    order_id = callback.matches[0].group(1)
    from bson import ObjectId

    order = await db.get_db().orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    await db.update_order_status(order_id, "rejected")
    LOGGER.info(
        f"[RejectOrder] admin={callback.from_user.id} "
        f"order={order_id}"
    )

    await callback.message.edit_text(
        f"❌ Order `{order_id[-6:]}` **rejected**.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_back_panel_inline(),
    )

    # Notify user
    try:
        await client.send_message(
            order["user_id"],
            f"❌ **Payment Rejected**\n\n"
            f"Your payment for **{order.get('course_name','your course')}** "
            f"could not be verified.\n\n"
            f"🆔 Order ID: `{order_id}`\n\n"
            f"Please contact support for help.",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        LOGGER.warning(f"Could not notify user {order['user_id']}: {e}")

    await callback.answer("Order rejected.")


# ════════════════════════════════════════════════════════════════════════════
#  STATS
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^admin:stats$"))
@admin_callback_required
async def cb_stats(client: Client, callback: CallbackQuery):
    all_users   = await db.get_all_users()
    all_courses = await db.get_all_courses_admin()
    active_c    = [c for c in all_courses if c.get("is_active")]
    pending_o   = await db.get_all_pending_orders()
    db_inst     = db.get_db()
    total_o     = await db_inst.orders.count_documents({})
    approved_o  = await db_inst.orders.count_documents({"status": "approved"})

    await callback.message.edit_text(
        f"📊 **Bot Statistics**\n\n"
        f"👥 Total Users:      **{len(all_users)}**\n"
        f"🎓 Total Courses:    **{len(all_courses)}** "
        f"({len(active_c)} active)\n"
        f"🧾 Total Orders:     **{total_o}**\n"
        f"✅ Approved Orders:  **{approved_o}**\n"
        f"⏳ Pending Orders:   **{len(pending_o)}**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_back_panel_inline(),
    )
    await callback.answer()


# ════════════════════════════════════════════════════════════════════════════
#  BROADCAST
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^admin:broadcast$"))
@admin_callback_required
async def cb_broadcast_start(client: Client, callback: CallbackQuery):
    set_state(callback.from_user.id, States.ADMIN_BROADCAST)
    await callback.message.edit_text(
        "📢 **Broadcast Message**\n\n"
        "Send the message you want to broadcast to **all users**.\n"
        "_Supports text, photos, and documents._",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_cancel_inline(),
    )
    await callback.answer()


# ════════════════════════════════════════════════════════════════════════════
#  FSM MESSAGE HANDLER (Admin text/media input)
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(
    filters.private
    & ~filters.command(
        ["start", "admin", "cancel", "help"]
    ),
    group=10,
)
async def admin_fsm_handler(client: Client, message: Message):
    uid = message.from_user.id
    if not is_admin(uid):
        return  # Only admins handled here

    state = get_state(uid)

    # ── Non-admin FSM state ── ignore silently
    if state not in (
        States.ADMIN_ADD_BRAND,
        States.ADMIN_ADD_BATCH,
        States.ADMIN_ADD_CATEGORY,
        States.ADMIN_ADD_SUBJECT,
        States.ADMIN_ADD_NAME,
        States.ADMIN_ADD_DESC,
        States.ADMIN_ADD_PRICE,
        States.ADMIN_ADD_CURRENCY,
        States.ADMIN_ADD_FILE,
        States.ADMIN_BROADCAST,
    ):
        return

    # ── Step 1: Brand ─────────────────────────────────────────────────────
    if state == States.ADMIN_ADD_BRAND:
        val = message.text.strip() if message.text else None
        if not val:
            await message.reply_text(
                "⚠️ Please send the **Brand Name** as text.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_cancel_inline(),
            )
            return
        update_data(uid, brand=val)
        set_state(uid, States.ADMIN_ADD_BATCH, get_data(uid))
        await message.reply_text(
            f"✅ Brand: **{val}**\n\n"
            f"➕ **Step 2 / 9** — Type the **Batch Name**:\n"
            f"_e.g. 2024-Batch, Jan-2025_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_cancel_inline(),
        )

    # ── Step 2: Batch ─────────────────────────────────────────────────────
    elif state == States.ADMIN_ADD_BATCH:
        val = message.text.strip() if message.text else None
        if not val:
            await message.reply_text(
                "⚠️ Please send the **Batch Name** as text.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_cancel_inline(),
            )
            return
        update_data(uid, batch=val)
        set_state(uid, States.ADMIN_ADD_CATEGORY, get_data(uid))
        await message.reply_text(
            f"✅ Batch: **{val}**\n\n"
            f"➕ **Step 3 / 9** — Type the **Category**:\n"
            f"_e.g. Science, Commerce, Arts_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_cancel_inline(),
        )

    # ── Step 3: Category ──────────────────────────────────────────────────
    elif state == States.ADMIN_ADD_CATEGORY:
        val = message.text.strip() if message.text else None
        if not val:
            await message.reply_text(
                "⚠️ Please send the **Category** as text.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_cancel_inline(),
            )
            return
        update_data(uid, category=val)
        set_state(uid, States.ADMIN_ADD_SUBJECT, get_data(uid))
        await message.reply_text(
            f"✅ Category: **{val}**\n\n"
            f"➕ **Step 4 / 9** — Type the **Subject Name**:\n"
            f"_e.g. Physics, Mathematics, Chemistry_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_cancel_inline(),
        )

    # ── Step 4: Subject ───────────────────────────────────────────────────
    elif state == States.ADMIN_ADD_SUBJECT:
        val = message.text.strip() if message.text else None
        if not val:
            await message.reply_text(
                "⚠️ Please send the **Subject Name** as text.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_cancel_inline(),
            )
            return
        update_data(uid, subject=val)
        set_state(uid, States.ADMIN_ADD_NAME, get_data(uid))
        await message.reply_text(
            f"✅ Subject: **{val}**\n\n"
            f"➕ **Step 5 / 9** — Type the **Course Name**:\n"
            f"_e.g. JEE Advanced Complete Physics 2024_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_cancel_inline(),
        )

    # ── Step 5: Course Name ───────────────────────────────────────────────
    elif state == States.ADMIN_ADD_NAME:
        val = message.text.strip() if message.text else None
        if not val:
            await message.reply_text(
                "⚠️ Please send the **Course Name** as text.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_cancel_inline(),
            )
            return
        update_data(uid, name=val)
        set_state(uid, States.ADMIN_ADD_DESC, get_data(uid))
        await message.reply_text(
            f"✅ Name: **{val}**\n\n"
            f"➕ **Step 6 / 9** — Type the **Course Description**:\n"
            f"_Detailed info about what the course covers_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_cancel_inline(),
        )

    # ── Step 6: Description ───────────────────────────────────────────────
    elif state == States.ADMIN_ADD_DESC:
        val = message.text.strip() if message.text else None
        if not val:
            await message.reply_text(
                "⚠️ Please send the **Description** as text.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_cancel_inline(),
            )
            return
        update_data(uid, description=val)
        set_state(uid, States.ADMIN_ADD_PRICE, get_data(uid))
        await message.reply_text(
            f"✅ Description saved.\n\n"
            f"➕ **Step 7 / 9** — Type the **Price** (numbers only):\n"
            f"_e.g. 999 or 1499.50_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_cancel_inline(),
        )

    # ── Step 7: Price ─────────────────────────────────────────────────────
    elif state == States.ADMIN_ADD_PRICE:
        raw = message.text.strip() if message.text else ""
        try:
            price = float(raw)
        except ValueError:
            await message.reply_text(
                "⚠️ Invalid price. Please enter a number.\n"
                "_e.g. `999` or `1499.50`_",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_cancel_inline(),
            )
            return
        update_data(uid, price=price)
        set_state(uid, States.ADMIN_ADD_CURRENCY, get_data(uid))
        await message.reply_text(
            f"✅ Price: **{price}**\n\n"
            f"➕ **Step 8 / 9** — Type the **Currency Code**:\n"
            f"_e.g. INR, USD, EUR_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_cancel_inline(),
        )

    # ── Step 8: Currency ──────────────────────────────────────────────────
    elif state == States.ADMIN_ADD_CURRENCY:
        val = (
            message.text.strip().upper() if message.text else None
        )
        if not val:
            await message.reply_text(
                "⚠️ Please send the **Currency Code**.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_cancel_inline(),
            )
            return
        update_data(uid, currency=val)
        set_state(uid, States.ADMIN_ADD_FILE, get_data(uid))
        await message.reply_text(
            f"✅ Currency: **{val}**\n\n"
            f"➕ **Step 9 / 9** — Send a **Preview Image** for the course.\n\n"
            f"Tap **⏭ Skip** to save without an image.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_skip_inline(),
        )

    # ── Step 9: File / Photo ──────────────────────────────────────────────
    elif state == States.ADMIN_ADD_FILE:
        file_id = None
        if message.photo:
            file_id = message.photo.file_id
        elif message.document:
            file_id = message.document.file_id

        data = get_data(uid)
        data["file_id"] = file_id

        course_id = await _persist_course(data)
        clear_state(uid)

        LOGGER.info(
            f"[AddCourse] admin={uid} "
            f"course_id={course_id} "
            f"image={'yes' if file_id else 'no'}"
        )

        await message.reply_text(
            f"✅ **Course Added Successfully!**\n\n"
            f"🆔 ID: `{course_id}`\n"
            f"🏷 Brand: {data.get('brand')}\n"
            f"📦 Batch: {data.get('batch')}\n"
            f"📂 Category: {data.get('category')}\n"
            f"📖 Subject: {data.get('subject')}\n"
            f"🎓 Name: {data.get('name')}\n"
            f"💰 Price: {data.get('currency')} {data.get('price')}\n"
            f"🖼 Preview: {'Yes ✅' if file_id else 'No ❌'}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_panel_inline(),
        )

    # ── Broadcast ─────────────────────────────────────────────────────────
    elif state == States.ADMIN_BROADCAST:
        await _do_broadcast(client, message, uid)


# ════════════════════════════════════════════════════════════════════════════
#  PRIVATE HELPERS
# ════════════════════════════════════════════════════════════════════════════

async def _persist_course(data: dict) -> str:
    """Save course dict to MongoDB. Returns str _id."""
    return await db.add_course(
        {
            "brand":       data["brand"],
            "batch":       data["batch"],
            "category":    data["category"],
            "subject":     data["subject"],
            "name":        data["name"],
            "description": data.get("description", ""),
            "price":       data["price"],
            "currency":    data["currency"],
            "file_id":     data.get("file_id"),
        }
    )


async def _do_broadcast(
    client: Client, message: Message, uid: int
) -> None:
    """Broadcast a message to all registered users."""
    all_users = await db.get_all_users()
    sent      = 0
    failed    = 0

    status = await message.reply_text(
        f"📢 Broadcasting to **{len(all_users)}** users… please wait.",
        parse_mode=ParseMode.MARKDOWN,
    )

    for user in all_users:
        try:
            if message.photo:
                await client.send_photo(
                    user["user_id"],
                    message.photo.file_id,
                    caption=message.caption or "",
                    parse_mode=ParseMode.MARKDOWN,
                )
            elif message.document:
                await client.send_document(
                    user["user_id"],
                    message.document.file_id,
                    caption=message.caption or "",
                    parse_mode=ParseMode.MARKDOWN,
                )
            else:
                await client.send_message(
                    user["user_id"],
                    message.text or "",
                    parse_mode=ParseMode.MARKDOWN,
                )
            sent += 1
        except Exception:
            failed += 1

    clear_state(uid)
    LOGGER.info(
        f"[Broadcast] admin={uid} sent={sent} failed={failed}"
    )

    await status.edit_text(
        f"✅ **Broadcast Complete!**\n\n"
        f"✅ Sent:   {sent}\n"
        f"❌ Failed: {failed}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_back_panel_inline(),
    )
