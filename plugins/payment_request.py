# plugins/payment_request.py
# Copyright @YourChannel
# ─────────────────────────────────────────────────────────────
# Course Code ভিত্তিক Payment Request Flow
#
# Flow:
#   💸 PAYMENT REQUEST বাটন
#     → Course Code চাওয়া
#       → Mobile Number চাওয়া (01XXXXXXXXX format)
#         → Transaction ID চাওয়া
#           (bKash = 10 ডিজিট, Nagad = 8 ডিজিট)
#             → Admin কে Approve/Reject/Ban বাটনসহ notify
#               → Approve → OTL + Membership Card
# ─────────────────────────────────────────────────────────────

import re
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
from config import ADMIN_IDS, ADMIN_USERNAME, SUPPORT_USERNAME
from misc import States, clear_state, get_state, set_state, update_data, get_data
from misc.keyboards import main_menu_inline
from misc.messages import MSG
from utils import LOGGER

# ── In-memory payment request state ───────────────────────────
# { user_id: { step, course_id, course_code, phone, tx_id, method } }
_pay_req_state: dict = {}

# ── Regex patterns ─────────────────────────────────────────────
_PHONE_RE  = re.compile(r"^01[3-9]\d{8}$")       # 01XXXXXXXXX (11 digits)
_BKASH_RE  = re.compile(r"^\d{10}$")              # bKash TXN = 10 digits
_NAGAD_RE  = re.compile(r"^\d{8}$")               # Nagad TXN = 8 digits


def _detect_method(tx_id: str) -> str:
    """Transaction ID দেখে method অনুমান করো।"""
    if re.match(r"^\d{10}$", tx_id):
        return "bKash"
    if re.match(r"^\d{8}$", tx_id):
        return "Nagad"
    return "Manual"


def _validate_tx(tx_id: str, method: str) -> bool:
    """Transaction ID validate করো।"""
    if method == "bKash":
        return bool(_BKASH_RE.match(tx_id))
    if method == "Nagad":
        return bool(_NAGAD_RE.match(tx_id))
    # Manual বা অন্য — যেকোনো ৬+ character
    return len(tx_id) >= 6


def _admin_notify_kb(order_id: str, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ APPROVE",
                    callback_data=f"payreq:approve:{order_id}",
                ),
                InlineKeyboardButton(
                    "❎ REJECT",
                    callback_data=f"payreq:reject:{order_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⛔ BAN",
                    callback_data=f"payreq:ban:{user_id}:{order_id}",
                ),
            ],
        ]
    )


