# plugins/admin_panel.py
# Copyright @YourChannel

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
#  Admin Panel Inline Keyboard
# ════════════════════════════════════════════════════════════

def _admin_panel_kb() -> InlineKeyboardMarkup:
    """Full admin panel keyboard"""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("➕ Add Course",      callback_data="admin:add_course"),
                InlineKeyboardButton("📋 List Courses",    callback_data="admin:list_courses"),
            ],
            [
                InlineKeyboardButton("🧾 Pending Orders",  callback_data="admin:orders"),
                InlineKeyboardButton("📊 Stats",           callback_data="admin:stats"),
            ],
            [
                InlineKeyboardButton("📢 Broadcast",       callback_data="admin:broadcast"),
                InlineKeyboardButton("🎛 Button Editor",   callback_data="admin:button_editor"),
            ],
            [
                InlineKeyboardButton("☎️ Helpline Edit",   callback_data="admin:helpline_edit"),
                InlineKeyboardButton("🚫 Banned Users",    callback_data="admin:banned"),
            ],
            [InlineKeyboardButton("❌ Close",              callback_data="admin:close")],
        ]
    )


# ════════════════════════════════════════════════════════════
#  Helper functions
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
            "group_id":       data.get("group_id"),
            "group_username": data.get("group_username"),
            "group_checked":  data.get("group_checked", False),
            "course_code":    data.get("course_code"),
        }
    )


