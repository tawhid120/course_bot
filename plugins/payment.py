# plugins/payment.py
# Copyright @YourChannel
# ─────────────────────────────────────────────────────────────
# Payment + Proof Submission System
#
# Flow (Manual Payment — bKash / Nagad):
#   Buy Now → Payment Method (bKash বা Nagad)
#     → Instructions দেখানো
#       → Phone Number চাওয়া (আবশ্যিক)
#         → Screenshot চাওয়া (ঐচ্ছিক — skip করা যাবে)
#           → Admin কে notify করো
#             → Admin Approve/Reject করে
#               → Membership Card পাঠানো
# ─────────────────────────────────────────────────────────────

from datetime import datetime

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import db
from config import (
    ADMIN_IDS,
    ADMIN_USERNAME,
    BKASH_NUMBER,
    NAGAD_NUMBER,
    SUPPORT_USERNAME,
)
from misc import (
    States,
    clear_state,
    get_data,
    get_state,
    main_menu_inline,
    set_state,
    update_data,
)
from misc.keyboards import (
    admin_proof_actions_kb,
    payment_methods_kb,
    proof_cancel_kb,
    proof_phone_kb,
    proof_screenshot_kb,
    admin_back_panel_inline,
)
from misc.messages import MSG
from utils import LOGGER

# ── In-memory proof state store ───────────────────────────────
_proof_state: dict = {}


# ═════════════════════════════════════════════════════════════
#  TEXT HELPERS
# ═════════════════════════════════════════════════════════════

def _payment_menu_text(course: dict) -> str:
    return MSG.PAYMENT_METHOD_SELECT.format(
        name     = course["name"],
        currency = course["currency"],
        price    = course["price"],
        support  = SUPPORT_USERNAME,
    )


def _bkash_text(course: dict, user_id: int) -> str:
    return MSG.PAYMENT_BKASH.format(
        course_name  = course["name"],
        price        = course["price"],
        currency     = course["currency"],
        bkash_number = BKASH_NUMBER,
        user_id      = user_id,
        support      = SUPPORT_USERNAME,
    )


def _nagad_text(course: dict, user_id: int) -> str:
    return MSG.PAYMENT_NAGAD.format(
        course_name  = course["name"],
        price        = course["price"],
        currency     = course["currency"],
        nagad_number = NAGAD_NUMBER,
        user_id      = user_id,
        support      = SUPPORT_USERNAME,
    )


# ═════════════════════════════════════════════════════════════
#  HELPER — Admin কে Purchase Log পাঠানো
# ═════════════════════════════════════════════════════════════