def setup(app: Client) -> None:

    # ── 💸 PAYMENT REQUEST বাটন ────────────────────────────────
    @app.on_message(
        filters.private & filters.regex(r"^💸 PAYMENT REQUEST$"),
        group=20,
    )
    async def btn_payment_request(client: Client, message: Message):
        uid = message.from_user.id

        # Ban check
        if await db.is_banned(uid):
            await message.reply_text(
                "🚫 **আপনাকে এই Bot থেকে Banned করা হয়েছে।**\n\n"
                f"সাহায্যের জন্য: {SUPPORT_USERNAME}",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        _pay_req_state[uid] = {"step": "course_code"}

        await message.reply_text(
            "💸 **Payment Request**\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "**ধাপ ১/৩ — Course Code দিন:**\n\n"
            "📌 Course Code টি Payment Instructions এ দেওয়া আছে।\n"
            "_e.g. PHY2024, MATH101_\n\n"
            "❌ বাতিল করতে /cancel দিন।",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ বাতিল করুন", callback_data="payreq:cancel")]]
            ),
        )

    # ── Cancel callback ────────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^payreq:cancel$"))
    async def cb_payreq_cancel(client: Client, callback: CallbackQuery):
        uid = callback.from_user.id
        _pay_req_state.pop(uid, None)
        await callback.message.edit_text(
            "✅ **বাতিল করা হয়েছে।**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_inline(),
        )
        await callback.answer("বাতিল হয়েছে।")

    # ── Message input handler ──────────────────────────────────
    @app.on_message(
        filters.private & filters.text,
        group=20,
    )
    async def payreq_input_handler(client: Client, message: Message):
        uid   = message.from_user.id
        state = _pay_req_state.get(uid)
        if not state:
            return

        # Ban check
        if await db.is_banned(uid):
            _pay_req_state.pop(uid, None)
            return

        step = state.get("step")
        text = message.text.strip()

        # ── ধাপ ১: Course Code ─────────────────────────────────
        if step == "course_code":
            course = await db.get_course_by_code(text)
            if not course:
                await message.reply_text(
                    "❌ **Course Code সঠিক নয়!**\n\n"
                    f"`{text}` নামে কোনো Course পাওয়া যায়নি।\n\n"
                    "📌 সঠিক Course Code দিন অথবা /cancel দিন।",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return

            # Already purchased?
            course_id = str(course["_id"])
            if await db.check_user_owns_course(uid, course_id):
                _pay_req_state.pop(uid, None)
                await message.reply_text(
                    MSG.ALREADY_PURCHASED.format(
                        name=course["name"], support=SUPPORT_USERNAME
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=main_menu_inline(),
                )
                return

            # Pending check
            existing = await db.get_pending_proof_for_course(uid, course_id)
            if existing:
                _pay_req_state.pop(uid, None)
                await message.reply_text(
                    MSG.PROOF_ALREADY_PENDING.format(
                        course_name=course["name"],
                        proof_id=str(existing["_id"])[-8:],
                        support=SUPPORT_USERNAME,
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )
                return

            state["course_id"]   = course_id
            state["course_code"] = text.upper()
            state["course_name"] = course["name"]
            state["currency"]    = course["currency"]
            state["price"]       = course["price"]
            state["step"]        = "phone"

            await message.reply_text(
                f"✅ **Course পাওয়া গেছে!**\n\n"
                f"📦 **Course:** `{course['name']}`\n"
                f"💰 **মূল্য:** `{course['currency']} {course['price']}`\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"**ধাপ ২/৩ — Mobile Number দিন:**\n\n"
                f"📱 যে নম্বর থেকে Payment করেছেন সেটা দিন।\n"
                f"_e.g. 01712345678_\n\n"
                f"❌ বাতিল করতে /cancel দিন।",
                parse_mode=ParseMode.MARKDOWN,
            )

        # ── ধাপ ২: Mobile Number ───────────────────────────────
        elif step == "phone":
            if not _PHONE_RE.match(text):
                await message.reply_text(
                    "❌ **Mobile Number সঠিক নয়!**\n\n"
                    "📌 নম্বরটি অবশ্যই:\n"
                    "• ১১ ডিজিটের হতে হবে\n"
                    "• **01** দিয়ে শুরু হতে হবে\n\n"
                    "_e.g. 01712345678_\n\n"
                    "আবার চেষ্টা করুন অথবা /cancel দিন।",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return

            state["phone"] = text
            state["step"]  = "tx_id"

            await message.reply_text(
                f"✅ **Mobile:** `{text}`\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"**ধাপ ৩/৩ — Transaction ID দিন:**\n\n"
                f"💳 Payment করার পর যে Transaction ID পেয়েছেন সেটা দিন।\n\n"
                f"📌 **Format:**\n"
                f"• **bKash:** ১০ ডিজিটের নম্বর\n"
                f"• **Nagad:** ৮ ডিজিটের নম্বর\n\n"
                f"❌ বাতিল করতে /cancel দিন।",
                parse_mode=ParseMode.MARKDOWN,
            )

        # ── ধাপ ৩: Transaction ID ──────────────────────────────
        elif step == "tx_id":
            method = _detect_method(text)

            if not _validate_tx(text, method):
                await message.reply_text(
                    "❌ **Transaction ID সঠিক নয়!**\n\n"
                    "📌 **Format:**\n"
                    "• **bKash:** ঠিক ১০ ডিজিটের সংখ্যা\n"
                    "• **Nagad:** ঠিক ৮ ডিজিটের সংখ্যা\n\n"
                    "আবার চেষ্টা করুন অথবা /cancel দিন।",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return

            state["tx_id"]  = text
            state["method"] = method
            state["step"]   = "done"

            user         = message.from_user
            username_str = f"@{user.username}" if user.username else "@N/A"

            # Save proof
            proof_id = await db.save_payment_proof(
                {
                    "user_id":      uid,
                    "user_name":    user.first_name,
                    "username":     username_str,
                    "course_id":    state["course_id"],
                    "course_name":  state["course_name"],
                    "amount":       state["price"],
                    "currency":     state["currency"],
                    "method":       method,
                    "phone_number": state["phone"],
                    "tx_id":        text,
                    "proof_caption": f"TX: {text}",
                }
            )

            # Save order
            membership_id = await db.get_unique_membership_id()
            order_id = await db.create_order(
                {
                    "user_id":       uid,
                    "user_name":     user.first_name,
                    "username":      username_str,
                    "course_id":     state["course_id"],
                    "course_name":   state["course_name"],
                    "amount":        state["price"],
                    "currency":      state["currency"],
                    "method":        method,
                    "phone_number":  state["phone"],
                    "tx_id":         text,
                    "membership_id": membership_id,
                    "course_code":   state["course_code"],
                }
            )

            _pay_req_state.pop(uid, None)

            LOGGER.info(
                f"[PayReq] Submitted | user={uid} "
                f"course={state['course_name']} tx={text}"
            )

            # User কে confirmation
            await message.reply_text(
                f"✅ **Payment Request জমা হয়েছে!**\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📦 **Course:** `{state['course_name']}`\n"
                f"💳 **Method:** `{method}`\n"
                f"📱 **Phone:** `{state['phone']}`\n"
                f"🔢 **TX ID:** `{text}`\n"
                f"🆔 **Order ID:** `#{order_id[-8:]}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"⏳ Admin আপনার payment verify করছেন।\n"
                f"সাধারণত কয়েক মিনিটের মধ্যে Confirm হবে।\n\n"
                f"📞 সাহায্য: {SUPPORT_USERNAME}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu_inline(),
            )

            # Admin দের notify করো
            admin_text = (
                f"🔔 NEW PAYMENT REQUEST\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 User: {user.first_name} (`{uid}`)\n"
                f"📛 Username: {username_str}\n"
                f"📱 Phone: {state['phone']}\n"
                f"📦 Course Code: {state['course_code']}\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"⬇️ Verify করে Approve, Reject বা Ban করুন:"
            )


            for admin_id in ADMIN_IDS:
                try:
                    await client.send_message(
                        admin_id,
                        admin_text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=_admin_notify_kb(order_id, uid),
                    )
                except Exception as e:
                    LOGGER.warning(
                        f"[PayReq] Admin {admin_id} notify failed: {e}"
                    )

    @app.on_callback_query(
        filters.regex(r"^payreq:approve:([a-f0-9]{24})$")
    )
    async def cb_payreq_approve(client: Client, callback: CallbackQuery):
        from auth import is_admin as _is_admin
        if not _is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        order_id = callback.matches[0].group(1)
        from bson import ObjectId
        order = await db.get_db().orders.find_one(
            {"_id": ObjectId(order_id)}
        )
        if not order:
            return await callback.answer("Order পাওয়া যায়নি!", show_alert=True)

        if order.get("status") != "pending":
            return await callback.answer(
                f"এই Order ইতিমধ্যে {order['status']}!", show_alert=True
            )

        # ── Process Approval ──────────────────────────────────────
        user_id = order["user_id"]
        membership_id = order.get("membership_id") or await db.get_unique_membership_id()
        await db.update_order_status(order_id, "approved")
        await db.update_order_membership(order_id, membership_id)

        # Update payment proof status
        proof = await db.get_db().payment_proofs.find_one(
            {
                "user_id":   user_id,
                "course_id": order["course_id"],
                "status":    "pending",
            }
        )
        if proof:
            await db.update_proof_status(str(proof["_id"]), "approved")

        # ── Generate Multi-Course Links ──────────────────────────
        from plugins.group_manager import generate_one_time_link

        # Get Discussion Group Link for the approved course
        course_info = await db.get_db().courses.find_one({"_id": ObjectId(order["course_id"])})
        discussion_link = course_info.get("discussion_group_link", "https://t.me/+WU_Qyp-jlNdjOWU1") if course_info else "https://t.me/+WU_Qyp-jlNdjOWU1"

        subjects = {
            "Physics": "Physics",
            "Chemistry": "Chemistry",
            "Math": "Math",
            "Biology": "Biology"
        }

        links_text = ""
        for label, name in subjects.items():
            # Find course by name to get group_id
            course = await db.get_db().courses.find_one({"name": {"$regex": name, "$options": "i"}})
            if course and course.get("group_id"):
                link = await generate_one_time_link(client, int(course["group_id"]), user_id, name)
                links_text += f"🔹 {label}: `{link if link else 'Failed'}`\n"
            else:
                links_text += f"🔹 {label}: `Not Set`\n"

        approval_msg = (
            f"✅ Payment Approved!\n\n"
            f"🔗 Discussion Group :\n"
            f"{discussion_link}\n\n"
            f"📚 Course Links:\n"
            f"{links_text}\n"
            f"⏰ Link Valid : 24 Hours\n"
            f"🔐 One Time Join Link"
        )

        # Send to User
        try:
            await client.send_message(user_id, approval_msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        except Exception as e:
            LOGGER.warning(f"[PayReq] Failed to send approval msg to {user_id}: {e}")

        # Send Membership Card
        phone = order.get("phone_number") or "N/A"
        await _send_membership_card(
            client, user_id, order.get("user_name", "User"), phone, order["course_name"], membership_id
        )

        await callback.message.edit_text(
            f"✅ **Approved!**\n\n"
            f"👤 User: `{user_id}`\n"
            f"📦 Course: {order['course_name']}\n"
            f"🎫 Membership ID: `{membership_id}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer("✅ Approved!")

    # ── Admin: Reject ──────────────────────────────────────────
    @app.on_callback_query(
        filters.regex(r"^payreq:reject:([a-f0-9]{24})$")
    )
    async def cb_payreq_reject(client: Client, callback: CallbackQuery):
        from auth import is_admin as _is_admin
        if not _is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        order_id = callback.matches[0].group(1)
        from bson import ObjectId
        order = await db.get_db().orders.find_one(
            {"_id": ObjectId(order_id)}
        )
        if not order:
            return await callback.answer("Order পাওয়া যায়নি!", show_alert=True)

        await db.update_order_status(order_id, "rejected")

        # Proof ও reject করো
        proof = await db.get_db().payment_proofs.find_one(
            {
                "user_id":   order["user_id"],
                "course_id": order["course_id"],
                "status":    "pending",
            }
        )
        if proof:
            await db.update_proof_status(str(proof["_id"]), "rejected")

        try:
            await client.send_message(
                order["user_id"],
                "❎ Payment Rejected!\n\n"
                "👨‍💻 আপনি অকারণে মিথ‍্যা পেমেন্ট রিকোয়েস্ট দিচ্ছেন। দ্বিতীয়বার এমন মিথ‍্যা পেমেন্ট রিকোয়েস্ট পাঠালে আপনাকে এই বট থেকে ⛔ BAN করে দেওয়া হবে।",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass

        await callback.message.edit_text(
            f"❌ **Rejected.**\n\n"
            f"👤 User: `{order['user_id']}`\n"
            f"📦 Course: {order['course_name']}",
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer("❌ Rejected.")

    # ── Admin: Ban User ────────────────────────────────────────
    @app.on_callback_query(
        filters.regex(r"^payreq:ban:(\d+):([a-f0-9]{24})$")
    )
    async def cb_payreq_ban(client: Client, callback: CallbackQuery):
        from auth import is_admin as _is_admin
        if not _is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        user_id  = int(callback.matches[0].group(1))
        order_id = callback.matches[0].group(2)

        await db.ban_user(user_id, reason="Banned via payment request review")
        await db.update_order_status(order_id, "rejected")

        try:
            await client.send_message(
                user_id,
                "⛔ BANNED\n\n"
                "👨‍💻 আপনাকে এই বট থেকে BAN করা হয়েছে। আপনি আর কোনো ধরনের পেমেন্ট রিকোয়েস্ট পাঠাতে পারবেন না।",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass

        await callback.message.edit_text(
            f"🚫 **User {user_id} Banned & Order Rejected!**",
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer(f"🚫 User {user_id} banned!")

    # ── Admin: Unban User ──────────────────────────────────────
    @app.on_message(
        filters.command("unban") & filters.private
    )
    async def cmd_unban(client: Client, message: Message):
        from auth import is_admin as _is_admin
        if not _is_admin(message.from_user.id):
            return

        if len(message.command) < 2:
            await message.reply_text(
                "❌ **Usage:** `/unban {user_id}`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        try:
            user_id = int(message.command[1])
            await db.unban_user(user_id)
            await message.reply_text(
                f"✅ **User `{user_id}` has been unbanned successfully.**",
                parse_mode=ParseMode.MARKDOWN,
            )
        except ValueError:
            await message.reply_text("❌ Please provide a valid numeric User ID.")
        except Exception as e:
            LOGGER.error(f"[PayReq] Unban failed: {e}")
            await message.reply_text(f"❌ An error occurred: {e}")

    LOGGER.info("[PaymentRequest] Plugin loaded ✅")


# ════════════════════════════════════════════════════════════
#  HELPER — Membership Card
# ════════════════════════════════════════════════════════════

async def _send_membership_card(
    client: Client,
    user_id: int,
    user_name: str,
    phone: str,
    course_name: str,
    membership_id: str,
) -> None:
    from misc.messages import MSG
    if phone and phone not in ("N/A", "দেননি", ""):
        text = MSG.MEMBERSHIP_CARD.format(
            membership_id=membership_id,
            name=user_name,
            phone=phone,
            course_name=course_name,
        )
    else:
        text = MSG.MEMBERSHIP_CARD_NO_PHONE.format(
            membership_id=membership_id,
            name=user_name,
            course_name=course_name,
        )
    try:
        await client.send_message(user_id, text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        LOGGER.warning(f"[MembershipCard] Send failed user={user_id}: {e}")
