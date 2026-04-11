# plugins/admin_panel.py
# Copyright @YourChannel
# ─────────────────────────────────────────────────────────────
# পুরো ফাইলটা এভাবে লিখবে।
# শুধু নতুন/পরিবর্তিত অংশগুলো mark করা আছে ← নতুন
# ─────────────────────────────────────────────────────────────

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import db
from auth import is_admin
from config import SUPPORT_USERNAME
from misc import (
    States,
    admin_back_panel_inline,
    admin_cancel_inline,
    admin_confirm_remove_inline,
    admin_course_list_inline,
    admin_order_actions_inline,
    admin_panel_inline,
    admin_skip_inline,
    clear_state,
    get_data,
    get_state,
    main_menu_inline,
    set_state,
    update_data,
)
from misc.messages import MSG
from utils import LOGGER


# ════════════════════════════════════════════════════════════
#  Helper functions (module level)
# ════════════════════════════════════════════════════════════

async def _persist_course(data: dict) -> str:
    return await db.add_course(
        {
            "brand":          data["brand"],
            "batch":          data["batch"],
            "category":       data["category"],
            "subject":        data["subject"],
            "name":           data["name"],
            "description":    data.get("description", ""),
            "price":          data["price"],
            "currency":       data["currency"],
            "file_id":        data.get("file_id"),
            "group_id":       data.get("group_id"),        # ← নতুন
            "group_username": data.get("group_username"),  # ← নতুন
            "group_checked":  data.get("group_checked", False),  # ← নতুন
        }
    )