async def _notify_admin_purchase(
    client: Client,
    user_id: int,
    user_name: str,
    phone: str,
    course_name: str,
    method: str,
    order_id: str,
) -> None:
    text = MSG.ADMIN_PURCHASE_LOG.format(
        user_name   = user_name,
        user_id     = user_id,
        phone       = phone if phone and phone != "N/A" else "দেননি",
        course_name = course_name,
        method      = method,
        order_id    = order_id,
        date        = datetime.utcnow().strftime("%d %b %Y, %H:%M UTC"),
    )
    for admin_id in ADMIN_IDS:
        try:
            await client.send_message(
                admin_id, text, parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            LOGGER.warning(f"[Payment] Admin {admin_id} log failed: {e}")


# ═════════════════════════════════════════════════════════════
#  HELPER — Membership Card পাঠানো
# ═════════════════════════════════════════════════════════════

async def _send_membership_card(
    client: Client,
    user_id: int,
    user_name: str,
    phone: str,
    course_name: str,
    membership_id: str,
) -> None:
    if phone and phone not in ("N/A", "দেননি", ""):
        text = MSG.MEMBERSHIP_CARD.format(
            membership_id = membership_id,
            name          = user_name,
            phone         = phone,
            course_name   = course_name,
        )
    else:
        text = MSG.MEMBERSHIP_CARD_NO_PHONE.format(
            membership_id = membership_id,
            name          = user_name,
            course_name   = course_name,
        )
    try:
        await client.send_message(user_id, text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        LOGGER.warning(f"[MembershipCard] Send failed user={user_id}: {e}")


# ═════════════════════════════════════════════════════════════
#  setup(app)
# ═════════════════════════════════════════════════════════════

def setup(app: Client) -> None:

    # ── Buy Now ───────────────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^buy:([a-f0-9]{24})$"))
    async def cb_buy_now(client: Client, callback: CallbackQuery):
        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)
        if not course:
            return await callback.answer(MSG.ERROR_COURSE_NOT_FOUND, show_alert=True)

        if await db.check_user_owns_course(callback.from_user.id, course_id):
            await callback.message.edit_text(
                MSG.ALREADY_PURCHASED.format(name=course["name"], support=SUPPORT_USERNAME),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu_inline(),
            )
            return await callback.answer()

        await callback.message.edit_text(
            _payment_menu_text(course),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=payment_methods_kb(course_id),
        )
        await callback.answer()

    # ── Back to Payment Methods ───────────────────────────────
    @app.on_callback_query(filters.regex(r"^cpay:back:([a-f0-9]{24})$"))
    async def cb_payment_back(client: Client, callback: CallbackQuery):
        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)
        if not course:
            return await callback.answer(MSG.ERROR_COURSE_NOT_FOUND, show_alert=True)
        _proof_state.pop(callback.from_user.id, None)
        await callback.message.edit_text(
            _payment_menu_text(course),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=payment_methods_kb(course_id),
        )
        await callback.answer()

    # ── bKash ─────────────────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^cpay:bkash:([a-f0-9]{24})$"))
    async def cb_pay_bkash(client: Client, callback: CallbackQuery):
        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)
        if not course:
            return await callback.answer(MSG.ERROR_COURSE_NOT_FOUND, show_alert=True)

        uid = callback.from_user.id
        _proof_state[uid] = {"course_id": course_id, "method": "bKash", "step": "phone", "phone": None}

        await callback.message.edit_text(_bkash_text(course, uid), parse_mode=ParseMode.MARKDOWN)
        await callback.message.reply_text(
            MSG.PROOF_ASK_PHONE.format(
                course_name=course["name"], currency=course["currency"], price=course["price"]
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=proof_phone_kb(course_id),
        )
        await callback.answer("📲 bKash নির্দেশনা")

    # ── Nagad ─────────────────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^cpay:nagad:([a-f0-9]{24})$"))
    async def cb_pay_nagad(client: Client, callback: CallbackQuery):
        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)
        if not course:
            return await callback.answer(MSG.ERROR_COURSE_NOT_FOUND, show_alert=True)

        uid = callback.from_user.id
        _proof_state[uid] = {"course_id": course_id, "method": "Nagad", "step": "phone", "phone": None}

        await callback.message.edit_text(_nagad_text(course, uid), parse_mode=ParseMode.MARKDOWN)
        await callback.message.reply_text(
            MSG.PROOF_ASK_PHONE.format(
                course_name=course["name"], currency=course["currency"], price=course["price"]
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=proof_phone_kb(course_id),
        )
        await callback.answer("📲 Nagad নির্দেশনা")

    # NOTE: cb_skip_phone handler সম্পূর্ণ সরানো হয়েছে কারণ ফোন নম্বর বাধ্যতামূলক।

    # ── Skip Screenshot — সরাসরি জমা দাও ─────────────────────
    @app.on_callback_query(filters.regex(r"^proof:skip_screenshot:([a-f0-9]{24})$"))
    async def cb_skip_screenshot(client: Client, callback: CallbackQuery):
        course_id = callback.matches[0].group(1)
        uid       = callback.from_user.id
        course    = await db.get_course_by_id(course_id)
        if not course:
            return await callback.answer(MSG.ERROR_COURSE_NOT_FOUND, show_alert=True)

        state = _proof_state.get(uid)
        if not state:
            return await callback.answer("Session expired. আবার শুরু করুন।", show_alert=True)

        phone        = state.get("phone") or "N/A"
        method       = state.get("method", "manual")
        user         = callback.from_user
        username_str = f"@{user.username}" if user.username else "@N/A"

        existing = await db.get_pending_proof_for_course(uid, course_id)
        if existing:
            _proof_state.pop(uid, None)
            return await callback.message.edit_text(
                MSG.PROOF_ALREADY_PENDING.format(
                    course_name=course["name"],
                    proof_id=str(existing["_id"])[-8:],
                    support=SUPPORT_USERNAME,
                ),
                parse_mode=ParseMode.MARKDOWN,
            )

        proof_id = await db.save_payment_proof({
            "user_id": uid, "user_name": user.first_name, "username": username_str,
            "course_id": course_id, "course_name": course["name"],
            "amount": course["price"], "currency": course["currency"],
            "method": method, "phone_number": phone,
            "proof_file_id": None, "proof_caption": "Screenshot দেননি",
        })

        membership_id = await db.get_unique_membership_id()
        order_id = await db.create_order({
            "user_id": uid, "user_name": user.first_name, "username": username_str,
            "course_id": course_id, "course_name": course["name"],
            "amount": course["price"], "currency": course["currency"],
            "method": method, "phone_number": phone, "membership_id": membership_id,
        })

        _proof_state.pop(uid, None)

        await callback.message.edit_text(
            MSG.PROOF_SUBMITTED.format(
                course_name=course["name"], method=method,
                phone=phone, proof_id=proof_id[-8:], support=SUPPORT_USERNAME,
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🏠 Main Menu", callback_data="back:main")]]
            ),
        )

        await _notify_admin_purchase(client, uid, user.first_name, phone, course["name"], method, order_id)

        admin_text = MSG.ADMIN_NEW_PROOF.format(
            user_name=user.first_name, user_id=uid, username=username_str,
            phone=phone, course_name=course["name"], currency=course["currency"],
            price=course["price"], method=method, proof_id=proof_id[-8:],
            caption="Screenshot দেননি",
        )
        for admin_id in ADMIN_IDS:
            try:
                await client.send_message(admin_id, admin_text, parse_mode=ParseMode.MARKDOWN,
                                          reply_markup=admin_proof_actions_kb(proof_id))
            except Exception as e:
                LOGGER.warning(f"[Proof] Admin {admin_id} notify failed: {e}")

        await callback.answer("✅ জমা হয়েছে!")

    # ── Admin Proof Approve/Reject Sections remain the same ──
    # [cb_proof_approve এবং cb_proof_reject ফাংশনগুলো এখানে অপরিবর্তিত থাকবে]
    @app.on_callback_query(filters.regex(r"^proof:approve:([a-f0-9]{24})$"))
    async def cb_proof_approve(client: Client, callback: CallbackQuery):
        from auth import is_admin
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        proof_id = callback.matches[0].group(1)
        proof    = await db.get_proof_by_id(proof_id)
        if not proof:
            return await callback.answer("Proof not found.", show_alert=True)

        await db.update_proof_status(proof_id, "approved")

        from bson import ObjectId
        db_inst = db.get_db()
        order = await db_inst.orders.find_one(
            {"user_id": proof["user_id"], "course_id": proof["course_id"], "status": "pending"}
        )

        membership_id = None
        order_id_str  = ""

        if order:
            order_id_str  = str(order["_id"])
            membership_id = order.get("membership_id") or await db.get_unique_membership_id()
            await db.update_order_status(order_id_str, "approved")
            await db.update_order_membership(order_id_str, membership_id)
        else:
            membership_id = await db.get_unique_membership_id()
            order_id_str  = await db.create_order({
                "user_id": proof["user_id"], "user_name": proof.get("user_name", "User"),
                "username": proof.get("username", "@N/A"), "course_id": proof["course_id"],
                "course_name": proof["course_name"], "amount": proof["amount"],
                "currency": proof["currency"], "method": proof.get("method", "manual"),
                "phone_number": proof.get("phone_number"), "membership_id": membership_id,
                "status": "approved",
            })

        course = await db.get_course_by_id(str(proof["course_id"]))
        phone  = proof.get("phone_number") or "N/A"

        await _send_membership_card(
            client, proof["user_id"], proof.get("user_name", "User"),
            phone, proof["course_name"], membership_id,
        )

        if course:
            try:
                from plugins.group_manager import approve_and_send_link
                await approve_and_send_link(client, order_id_str, callback.message.chat.id)
            except Exception as e:
                LOGGER.warning(f"[ProofApprove] OTL failed: {e}")

        try:
            await callback.message.edit_caption(
                caption=(
                    f"✅ **Proof Approved!**\n\n"
                    f"👤 User: `{proof['user_id']}`\n"
                    f"📦 Course: {proof['course_name']}\n"
                    f"🎫 Membership ID: `{membership_id}`"
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            await callback.message.edit_text(
                f"✅ **Proof Approved!** Membership: `{membership_id}`",
                parse_mode=ParseMode.MARKDOWN,
            )
        await callback.answer("✅ Approved!")

    @app.on_callback_query(filters.regex(r"^proof:reject:([a-f0-9]{24})$"))
    async def cb_proof_reject(client: Client, callback: CallbackQuery):
        from auth import is_admin
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        proof_id = callback.matches[0].group(1)
        proof    = await db.get_proof_by_id(proof_id)
        if not proof:
            return await callback.answer("Proof not found.", show_alert=True)

        await db.update_proof_status(proof_id, "rejected")

        try:
            await client.send_message(
                proof["user_id"],
                MSG.PAYMENT_REJECTED.format(
                    course_name=proof["course_name"],
                    order_id=proof_id[-8:],
                    support=SUPPORT_USERNAME,
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass

        try:
            await callback.message.edit_caption(
                caption=f"❌ **Proof Rejected.**\n\n👤 User: `{proof['user_id']}`\n📦 Course: {proof['course_name']}",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            await callback.message.edit_text(
                f"❌ **Proof Rejected.** User: `{proof['user_id']}`",
                parse_mode=ParseMode.MARKDOWN,
            )
        await callback.answer("❌ Rejected.")

    # ── Message Handler — Phone ও Screenshot input ─────────────
    @app.on_message(
        filters.private & (filters.text | filters.photo | filters.document),
        group=15,
    )
    async def proof_input_handler(client: Client, message: Message):
        uid   = message.from_user.id
        state = _proof_state.get(uid)
        if not state:
            return

        course_id = state.get("course_id")
        course    = await db.get_course_by_id(course_id)
        if not course:
            _proof_state.pop(uid, None)
            return

        step = state.get("step")

        # ── Phone Number ───────────────────────────────────────
        if step == "phone" and message.text:
            phone = message.text.strip()
            valid = (
                (phone.startswith("01") and len(phone) == 11 and phone.isdigit())
                or (phone.startswith("+") and len(phone) > 8)
            )
            if not valid:
                # পরিবর্তন এখানে: Mandatory message আপডেট করা হয়েছে
                await message.reply_text(
                    "⚠️ Valid Phone Number দিন।\n_e.g. 01712345678_\n\n"
                    "📌 যে নম্বর থেকে bKash/Nagad করেছেন সেটা দিন।\n"
                    "Payment verify করতে নম্বর **আবশ্যিক**।",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=proof_phone_kb(course_id),
                )
                return

            state["phone"] = phone
            state["step"]  = "screenshot"

            await message.reply_text(
                MSG.PROOF_ASK_SCREENSHOT.format(
                    course_name=course["name"], currency=course["currency"],
                    price=course["price"], method=state["method"],
                    phone_line=f"📱 **Phone:** `{phone}`\n",
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=proof_cancel_kb(course_id),
            )

        # ── Screenshot logic remains the same ──────────────────
        elif step == "screenshot" and (message.photo or message.document):
            file_id      = message.photo.file_id if message.photo else message.document.file_id
            caption      = message.caption or "No caption"
            phone        = state.get("phone") or "N/A"
            method       = state.get("method", "manual")
            user         = message.from_user
            username_str = f"@{user.username}" if user.username else "@N/A"

            existing = await db.get_pending_proof_for_course(uid, course_id)
            if existing:
                _proof_state.pop(uid, None)
                await message.reply_text(
                    MSG.PROOF_ALREADY_PENDING.format(
                        course_name=course["name"],
                        proof_id=str(existing["_id"])[-8:],
                        support=SUPPORT_USERNAME,
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )
                return

            proof_id = await db.save_payment_proof({
                "user_id": uid, "user_name": user.first_name, "username": username_str,
                "course_id": course_id, "course_name": course["name"],
                "amount": course["price"], "currency": course["currency"],
                "method": method, "phone_number": phone,
                "proof_file_id": file_id, "proof_caption": caption,
            })

            membership_id = await db.get_unique_membership_id()
            order_id = await db.create_order({
                "user_id": uid, "user_name": user.first_name, "username": username_str,
                "course_id": course_id, "course_name": course["name"],
                "amount": course["price"], "currency": course["currency"],
                "method": method, "phone_number": phone, "membership_id": membership_id,
            })

            _proof_state.pop(uid, None)

            LOGGER.info(f"[Proof] Submitted | user={uid} course={course['name']}")

            await message.reply_text(
                MSG.PROOF_SUBMITTED.format(
                    course_name=course["name"], method=method,
                    phone=phone, proof_id=proof_id[-8:], support=SUPPORT_USERNAME,
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🏠 Main Menu", callback_data="back:main")]]
                ),
            )

            await _notify_admin_purchase(client, uid, user.first_name, phone, course["name"], method, order_id)

            admin_text = MSG.ADMIN_NEW_PROOF.format(
                user_name=user.first_name, user_id=uid, username=username_str,
                phone=phone, course_name=course["name"], currency=course["currency"],
                price=course["price"], method=method, proof_id=proof_id[-8:], caption=caption,
            )
            for admin_id in ADMIN_IDS:
                try:
                    if message.photo:
                        await client.send_photo(admin_id, file_id, caption=admin_text,
                                                parse_mode=ParseMode.MARKDOWN,
                                                reply_markup=admin_proof_actions_kb(proof_id))
                    else:
                        await client.send_document(admin_id, file_id, caption=admin_text,
                                                   parse_mode=ParseMode.MARKDOWN,
                                                   reply_markup=admin_proof_actions_kb(proof_id))
                except Exception as e:
                    LOGGER.warning(f"[Proof] Admin {admin_id} failed: {e}")

        elif step == "screenshot" and message.text:
            await message.reply_text(
                "⚠️ Screenshot বা Document পাঠান।\n\nঅথবা নিচের বাটনে ক্লিক করে Skip করুন।",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=proof_cancel_kb(course_id),
            )

    LOGGER.info("[Payment] Plugin loaded ✅")