async def _do_broadcast(
    client: Client, message: Message, uid: int
) -> None:
    all_users = await db.get_all_users()
    sent = failed = 0

    status = await message.reply_text(
        MSG.BROADCAST_SENDING.format(total_users=len(all_users)),
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

    @app.on_callback_query(filters.regex(r"^admin:panel$"))
    async def cb_admin_panel(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        clear_state(callback.from_user.id)
        await callback.message.edit_text(
            "🛠 **Admin Panel**\n\nChoose an action:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_admin_panel_kb(),
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
            reply_markup=_admin_panel_kb(),
        )
        await callback.answer("Cancelled.")

    @app.on_callback_query(filters.regex(r"^admin:add_course$"))
    async def cb_add_course_start(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        set_state(callback.from_user.id, States.ADMIN_ADD_BRAND)
        await callback.message.edit_text(
            "➕ **Add New Course** — Step 1 / 11\n\n"
            "Type the **Brand / Institute Name**:\n"
            "_e.g. Physics Wallah, Unacademy_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_cancel_inline(),
        )
        await callback.answer()

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
            "➕ **Step 10 / 11** — **Private Group/Channel ID** দিন:\n\n"
            "ID সাধারণত `-100` দিয়ে শুরু হয়\n"
            "_e.g. `-1001234567890`_\n\n"
            "⏭ Group ছাড়া save করতে **Skip** করুন।",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_group_skip_kb(),
        )
        await callback.answer()

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
        set_state(uid, States.ADMIN_ADD_COURSE_CODE, data)

        await callback.message.edit_text(
            "⏭ Group skip করা হয়েছে।\n\n"
            "➕ **Step 11 / 11** — **Course Code** দিন:\n\n"
            "📌 এই Code ব্যবহার করে User payment request করবে।\n"
            "_e.g. PHY2024, MATH101_\n\n"
            "⚠️ Code অবশ্যই unique হতে হবে।\n\n"
            "⏭ Course Code ছাড়া save করতে **Skip** করুন।",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_course_code_skip_kb(),
        )
        await callback.answer()

    @app.on_callback_query(filters.regex(r"^admin:skip_course_code$"))
    async def cb_skip_course_code(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        uid = callback.from_user.id
        if get_state(uid) not in (
            States.ADMIN_ADD_COURSE_CODE,
            States.ADMIN_ADD_GROUP,
        ):
            return await callback.answer("Nothing to skip.", show_alert=True)

        data              = get_data(uid)
        data["course_code"] = None
        course_id         = await _persist_course(data)
        clear_state(uid)

        LOGGER.info(f"[AddCourse] admin={uid} course_id={course_id} (no code)")

        await callback.message.edit_text(
            f"✅ **Course Added!** _(Course Code ছাড়া)_\n\n"
            f"🆔 ID: `{course_id}`\n"
            f"🏷 Brand: {data.get('brand')}\n"
            f"🎓 Name: {data.get('name')}\n"
            f"💡 Course Code পরে List Courses → Course → Set Code থেকে যোগ করুন।",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_admin_panel_kb(),
        )
        await callback.answer("Course saved!")

    @app.on_callback_query(filters.regex(r"^admin:set_code:([a-f0-9]{24})$"))
    async def cb_set_code_start(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)
        if not course:
            return await callback.answer("Course not found.", show_alert=True)

        uid = callback.from_user.id
        _code_set_state[uid] = {"course_id": course_id, "course_name": course["name"]}

        current = course.get("course_code", "❌ নেই")
        await callback.message.edit_text(
            f"🏷 **Course Code Set করুন**\n\n"
            f"📦 Course: `{course['name']}`\n"
            f"🔢 Current Code: `{current}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"নতুন Course Code দিন:\n"
            f"_e.g. PHY2024, MATH101_\n\n"
            f"⚠️ Code অবশ্যই unique হতে হবে।",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_cancel_inline(),
        )
        await callback.answer()

    @app.on_callback_query(filters.regex(r"^admin:set_group:([a-f0-9]{24})$"))
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
            f"Private Group/Channel এর **ID** পাঠান:\n"
            f"_e.g. `-1001234567890`_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_cancel_inline(),
        )
        await callback.answer()

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
            f"📋 **All Courses** ({len(courses)} total)",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_course_list_inline(courses),
        )
        await callback.answer()

    @app.on_callback_query(filters.regex(r"^admin:view:([a-f0-9]{24})$"))
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
            f"`{group_id}` {'✅' if grp_check else '⚠️'}"
            if group_id
            else "❌ নেই"
        )
        course_code = course.get("course_code") or "❌ নেই"

        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🏷 Course Code Set",
                        callback_data=f"admin:set_code:{course_id}",
                    ),
                    InlineKeyboardButton(
                        "👥 Group Set",
                        callback_data=f"admin:set_group:{course_id}",
                    ),
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
            f"🏷 Course Code: `{course_code}`\n"
            f"👥 Group ID: {group_line}\n"
            f"📌 Status: {status}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb,
        )
        await callback.answer()

    @app.on_callback_query(filters.regex(r"^admin:remove:([a-f0-9]{24})$"))
    async def cb_remove_course(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)
        if not course:
            return await callback.answer("Course not found.", show_alert=True)
        await callback.message.edit_text(
            f"⚠️ **Confirm Removal**\n\n**{course['name']}** remove করবেন?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_confirm_remove_inline(course_id),
        )
        await callback.answer()

    @app.on_callback_query(filters.regex(r"^admin:confirm_remove:([a-f0-9]{24})$"))
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
                InlineKeyboardButton(label, callback_data=f"admin:order_detail:{oid}")
            ])
        rows.append([InlineKeyboardButton("🔙 Back", callback_data="admin:panel")])
        await callback.message.edit_text(
            f"🧾 **Pending Orders** ({len(orders)})",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(rows),
        )
        await callback.answer()

    @app.on_callback_query(filters.regex(r"^admin:order_detail:([a-f0-9]{24})$"))
    async def cb_order_detail(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        order_id = callback.matches[0].group(1)
        from bson import ObjectId
        order = await db.get_db().orders.find_one({"_id": ObjectId(order_id)})
        if not order:
            return await callback.answer("Not found.", show_alert=True)
        tx_info = f"\n🔢 **TX ID:** `{order.get('tx_id','N/A')}`" if order.get("tx_id") else ""
        phone_info = f"\n📱 **Phone:** `{order.get('phone_number','N/A')}`" if order.get("phone_number") else ""
        code_info  = f"\n🏷 **Course Code:** `{order.get('course_code','N/A')}`" if order.get("course_code") else ""
        await callback.message.edit_text(
            f"🧾 **Order Details**\n\n"
            f"🆔 Order: `{order_id}`\n"
            f"👤 User: {order.get('user_name','?')} (`{order.get('user_id','?')}`)\n"
            f"🎓 Course: {order.get('course_name','?')}"
            f"{code_info}\n"
            f"💰 Amount: {order.get('currency','')} {order.get('amount','?')}\n"
            f"💳 Method: {order.get('method','?')}"
            f"{phone_info}"
            f"{tx_info}\n"
            f"📌 Status: {order.get('status','?').title()}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_order_actions_inline(order_id),
        )
        await callback.answer()

    @app.on_callback_query(filters.regex(r"^admin:approve_order:([a-f0-9]{24})$"))
    async def cb_approve_order(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        order_id = callback.matches[0].group(1)
        from bson import ObjectId
        order = await db.get_db().orders.find_one({"_id": ObjectId(order_id)})
        if not order:
            return await callback.answer("Not found.", show_alert=True)

        await db.update_order_status(order_id, "approved")

        await callback.message.edit_text(
            f"⏳ **Approving order `{order_id[-6:]}`...**\n\nOne-Time Invite Link তৈরি হচ্ছে...",
            parse_mode=ParseMode.MARKDOWN,
        )

        from plugins.group_manager import approve_and_send_link
        await approve_and_send_link(client, order_id, callback.message.chat.id)

        await callback.answer(
            MSG.ADMIN_ORDER_APPROVED_CONFIRM.format(order_id_short=order_id[-6:])
        )

    @app.on_callback_query(filters.regex(r"^admin:reject_order:([a-f0-9]{24})$"))
    async def cb_reject_order(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)
        order_id = callback.matches[0].group(1)
        from bson import ObjectId
        order = await db.get_db().orders.find_one({"_id": ObjectId(order_id)})
        if not order:
            return await callback.answer("Not found.", show_alert=True)
        await db.update_order_status(order_id, "rejected")
        await callback.message.edit_text(
            MSG.ADMIN_ORDER_REJECTED_CONFIRM.format(order_id_short=order_id[-6:]),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_back_panel_inline(),
        )
        try:
            await client.send_message(
                order["user_id"],
                MSG.PAYMENT_REJECTED.format(
                    course_name=order.get("course_name", "Unknown"),
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
        stats = await db.get_full_stats()
        await callback.message.edit_text(
            f"📊 **Bot Statistics**\n\n"
            f"👥 Total Users:     **{stats['total_users']}**\n"
            f"🎓 Courses:         **{stats['total_courses']}** ({stats['active_courses']} active)\n"
            f"👥 With Group:      **{stats['courses_w_group']}**\n"
            f"🧾 Total Orders:    **{stats['total_orders']}**\n"
            f"✅ Approved:        **{stats['approved_orders']}**\n"
            f"⏳ Pending:         **{stats['pending_orders']}**\n"
            f"❌ Rejected:        **{stats['rejected_orders']}**\n"
            f"📸 Pending Proofs:  **{stats['pending_proofs']}**\n"
            f"🚫 Banned Users:    **{stats['banned_users']}**",
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

    @app.on_callback_query(filters.regex(r"^admin:helpline_edit$"))
    async def cb_helpline_edit(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        uid = callback.from_user.id
        set_state(uid, States.IDLE)
        _helpline_edit_state[uid] = {"step": "edit_msg"}

        current = await db.get_setting("helpline_message", default="(not set)")
        support = await db.get_setting("support_username", default=SUPPORT_USERNAME)

        await callback.message.edit_text(
            f"☎️ **Helpline Edit**\n\n"
            f"**Current Support Username:** `{support}`\n\n"
            f"**Current Helpline Message:**\n{current[:300]}...\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"নতুন **Support Username** দিন (e.g. @mybot):\n"
            f"অথবা **Skip** করুন।",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("⏭ Skip (Username)", callback_data="admin:helpline_skip_user")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="admin:panel")],
                ]
            ),
        )
        await callback.answer()

    @app.on_callback_query(filters.regex(r"^admin:helpline_skip_user$"))
    async def cb_helpline_skip_user(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        uid = callback.from_user.id
        state = _helpline_edit_state.get(uid, {})
        state["step"] = "edit_msg"
        _helpline_edit_state[uid] = state

        await callback.message.edit_text(
            "📝 **Helpline Message দিন:**\n\n"
            "_(Markdown supported)_\n\n"
            "❌ বাতিল করতে /cancel দিন।",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ Cancel", callback_data="admin:panel")]]
            ),
        )
        await callback.answer()

    @app.on_callback_query(filters.regex(r"^admin:banned$"))
    async def cb_admin_banned(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        banned = await db.get_all_banned()
        if not banned:
            await callback.message.edit_text(
                "🚫 **Banned Users**\n\nকোনো Banned User নেই।",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_back_panel_inline(),
            )
            return await callback.answer()

        rows = []
        for b in banned[:20]:
            uid_  = b["user_id"]
            rows.append(
                [
                    InlineKeyboardButton(f"🚫 {uid_}", callback_data=f"admin:baninfo:{uid_}"),
                    InlineKeyboardButton("✅ Unban", callback_data=f"admin:unban:{uid_}"),
                ]
            )
        rows.append([InlineKeyboardButton("🔙 ফিরুন", callback_data="admin:panel")])

        await callback.message.edit_text(
            f"🚫 **Banned Users** ({len(banned)} জন)",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(rows),
        )
        await callback.answer()

    @app.on_callback_query(filters.regex(r"^admin:unban:(\d+)$"))
    async def cb_admin_unban(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        user_id = int(callback.matches[0].group(1))
        ok      = await db.unban_user(user_id)

        if ok:
            try:
                await client.send_message(
                    user_id,
                    "✅ **আপনার Ban তুলে নেওয়া হয়েছে।**\n\nআবার Bot ব্যবহার করতে পারবেন।",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass
            await callback.answer(f"✅ User {user_id} unbanned!")
            banned = await db.get_all_banned()
            if not banned:
                await callback.message.edit_text(
                    "🚫 **Banned Users**\n\nকোনো Banned User নেই।",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=admin_back_panel_inline(),
                )
            else:
                rows = []
                for b in banned[:20]:
                    uid_  = b["user_id"]
                    rows.append(
                        [
                            InlineKeyboardButton(f"🚫 {uid_}", callback_data=f"admin:baninfo:{uid_}"),
                            InlineKeyboardButton("✅ Unban", callback_data=f"admin:unban:{uid_}"),
                        ]
                    )
                rows.append([InlineKeyboardButton("🔙 ফিরুন", callback_data="admin:panel")])
                await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(rows))
        else:
            await callback.answer("❌ Unban ব্যর্থ!", show_alert=True)

    @app.on_callback_query(filters.regex(r"^admin:save_anyway$"))
    async def cb_save_anyway(client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        uid  = callback.from_user.id
        data = get_data(uid)

        if get_state(uid) not in (
            States.ADMIN_ADD_GROUP,
            States.ADMIN_ADD_FILE,
            States.ADMIN_ADD_COURSE_CODE,
        ):
            return await callback.answer("State expired.", show_alert=True)

        course_id = await _persist_course(data)
        clear_state(uid)

        LOGGER.info(f"[AddCourse] admin={uid} course_id={course_id} group={data.get('group_id')} verified=False")

        await callback.message.edit_text(
            f"✅ **Course Saved** _(group unverified)_\n\n"
            f"🆔 ID: `{course_id}`\n"
            f"🎓 Name: {data.get('name')}\n"
            f"👥 Group: `{data.get('group_id')}` ⚠️",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_admin_panel_kb(),
        )
        await callback.answer("Saved!")

    @app.on_message(
        filters.private & ~filters.command(["start", "admin", "cancel", "help", "checkgroup"]),
        group=10,
    )
    async def admin_fsm_handler(client: Client, message: Message):
        uid = message.from_user.id
        if not is_admin(uid):
            return

        code_state = _code_set_state.get(uid)
        if code_state:
            raw = message.text.strip().upper() if message.text else ""
            if not raw:
                return await message.reply_text("⚠️ Course Code text হিসেবে দিন।", reply_markup=admin_cancel_inline())
            existing = await db.get_course_by_code(raw)
            if existing and str(existing["_id"]) != code_state["course_id"]:
                return await message.reply_text(f"❌ `{raw}` Code টি ইতিমধ্যে অন্য Course এ ব্যবহার হচ্ছে!", parse_mode=ParseMode.MARKDOWN)
            ok = await db.set_course_code(code_state["course_id"], raw)
            _code_set_state.pop(uid, None)
            if ok:
                await message.reply_text(f"✅ **Course Code Set হয়েছে!**\n\n📦 Course: `{code_state['course_name']}`\n🏷 Code: `{raw}`", parse_mode=ParseMode.MARKDOWN, reply_markup=admin_back_panel_inline())
            else:
                await message.reply_text("❌ Code set ব্যর্থ হয়েছে।")
            return

        hl_state = _helpline_edit_state.get(uid)
        if hl_state:
            step = hl_state.get("step")
            text = message.text.strip() if message.text else ""
            if step == "edit_username":
                await db.set_setting("support_username", text)
                hl_state["step"] = "edit_msg"
                return await message.reply_text(f"✅ **Support Username আপডেট:** `{text}`\n\nএখন **Helpline Message** দিন:", parse_mode=ParseMode.MARKDOWN)
            elif step == "edit_msg":
                await db.set_setting("helpline_message", text)
                _helpline_edit_state.pop(uid, None)
                return await message.reply_text("✅ **Helpline Message আপডেট হয়েছে!**", parse_mode=ParseMode.MARKDOWN, reply_markup=admin_back_panel_inline())

        state = get_state(uid)
        _admin_states = {
            States.ADMIN_ADD_BRAND, States.ADMIN_ADD_BATCH, States.ADMIN_ADD_CATEGORY,
            States.ADMIN_ADD_SUBJECT, States.ADMIN_ADD_NAME, States.ADMIN_ADD_DESC,
            States.ADMIN_ADD_PRICE, States.ADMIN_ADD_CURRENCY, States.ADMIN_ADD_FILE,
            States.ADMIN_ADD_GROUP, States.ADMIN_ADD_COURSE_CODE, States.ADMIN_SET_GROUP,
            States.ADMIN_BROADCAST,
        }
        if state not in _admin_states:
            return

        if state == States.ADMIN_ADD_BRAND:
            val = message.text.strip() if message.text else None
            if not val: return await message.reply_text("⚠️ Brand Name text হিসেবে দিন।", reply_markup=admin_cancel_inline())
            update_data(uid, brand=val)
            set_state(uid, States.ADMIN_ADD_BATCH, get_data(uid))
            await message.reply_text(f"✅ Brand: **{val}**\n\n➕ **Step 2/11** — **Batch Name:**", parse_mode=ParseMode.MARKDOWN, reply_markup=admin_cancel_inline())

        elif state == States.ADMIN_ADD_BATCH:
            val = message.text.strip() if message.text else None
            if not val: return await message.reply_text("⚠️ Batch Name text হিসেবে দিন।", reply_markup=admin_cancel_inline())
            update_data(uid, batch=val)
            set_state(uid, States.ADMIN_ADD_CATEGORY, get_data(uid))
            await message.reply_text(f"✅ Batch: **{val}**\n\n➕ **Step 3/11** — **Category:**", parse_mode=ParseMode.MARKDOWN, reply_markup=admin_cancel_inline())

        elif state == States.ADMIN_ADD_CATEGORY:
            val = message.text.strip() if message.text else None
            if not val: return await message.reply_text("⚠️ Category text হিসেবে দিন।", reply_markup=admin_cancel_inline())
            update_data(uid, category=val)
            set_state(uid, States.ADMIN_ADD_SUBJECT, get_data(uid))
            await message.reply_text(f"✅ Category: **{val}**\n\n➕ **Step 4/11** — **Subject Name:**", parse_mode=ParseMode.MARKDOWN, reply_markup=admin_cancel_inline())

        elif state == States.ADMIN_ADD_SUBJECT:
            val = message.text.strip() if message.text else None
            if not val: return await message.reply_text("⚠️ Subject text হিসেবে দিন।", reply_markup=admin_cancel_inline())
            update_data(uid, subject=val)
            set_state(uid, States.ADMIN_ADD_NAME, get_data(uid))
            await message.reply_text(f"✅ Subject: **{val}**\n\n➕ **Step 5/11** — **Course Name:**", parse_mode=ParseMode.MARKDOWN, reply_markup=admin_cancel_inline())

        elif state == States.ADMIN_ADD_NAME:
            val = message.text.strip() if message.text else None
            if not val: return await message.reply_text("⚠️ Course Name text হিসেবে দিন।", reply_markup=admin_cancel_inline())
            update_data(uid, name=val)
            set_state(uid, States.ADMIN_ADD_DESC, get_data(uid))
            await message.reply_text(f"✅ Name: **{val}**\n\n➕ **Step 6/11** — **Description:**", parse_mode=ParseMode.MARKDOWN, reply_markup=admin_cancel_inline())

        elif state == States.ADMIN_ADD_DESC:
            val = message.text.strip() if message.text else None
            if not val: return await message.reply_text("⚠️ Description text হিসেবে দিন।", reply_markup=admin_cancel_inline())
            update_data(uid, description=val)
            set_state(uid, States.ADMIN_ADD_PRICE, get_data(uid))
            await message.reply_text(f"✅ Description saved.\n\n➕ **Step 7/11** — **Price** (number only):", parse_mode=ParseMode.MARKDOWN, reply_markup=admin_cancel_inline())

        elif state == States.ADMIN_ADD_PRICE:
            raw = message.text.strip() if message.text else ""
            try: price = float(raw)
            except ValueError: return await message.reply_text("⚠️ Valid price দিন।", parse_mode=ParseMode.MARKDOWN, reply_markup=admin_cancel_inline())
            update_data(uid, price=price)
            set_state(uid, States.ADMIN_ADD_CURRENCY, get_data(uid))
            await message.reply_text(f"✅ Price: **{price}**\n\n➕ **Step 8/11** — **Currency Code:**", parse_mode=ParseMode.MARKDOWN, reply_markup=admin_cancel_inline())

        elif state == States.ADMIN_ADD_CURRENCY:
            val = message.text.strip().upper() if message.text else None
            if not val: return await message.reply_text("⚠️ Currency code দিন।", reply_markup=admin_cancel_inline())
            update_data(uid, currency=val)
            set_state(uid, States.ADMIN_ADD_FILE, get_data(uid))
            await message.reply_text(f"✅ Currency: **{val}**\n\n➕ **Step 9/11** — **Preview Image** পাঠান:", parse_mode=ParseMode.MARKDOWN, reply_markup=admin_skip_inline())

        elif state == States.ADMIN_ADD_FILE:
            file_id = message.photo.file_id if message.photo else (message.document.file_id if message.document else None)
            update_data(uid, file_id=file_id)
            set_state(uid, States.ADMIN_ADD_GROUP, get_data(uid))
            await message.reply_text(f"✅ Image saved.\n\n➕ **Step 10/11** — **Private Group ID:**", parse_mode=ParseMode.MARKDOWN, reply_markup=_group_skip_kb())

        elif state == States.ADMIN_ADD_GROUP:
            raw = message.text.strip() if message.text else ""
            try: group_id = int(raw)
            except ValueError: return await message.reply_text("⚠️ Valid Group ID দিন।", parse_mode=ParseMode.MARKDOWN, reply_markup=_group_skip_kb())
            checking = await message.reply_text(f"⏳ Group `{group_id}` check হচ্ছে...", parse_mode=ParseMode.MARKDOWN)
            from plugins.group_manager import check_bot_is_admin
            result = await check_bot_is_admin(client, group_id)
            if result["error"]:
                update_data(uid, group_id=group_id, group_checked=False)
                set_state(uid, States.ADMIN_ADD_COURSE_CODE, get_data(uid))
                return await checking.edit_text(f"⚠️ Group check এ সমস্যা: `{result['error']}`\n\n➕ **Step 11/11** — **Course Code** দিন:", reply_markup=_course_code_skip_kb())
            verified = result["is_admin"] and result["can_invite"]
            update_data(uid, group_id=group_id, group_checked=verified)
            set_state(uid, States.ADMIN_ADD_COURSE_CODE, get_data(uid))
            await checking.edit_text(f"{'✅' if verified else '⚠️'} Group: `{group_id}` verified!\n\n➕ **Step 11/11** — **Course Code** দিন:", reply_markup=_course_code_skip_kb())

        elif state == States.ADMIN_ADD_COURSE_CODE:
            raw = message.text.strip().upper() if message.text else ""
            if not raw: return await message.reply_text("⚠️ Course Code দিন।", reply_markup=_course_code_skip_kb())
            existing = await db.get_course_by_code(raw)
            if existing: return await message.reply_text(f"❌ `{raw}` Code ইতিমধ্যে ব্যবহার হচ্ছে!", reply_markup=_course_code_skip_kb())
            data = get_data(uid)
            data["course_code"] = raw
            course_id = await _persist_course(data)
            clear_state(uid)
            await message.reply_text(f"✅ **Course Added Successfully!**\n\n🆔 ID: `{course_id}`\n🏷 Code: `{raw}`", reply_markup=_admin_panel_kb())

        elif state == States.ADMIN_SET_GROUP:
            raw = message.text.strip() if message.text else ""
            try: group_id = int(raw)
            except ValueError: return await message.reply_text("⚠️ Valid Group ID দিন।", reply_markup=admin_cancel_inline())
            data = get_data(uid)
            course_id = data.get("course_id")
            checking = await message.reply_text(f"⏳ Group `{group_id}` check হচ্ছে...", parse_mode=ParseMode.MARKDOWN)
            from plugins.group_manager import check_bot_is_admin
            result = await check_bot_is_admin(client, group_id)
            checked = result["is_admin"] and result["can_invite"] and not result["error"]
            await db.set_course_group(course_id, group_id, group_checked=checked)
            clear_state(uid)
            await checking.edit_text(
                f"{'✅' if checked else '⚠️'} **Group Set!**\n\n"
                f"📦 Course: `{data.get('course_name')}`\n"
                f"👥 Group ID: `{group_id}`\n"
                f"📌 Status: {'✅ Verified' if checked else f'⚠️ {result.get(\"error\", \"Bot admin নয়\")}'}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_back_panel_inline(),
            )

        elif state == States.ADMIN_BROADCAST:
            await _do_broadcast(client, message, uid)

    LOGGER.info("[AdminPanel] Plugin loaded ✅")


# ════════════════════════════════════════════════════════════
#  Module-level state stores
# ════════════════════════════════════════════════════════════
_code_set_state:      dict = {}
_helpline_edit_state: dict = {}


# ════════════════════════════════════════════════════════════
#  Keyboard helpers
# ════════════════════════════════════════════════════════════

def _group_skip_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⏭ Group ছাড়াই Continue", callback_data="admin:skip_group")],
            [InlineKeyboardButton("❌ Cancel",               callback_data="admin:cancel")],
        ]
    )


def _course_code_skip_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⏭ Code ছাড়াই Save করুন", callback_data="admin:skip_course_code")],
            [InlineKeyboardButton("❌ Cancel",               callback_data="admin:cancel")],
        ]
    )


def _save_anyway_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💾 তবুও Save করুন",     callback_data="admin:save_anyway")],
            [InlineKeyboardButton("⏭ Group ছাড়াই Save",   callback_data="admin:skip_group")],
            [InlineKeyboardButton("❌ Cancel",              callback_data="admin:cancel")],
        ]
    )