async def _do_broadcast(
    client: Client, message: Message, uid: int
) -> None:
    all_users = await db.get_all_users()
    sent = failed = 0

    status = await message.reply_text(
        MSG.BROADCAST_SENDING.format(
            total_users=len(all_users)
        ),
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
    await status.edit_text(
        MSG.BROADCAST_DONE.format(sent=sent, failed=failed),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_back_panel_inline(),
    )


# ════════════════════════════════════════════════════════════
#  setup(app)
# ════════════════════════════════════════════════════════════

def setup(app: Client) -> None:

    # ══════════════════════════════════════════════════════════
    #  Panel, Close, Cancel — same as before
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(filters.regex(r"^admin:panel$"))
    async def cb_admin_panel(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        clear_state(callback.from_user.id)
        await callback.message.edit_text(
            "🛠 **Admin Panel**\n\nChoose an action:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_panel_inline(),
        )
        await callback.answer()

    @app.on_callback_query(filters.regex(r"^admin:close$"))
    async def cb_admin_close(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        clear_state(callback.from_user.id)
        await callback.message.edit_text(
            "✅ Admin panel closed.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_inline(),
        )
        await callback.answer()

    @app.on_callback_query(filters.regex(r"^admin:cancel$"))
    async def cb_admin_cancel(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        clear_state(callback.from_user.id)
        await callback.message.edit_text(
            "❌ **Action cancelled.**\n\n🛠 **Admin Panel**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_panel_inline(),
        )
        await callback.answer("Cancelled.")

    # ══════════════════════════════════════════════════════════
    #  Add Course — Step 1 Trigger
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(filters.regex(r"^admin:add_course$"))
    async def cb_add_course_start(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        set_state(callback.from_user.id, States.ADMIN_ADD_BRAND)
        await callback.message.edit_text(
            "➕ **Add New Course** — Step 1 / 10\n\n"
            "Type the **Brand / Institute Name**:\n"
            "_e.g. Physics Wallah, Unacademy_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_cancel_inline(),
        )
        await callback.answer()

    # ══════════════════════════════════════════════════════════
    #  Skip File
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(filters.regex(r"^admin:skip_file$"))
    async def cb_skip_file(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        uid = callback.from_user.id
        if get_state(uid) != States.ADMIN_ADD_FILE:
            return await callback.answer("Nothing to skip.", show_alert=True)

        update_data(uid, file_id=None)
        set_state(uid, States.ADMIN_ADD_GROUP, get_data(uid))

        await callback.message.edit_text(
            "⏭ Image skip করা হয়েছে।\n\n"
            "➕ **Step 10 / 10** — **Private Group/Channel ID** দিন:\n\n"
            "📌 Group ID কীভাবে পাবেন:\n"
            "• Group এ `/checkgroup` bot forward করুন\n"
            "• অথবা `/start` দিন @userinfobot কে\n"
            "• ID সাধারণত `-100` দিয়ে শুরু হয়\n\n"
            "_e.g. `-1001234567890`_\n\n"
            "⏭ Group ছাড়া save করতে **Skip** করুন।",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_group_skip_kb(),
        )
        await callback.answer()

    # ══════════════════════════════════════════════════════════
    #  Skip Group (Step 10) ← নতুন
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(filters.regex(r"^admin:skip_group$"))
    async def cb_skip_group(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        uid = callback.from_user.id
        if get_state(uid) != States.ADMIN_ADD_GROUP:
            return await callback.answer("Nothing to skip.", show_alert=True)

        data = get_data(uid)
        data["group_id"]       = None
        data["group_username"] = None
        data["group_checked"]  = False

        course_id = await _persist_course(data)
        clear_state(uid)

        LOGGER.info(
            f"[AddCourse] admin={uid} "
            f"course_id={course_id} (no group)"
        )

        await callback.message.edit_text(
            f"✅ **Course Added!** _(group ছাড়া)_\n\n"
            f"🆔 ID: `{course_id}`\n"
            f"🏷 Brand: {data.get('brand')}\n"
            f"📦 Batch: {data.get('batch')}\n"
            f"📂 Category: {data.get('category')}\n"
            f"📖 Subject: {data.get('subject')}\n"
            f"🎓 Name: {data.get('name')}\n"
            f"💰 Price: {data.get('currency')} {data.get('price')}\n"
            f"👥 Group: ❌ (পরে যোগ করতে পারবেন)\n\n"
            f"💡 Group যোগ করতে:\n"
            f"List Courses → Course → Set Group",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_panel_inline(),
        )
        await callback.answer("Course saved!")

    # ══════════════════════════════════════════════════════════
    #  Set Group for Existing Course ← নতুন
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(
        filters.regex(r"^admin:set_group:([a-f0-9]{24})$")
    )
    async def cb_set_group_start(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)
        if not course:
            return await callback.answer("Course not found.", show_alert=True)

        uid = callback.from_user.id
        set_state(
            uid,
            States.ADMIN_SET_GROUP,
            {"course_id": course_id, "course_name": course["name"]},
        )

        current = course.get("group_id", "❌ নেই")
        await callback.message.edit_text(
            f"👥 **Group Set করুন**\n\n"
            f"📦 Course: `{course['name']}`\n"
            f"🔢 Current Group ID: `{current}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"Private Group/Channel এর **ID** পাঠান:\n\n"
            f"📌 Group ID কীভাবে পাবেন:\n"
            f"• `/checkgroup -1001234567890` দিন\n"
            f"• Group → Settings → Copy ID\n"
            f"• ID সাধারণত `-100` দিয়ে শুরু হয়\n\n"
            f"_e.g. `-1001234567890`_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_cancel_inline(),
        )
        await callback.answer()

    # ══════════════════════════════════════════════════════════
    #  List Courses
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(filters.regex(r"^admin:list_courses$"))
    async def cb_list_courses(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        courses = await db.get_all_courses_admin()
        if not courses:
            await callback.message.edit_text(
                "📋 **All Courses**\n\nNo courses yet.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_back_panel_inline(),
            )
            return await callback.answer()

        await callback.message.edit_text(
            f"📋 **All Courses** ({len(courses)} total)\n\n"
            f"✅ = Active | ❌ = Deactivated | 👥 = Has Group",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_course_list_inline(courses),
        )
        await callback.answer()

    # ══════════════════════════════════════════════════════════
    #  View Single Course (Admin) ← group info যোগ
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(
        filters.regex(r"^admin:view:([a-f0-9]{24})$")
    )
    async def cb_admin_view(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)
        if not course:
            return await callback.answer("Course not found.", show_alert=True)

        status    = "✅ Active" if course.get("is_active") else "❌ Deactivated"
        group_id  = course.get("group_id")
        grp_check = course.get("group_checked", False)

        group_line = (
            f"`{group_id}` "
            f"{'✅ Verified' if grp_check else '⚠️ Not verified'}"
            if group_id
            else "❌ নেই"
        )

        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "👥 Group Set/Update",       # ← নতুন বাটন
                        callback_data=f"admin:set_group:{course_id}",
                    )
                ],
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
            f"📝 Description: {course.get('description','N/A')}\n"
            f"💰 Price: {course['currency']} {course['price']}\n"
            f"🖼 Preview: {'Yes ✅' if course.get('file_id') else 'No ❌'}\n"
            f"👥 Group ID: {group_line}\n"           # ← নতুন
            f"📌 Status: {status}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb,
        )
        await callback.answer()

    # ══════════════════════════════════════════════════════════
    #  Remove, Orders, Stats, Broadcast — same as before
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(
        filters.regex(r"^admin:remove:([a-f0-9]{24})$")
    )
    async def cb_remove_course(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)
        if not course:
            return await callback.answer("Course not found.", show_alert=True)
        await callback.message.edit_text(
            f"⚠️ **Confirm Removal**\n\n"
            f"**{course['name']}** remove করবেন?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_confirm_remove_inline(course_id),
        )
        await callback.answer()

    @app.on_callback_query(
        filters.regex(r"^admin:confirm_remove:([a-f0-9]{24})$")
    )
    async def cb_confirm_remove(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        course_id = callback.matches[0].group(1)
        ok        = await db.deactivate_course(course_id)
        if ok:
            await callback.message.edit_text(
                "✅ **Course removed!**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_back_panel_inline(),
            )
            await callback.answer("Removed!")
        else:
            await callback.answer("❌ Failed.", show_alert=True)

    @app.on_callback_query(filters.regex(r"^admin:orders$"))
    async def cb_admin_orders(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        orders = await db.get_all_pending_orders()
        if not orders:
            await callback.message.edit_text(
                "🧾 **Pending Orders**\n\nNo pending orders! 🎉",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_back_panel_inline(),
            )
            return await callback.answer()
        rows = []
        for o in orders:
            oid   = str(o["_id"])
            label = (
                f"#{oid[-6:]} — "
                f"{o.get('course_name','?')} — "
                f"{o.get('user_name','?')}"
            )
            rows.append([
                InlineKeyboardButton(
                    label,
                    callback_data=f"admin:order_detail:{oid}",
                )
            ])
        rows.append([
            InlineKeyboardButton(
                "🔙 Back", callback_data="admin:panel"
            )
        ])
        await callback.message.edit_text(
            f"🧾 **Pending Orders** ({len(orders)})",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(rows),
        )
        await callback.answer()

    @app.on_callback_query(
        filters.regex(r"^admin:order_detail:([a-f0-9]{24})$")
    )
    async def cb_order_detail(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        order_id = callback.matches[0].group(1)
        from bson import ObjectId
        order = await db.get_db().orders.find_one(
            {"_id": ObjectId(order_id)}
        )
        if not order:
            return await callback.answer("Not found.", show_alert=True)
        await callback.message.edit_text(
            f"🧾 **Order Details**\n\n"
            f"🆔 Order: `{order_id}`\n"
            f"👤 User: {order.get('user_name','?')} "
            f"(`{order.get('user_id','?')}`)\n"
            f"🎓 Course: {order.get('course_name','?')}\n"
            f"💰 Amount: {order.get('currency','')} "
            f"{order.get('amount','?')}\n"
            f"💳 Method: {order.get('method','?')}\n"
            f"📌 Status: {order.get('status','?').title()}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_order_actions_inline(order_id),
        )
        await callback.answer()

    # ══════════════════════════════════════════════════════════
    #  Approve Order ← OTL পাঠানো যোগ হয়েছে
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(
        filters.regex(r"^admin:approve_order:([a-f0-9]{24})$")
    )
    async def cb_approve_order(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        order_id = callback.matches[0].group(1)
        from bson import ObjectId
        order = await db.get_db().orders.find_one(
            {"_id": ObjectId(order_id)}
        )
        if not order:
            return await callback.answer("Not found.", show_alert=True)

        await db.update_order_status(order_id, "approved")

        await callback.message.edit_text(
            f"⏳ **Approving order `{order_id[-6:]}`...**\n\n"
            f"One-Time Invite Link তৈরি হচ্ছে...",
            parse_mode=ParseMode.MARKDOWN,
        )

        # ── OTL Generate & Send ────────────────────────────────
        from plugins.group_manager import approve_and_send_link
        await approve_and_send_link(
            client,
            order_id,
            callback.message.chat.id,
        )

        await callback.answer(
            MSG.ADMIN_ORDER_APPROVED_CONFIRM.format(
                order_id_short=order_id[-6:]
            )
        )

    # ══════════════════════════════════════════════════════════
    #  Reject Order
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(
        filters.regex(r"^admin:reject_order:([a-f0-9]{24})$")
    )
    async def cb_reject_order(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        order_id = callback.matches[0].group(1)
        from bson import ObjectId
        order = await db.get_db().orders.find_one(
            {"_id": ObjectId(order_id)}
        )
        if not order:
            return await callback.answer("Not found.", show_alert=True)
        await db.update_order_status(order_id, "rejected")
        await callback.message.edit_text(
            MSG.ADMIN_ORDER_REJECTED_CONFIRM.format(
                order_id_short=order_id[-6:]
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_back_panel_inline(),
        )
        try:
            await client.send_message(
                order["user_id"],
                MSG.PAYMENT_REJECTED.format(
                    course_name=order.get("course_name", "Unknown Course"),
                    order_id=order_id,
                    support=SUPPORT_USERNAME,
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass
        await callback.answer("Rejected.")

    @app.on_callback_query(filters.regex(r"^admin:stats$"))
    async def cb_stats(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        all_users   = await db.get_all_users()
        all_courses = await db.get_all_courses_admin()
        active_c    = [c for c in all_courses if c.get("is_active")]
        grp_c       = [c for c in all_courses if c.get("group_id")]
        pending_o   = await db.get_all_pending_orders()
        db_inst     = db.get_db()
        total_o     = await db_inst.orders.count_documents({})
        approved_o  = await db_inst.orders.count_documents(
            {"status": "approved"}
        )
        await callback.message.edit_text(
            f"📊 **Bot Statistics**\n\n"
            f"👥 Users:          **{len(all_users)}**\n"
            f"🎓 Courses:        **{len(all_courses)}** "
            f"({len(active_c)} active)\n"
            f"👥 With Group:     **{len(grp_c)}**\n"
            f"🧾 Total Orders:   **{total_o}**\n"
            f"✅ Approved:       **{approved_o}**\n"
            f"⏳ Pending:        **{len(pending_o)}**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_back_panel_inline(),
        )
        await callback.answer()

    @app.on_callback_query(filters.regex(r"^admin:broadcast$"))
    async def cb_broadcast_start(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        set_state(callback.from_user.id, States.ADMIN_BROADCAST)
        await callback.message.edit_text(
            "📢 **Broadcast**\n\nMessage পাঠান:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_cancel_inline(),
        )
        await callback.answer()

    # ══════════════════════════════════════════════════════════
    #  FSM Message Handler ← Step 10 & Set Group যোগ
    # ══════════════════════════════════════════════════════════

    @app.on_message(
        filters.private
        & ~filters.command(["start","admin","cancel","help","checkgroup"]),
        group=10,
    )
    async def admin_fsm_handler(client: Client, message: Message):
        uid = message.from_user.id
        if not is_admin(uid):
            return

        state = get_state(uid)

        _admin_states = {
            States.ADMIN_ADD_BRAND,
            States.ADMIN_ADD_BATCH,
            States.ADMIN_ADD_CATEGORY,
            States.ADMIN_ADD_SUBJECT,
            States.ADMIN_ADD_NAME,
            States.ADMIN_ADD_DESC,
            States.ADMIN_ADD_PRICE,
            States.ADMIN_ADD_CURRENCY,
            States.ADMIN_ADD_FILE,
            States.ADMIN_ADD_GROUP,    # ← নতুন
            States.ADMIN_SET_GROUP,    # ← নতুন
            States.ADMIN_BROADCAST,
        }
        if state not in _admin_states:
            return

        # Steps 1-8 same as before
        if state == States.ADMIN_ADD_BRAND:
            val = message.text.strip() if message.text else None
            if not val:
                return await message.reply_text(
                    "⚠️ Brand Name text হিসেবে দিন।",
                    reply_markup=admin_cancel_inline(),
                )
            update_data(uid, brand=val)
            set_state(uid, States.ADMIN_ADD_BATCH, get_data(uid))
            await message.reply_text(
                f"✅ Brand: **{val}**\n\n"
                f"➕ **Step 2/10** — **Batch Name:**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_cancel_inline(),
            )

        elif state == States.ADMIN_ADD_BATCH:
            val = message.text.strip() if message.text else None
            if not val:
                return await message.reply_text(
                    "⚠️ Batch Name text হিসেবে দিন।",
                    reply_markup=admin_cancel_inline(),
                )
            update_data(uid, batch=val)
            set_state(uid, States.ADMIN_ADD_CATEGORY, get_data(uid))
            await message.reply_text(
                f"✅ Batch: **{val}**\n\n"
                f"➕ **Step 3/10** — **Category:**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_cancel_inline(),
            )

        elif state == States.ADMIN_ADD_CATEGORY:
            val = message.text.strip() if message.text else None
            if not val:
                return await message.reply_text(
                    "⚠️ Category text হিসেবে দিন।",
                    reply_markup=admin_cancel_inline(),
                )
            update_data(uid, category=val)
            set_state(uid, States.ADMIN_ADD_SUBJECT, get_data(uid))
            await message.reply_text(
                f"✅ Category: **{val}**\n\n"
                f"➕ **Step 4/10** — **Subject Name:**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_cancel_inline(),
            )

        elif state == States.ADMIN_ADD_SUBJECT:
            val = message.text.strip() if message.text else None
            if not val:
                return await message.reply_text(
                    "⚠️ Subject text হিসেবে দিন।",
                    reply_markup=admin_cancel_inline(),
                )
            update_data(uid, subject=val)
            set_state(uid, States.ADMIN_ADD_NAME, get_data(uid))
            await message.reply_text(
                f"✅ Subject: **{val}**\n\n"
                f"➕ **Step 5/10** — **Course Name:**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_cancel_inline(),
            )

        elif state == States.ADMIN_ADD_NAME:
            val = message.text.strip() if message.text else None
            if not val:
                return await message.reply_text(
                    "⚠️ Course Name text হিসেবে দিন।",
                    reply_markup=admin_cancel_inline(),
                )
            update_data(uid, name=val)
            set_state(uid, States.ADMIN_ADD_DESC, get_data(uid))
            await message.reply_text(
                f"✅ Name: **{val}**\n\n"
                f"➕ **Step 6/10** — **Description:**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_cancel_inline(),
            )

        elif state == States.ADMIN_ADD_DESC:
            val = message.text.strip() if message.text else None
            if not val:
                return await message.reply_text(
                    "⚠️ Description text হিসেবে দিন।",
                    reply_markup=admin_cancel_inline(),
                )
            update_data(uid, description=val)
            set_state(uid, States.ADMIN_ADD_PRICE, get_data(uid))
            await message.reply_text(
                f"✅ Description saved.\n\n"
                f"➕ **Step 7/10** — **Price** (number only):",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_cancel_inline(),
            )

        elif state == States.ADMIN_ADD_PRICE:
            raw = message.text.strip() if message.text else ""
            try:
                price = float(raw)
            except ValueError:
                return await message.reply_text(
                    "⚠️ Valid price দিন। _e.g. `999`_",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=admin_cancel_inline(),
                )
            update_data(uid, price=price)
            set_state(uid, States.ADMIN_ADD_CURRENCY, get_data(uid))
            await message.reply_text(
                f"✅ Price: **{price}**\n\n"
                f"➕ **Step 8/10** — **Currency Code:**\n"
                f"_e.g. INR, BDT, USD, XTR_",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_cancel_inline(),
            )

        elif state == States.ADMIN_ADD_CURRENCY:
            val = (
                message.text.strip().upper()
                if message.text else None
            )
            if not val:
                return await message.reply_text(
                    "⚠️ Currency code দিন।",
                    reply_markup=admin_cancel_inline(),
                )
            update_data(uid, currency=val)
            set_state(uid, States.ADMIN_ADD_FILE, get_data(uid))
            await message.reply_text(
                f"✅ Currency: **{val}**\n\n"
                f"➕ **Step 9/10** — **Preview Image** পাঠান:\n"
                f"_(Optional — Skip করতে পারেন)_",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_skip_inline(),
            )

        elif state == States.ADMIN_ADD_FILE:
            file_id = None
            if message.photo:
                file_id = message.photo.file_id
            elif message.document:
                file_id = message.document.file_id

            update_data(uid, file_id=file_id)
            set_state(uid, States.ADMIN_ADD_GROUP, get_data(uid))

            await message.reply_text(
                f"✅ {'Image saved.' if file_id else 'No image.'}\n\n"
                f"➕ **Step 10/10** — **Private Group/Channel ID:**\n\n"
                f"📌 Group ID কীভাবে পাবেন:\n"
                f"• `/checkgroup -1001234567890` দিন\n"
                f"• ID সাধারণত `-100` দিয়ে শুরু হয়\n\n"
                f"_e.g. `-1001234567890`_\n\n"
                f"⏭ Group ছাড়া save করতে **Skip** করুন।",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=_group_skip_kb(),
            )

        # ── Step 10: Group ID (Add Course flow) ── ← নতুন
        elif state == States.ADMIN_ADD_GROUP:
            raw = message.text.strip() if message.text else ""
            try:
                group_id = int(raw)
            except ValueError:
                return await message.reply_text(
                    "⚠️ Valid Group ID দিন।\n"
                    "_e.g. `-1001234567890`_\n\n"
                    "অথবা Skip করুন।",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=_group_skip_kb(),
                )

            # Bot admin check করো
            checking = await message.reply_text(
                f"⏳ Group `{group_id}` check হচ্ছে...",
                parse_mode=ParseMode.MARKDOWN,
            )

            from plugins.group_manager import check_bot_is_admin
            result = await check_bot_is_admin(client, group_id)

            if result["error"]:
                update_data(
                    uid,
                    group_id=group_id,
                    group_checked=False,
                    group_username=None,
                )
                await checking.edit_text(
                    f"⚠️ **Group check এ সমস্যা:**\n"
                    f"`{result['error']}`\n\n"
                    f"Group ID save হয়েছে কিন্তু "
                    f"Bot এখনো admin না।\n\n"
                    f"Course save করবেন?",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=_save_anyway_kb(),
                )
                return

            if result["is_admin"] and result["can_invite"]:
                update_data(
                    uid,
                    group_id=group_id,
                    group_checked=True,
                    group_username=None,
                )
                data      = get_data(uid)
                course_id = await _persist_course(data)
                clear_state(uid)

                LOGGER.info(
                    f"[AddCourse] admin={uid} "
                    f"course_id={course_id} "
                    f"group={group_id} verified=True"
                )

                await checking.edit_text(
                    f"✅ **Group verified & Course Saved!**\n\n"
                    f"🆔 Course ID: `{course_id}`\n"
                    f"🎓 Name: {data.get('name')}\n"
                    f"👥 Group: `{group_id}` ✅\n"
                    f"🔗 OTL: Ready to generate!",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=admin_panel_inline(),
                )
            else:
                # Admin কিন্তু permission নেই
                update_data(
                    uid,
                    group_id=group_id,
                    group_checked=False,
                    group_username=None,
                )
                issue = (
                    "Bot admin না"
                    if not result["is_admin"]
                    else "Invite permission নেই"
                )
                await checking.edit_text(
                    f"⚠️ **{issue}!**\n\n"
                    f"Group ID: `{group_id}`\n\n"
                    f"**সমাধান:**\n"
                    f"1. Group → Admin settings\n"
                    f"2. Bot কে Admin করুন\n"
                    f"3. 'Invite Users' permission দিন\n\n"
                    f"তবুও এই Group ID দিয়ে save করবেন?",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=_save_anyway_kb(),
                )

        # ── Set Group for Existing Course ── ← নতুন
        elif state == States.ADMIN_SET_GROUP:
            raw = message.text.strip() if message.text else ""
            try:
                group_id = int(raw)
            except ValueError:
                return await message.reply_text(
                    "⚠️ Valid Group ID দিন।\n"
                    "_e.g. `-1001234567890`_",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=admin_cancel_inline(),
                )

            data      = get_data(uid)
            course_id = data.get("course_id")

            checking = await message.reply_text(
                f"⏳ Group `{group_id}` check হচ্ছে...",
                parse_mode=ParseMode.MARKDOWN,
            )

            from plugins.group_manager import check_bot_is_admin
            result = await check_bot_is_admin(client, group_id)

            checked = (
                result["is_admin"] and result["can_invite"]
                and not result["error"]
            )

            await db.set_course_group(
                course_id, group_id,
                group_checked=checked,
            )
            clear_state(uid)

            LOGGER.info(
                f"[SetGroup] admin={uid} "
                f"course={course_id} group={group_id} "
                f"verified={checked}"
            )

            status_text = (
                "✅ Bot verified — OTL ready!"
                if checked
                else f"⚠️ {result.get('error','Bot admin নয়')} — "
                     f"পরে fix করুন"
            )

            await checking.edit_text(
                f"{'✅' if checked else '⚠️'} "
                f"**Group {'Set' if checked else 'Set (unverified)'}!**\n\n"
                f"📦 Course: `{data.get('course_name')}`\n"
                f"👥 Group ID: `{group_id}`\n"
                f"📌 Status: {status_text}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_back_panel_inline(),
            )

        elif state == States.ADMIN_BROADCAST:
            await _do_broadcast(client, message, uid)

    # ══════════════════════════════════════════════════════════
    #  Save Anyway callback ← নতুন
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(
        filters.regex(r"^admin:save_anyway$")
    )
    async def cb_save_anyway(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        uid  = callback.from_user.id
        data = get_data(uid)

        if get_state(uid) not in (
            States.ADMIN_ADD_GROUP,
            States.ADMIN_ADD_FILE,
        ):
            return await callback.answer(
                "State expired.", show_alert=True
            )

        course_id = await _persist_course(data)
        clear_state(uid)

        LOGGER.info(
            f"[AddCourse] admin={uid} "
            f"course_id={course_id} "
            f"group={data.get('group_id')} "
            f"verified=False (saved anyway)"
        )

        await callback.message.edit_text(
            f"✅ **Course Saved** _(group unverified)_\n\n"
            f"🆔 ID: `{course_id}`\n"
            f"🎓 Name: {data.get('name')}\n"
            f"👥 Group: `{data.get('group_id')}` ⚠️\n\n"
            f"Bot কে Group এ admin করার পর:\n"
            f"`/checkgroup {data.get('group_id')}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_panel_inline(),
        )
        await callback.answer("Saved!")


# ════════════════════════════════════════════════════════════
#  Keyboard helpers (module level)
# ════════════════════════════════════════════════════════════

def _group_skip_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⏭ Group ছাড়াই Save করুন",
                    callback_data="admin:skip_group",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="admin:cancel",
                )
            ],
        ]
    )


def _save_anyway_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💾 তবুও Save করুন",
                    callback_data="admin:save_anyway",
                )
            ],
            [
                InlineKeyboardButton(
                    "⏭ Group ছাড়াই Save",
                    callback_data="admin:skip_group",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="admin:cancel",
                )
            ],
        ]
    )
