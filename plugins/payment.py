# plugins/payment.py
# Copyright @YourChannel
# ─────────────────────────────────────────────────────────────
# Payment + Proof Submission System
#
# Flow (Manual Payment):
#   Buy Now → Payment Method
#     → bKash/Nagad/Crypto instructions
#       → Phone Number দাও (optional)
#         → Screenshot/Proof পাঠাও
#           → Admin কে notify করো
#             → Admin Approve/Reject করে
# ─────────────────────────────────────────────────────────────

import hashlib
import time
import uuid
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.handlers import RawUpdateHandler
from pyrogram.raw.functions.messages import (
    SendMedia,
    SetBotPrecheckoutResults,
)
from pyrogram.raw.types import (
    DataJSON,
    Invoice,
    InputMediaInvoice,
    KeyboardButtonBuy,
    KeyboardButtonRow,
    LabeledPrice,
    MessageActionPaymentSentMe,
    MessageService,
    PeerChannel,
    PeerChat,
    PeerUser,
    ReplyInlineMarkup,
    UpdateBotPrecheckoutQuery,
    UpdateNewMessage,
)
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
    BINANCE_ADDRESS,
    BINANCE_UID,
    NAGAD_NUMBER,
    SUPPORT_USERNAME,
)
from misc import States, clear_state, get_data, get_state, main_menu_inline, set_state, update_data
from misc.keyboards import (
    admin_proof_actions_kb,
    payment_methods_kb,
    proof_cancel_kb,
    proof_phone_kb,
    support_only_kb,
)
from misc.messages import MSG
from utils import LOGGER

# ── In-memory stores ──────────────────────────────────────────
_active_invoices: dict  = {}
_pending_methods: dict  = {}
_proof_state: dict      = {}
# Structure: { user_id: { course_id, method, phone } }


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


def _crypto_text(course: dict, user_id: int) -> str:
    return MSG.PAYMENT_CRYPTO.format(
        course_name     = course["name"],
        price           = course["price"],
        currency        = course["currency"],
        binance_uid     = BINANCE_UID,
        binance_address = BINANCE_ADDRESS,
        user_id         = user_id,
        support         = SUPPORT_USERNAME,
    )


# ═════════════════════════════════════════════════════════════
#  STARS INVOICE
# ═════════════════════════════════════════════════════════════

async def _send_stars_invoice(
    client: Client,
    chat_id: int,
    user_id: int,
    course: dict,
    course_id: str,
) -> None:
    if _active_invoices.get(user_id):
        await client.send_message(
            chat_id,
            MSG.STARS_DUPLICATE_INVOICE,
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    try:
        stars_amount = int(float(course["price"]))
    except (ValueError, TypeError):
        stars_amount = 1

    loading = await client.send_message(
        chat_id,
        MSG.STARS_INVOICE_GENERATING.format(
            course_name=course["name"]
        ),
        parse_mode=ParseMode.MARKDOWN,
    )

    try:
        _active_invoices[user_id] = True
        ts          = int(time.time())
        unique      = str(uuid.uuid4())[:8]
        payload_str = (
            f"course_{course_id}_{user_id}"
            f"_{stars_amount}_{ts}_{unique}"
        )
        random_id = (
            int(
                hashlib.sha256(
                    payload_str.encode()
                ).hexdigest(),
                16,
            )
            % (2**63)
        )

        invoice = Invoice(
            currency="XTR",
            prices=[
                LabeledPrice(
                    label=f"{course['name']} — {stars_amount} Stars",
                    amount=stars_amount,
                )
            ],
            max_tip_amount=0,
            suggested_tip_amounts=[],
            recurring=False, test=False,
            name_requested=False,
            phone_requested=False,
            email_requested=False,
            shipping_address_requested=False,
            flexible=False,
        )
        media = InputMediaInvoice(
            title=f"🎓 {course['name']}",
            description=(
                f"Course: {course['name']}\n"
                f"Subject: {course['subject']}\n"
                f"Brand: {course['brand']}\n"
                f"Price: {stars_amount} Stars"
            ),
            invoice=invoice,
            payload=payload_str.encode(),
            provider="STARS",
            provider_data=DataJSON(data="{}"),
        )
        markup = ReplyInlineMarkup(
            rows=[
                KeyboardButtonRow(
                    buttons=[
                        KeyboardButtonBuy(
                            text=f"⭐ {stars_amount} Stars দিয়ে কিনুন"
                        )
                    ]
                )
            ]
        )

        peer = await client.resolve_peer(chat_id)
        await client.invoke(
            SendMedia(
                peer=peer,
                media=media,
                message="",
                random_id=random_id,
                reply_markup=markup,
            )
        )

        await client.edit_message_text(
            chat_id,
            loading.id,
            MSG.STARS_INVOICE_READY.format(
                course_name  = course["name"],
                stars_amount = stars_amount,
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 Payment Method এ ফিরুন",
                            callback_data=f"cpay:back:{course_id}",
                        )
                    ]
                ]
            ),
        )

    except Exception as e:
        LOGGER.error(
            f"[Stars] Invoice failed | "
            f"user={user_id} error={e}"
        )
        await client.edit_message_text(
            chat_id,
            loading.id,
            MSG.STARS_INVOICE_FAILED.format(
                support=SUPPORT_USERNAME
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=payment_methods_kb(course_id),
        )
    finally:
        _active_invoices.pop(user_id, None)


# ═════════════════════════════════════════════════════════════
#  RAW UPDATE — Stars Pre-checkout & Success
# ═════════════════════════════════════════════════════════════

async def _raw_update_handler(
    client: Client, update, users, chats
) -> None:

    if isinstance(update, UpdateBotPrecheckoutQuery):
        try:
            await client.invoke(
                SetBotPrecheckoutResults(
                    query_id=update.query_id,
                    success=True,
                )
            )
        except Exception as e:
            LOGGER.error(f"[PreCheckout] Failed: {e}")
            try:
                await client.invoke(
                    SetBotPrecheckoutResults(
                        query_id=update.query_id,
                        success=False,
                        error="Payment error. Try again.",
                    )
                )
            except Exception:
                pass
        return

    if not (
        isinstance(update, UpdateNewMessage)
        and isinstance(update.message, MessageService)
        and isinstance(
            update.message.action, MessageActionPaymentSentMe
        )
    ):
        return

    payment = update.message.action

    try:
        user_id = None
        if update.message.from_id and hasattr(
            update.message.from_id, "user_id"
        ):
            user_id = update.message.from_id.user_id
        if not user_id and users:
            positives = [u for u in users if u > 0]
            user_id   = positives[0] if positives else None
        if not user_id:
            return

        pid = update.message.peer_id
        if isinstance(pid, PeerUser):
            chat_id = pid.user_id
        elif isinstance(pid, PeerChat):
            chat_id = pid.chat_id
        elif isinstance(pid, PeerChannel):
            chat_id = pid.channel_id
        else:
            chat_id = user_id

        payload   = payment.payload.decode()
        parts     = payload.split("_")
        if len(parts) < 3 or parts[0] != "course":
            return

        course_id   = parts[1]
        tx_id       = payment.charge.id
        amount_paid = payment.total_amount

        course = await db.get_course_by_id(course_id)
        if not course:
            return

        user_info = users.get(user_id)
        full_name = (
            f"{user_info.first_name} "
            f"{getattr(user_info,'last_name','') or ''}".strip()
            if user_info else "User"
        )
        username = (
            f"@{user_info.username}"
            if user_info and user_info.username
            else "@N/A"
        )

        # ── Membership ID generate করো ────────────────────────
        membership_id = await db.get_unique_membership_id()

        # ── Order create করো ──────────────────────────────────
        order_id = await db.create_order(
            {
                "user_id":       user_id,
                "user_name":     full_name,
                "username":      username,
                "course_id":     course_id,
                "course_name":   course["name"],
                "amount":        amount_paid,
                "currency":      "XTR",
                "method":        "telegram_stars",
                "tx_id":         tx_id,
                "status":        "approved",
                "membership_id": membership_id,
            }
        )

        # ── User কে Success message পাঠাও ─────────────────────
        await client.send_message(
            chat_id=chat_id,
            text=MSG.PAYMENT_STARS_SUCCESS.format(
                user_name    = full_name,
                course_name  = course["name"],
                stars_amount = amount_paid,
                tx_id        = tx_id,
                support      = SUPPORT_USERNAME,
            ),
            parse_mode=ParseMode.MARKDOWN,
        )

        # ── Membership Card পাঠাও ─────────────────────────────
        await client.send_message(
            chat_id=chat_id,
            text=MSG.MEMBERSHIP_CARD_NO_PHONE.format(
                membership_id = membership_id,
                name          = full_name,
                course_name   = course["name"],
                brand         = course["brand"],
                currency      = "Stars",
                price         = amount_paid,
                date          = datetime.utcnow().strftime(
                    "%d %B %Y"
                ),
            ),
            parse_mode=ParseMode.MARKDOWN,
        )

        # ── Admin notify করো ──────────────────────────────────
        admin_text = MSG.ADMIN_NEW_STARS_PAYMENT.format(
            user_name    = full_name,
            user_id      = user_id,
            username     = username,
            course_name  = course["name"],
            stars_amount = amount_paid,
            tx_id        = tx_id,
            order_id     = order_id,
        )
        for admin_id in ADMIN_IDS:
            try:
                await client.send_message(
                    admin_id,
                    admin_text,
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass

        # ── OTL Generate & Send ────────────────────────────────
        try:
            from plugins.group_manager import approve_and_send_link
            await approve_and_send_link(
                client, order_id, ADMIN_IDS[0]
            )
        except Exception as e:
            LOGGER.warning(f"[Stars] OTL failed: {e}")

    except Exception as e:
        LOGGER.error(f"[Stars] Payment error: {e}")
        try:
            await client.send_message(
                chat_id=user_id,
                text=MSG.ERROR_PAYMENT_PROCESSING.format(
                    support=SUPPORT_USERNAME
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass


# ═════════════════════════════════════════════════════════════
#  setup(app)
# ═════════════════════════════════════════════════════════════

def setup(app: Client) -> None:

    # ══════════════════════════════════════════════════════════
    #  Buy Now → Payment Method Screen
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(
        filters.regex(r"^buy:([a-f0-9]{24})$")
    )
    async def cb_buy_now(
        client: Client, callback: CallbackQuery
    ):
        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)
        if not course:
            return await callback.answer(
                MSG.ERROR_COURSE_NOT_FOUND, show_alert=True
            )

        # Duplicate purchase check
        if await db.check_user_owns_course(
            callback.from_user.id, course_id
        ):
            await callback.message.edit_text(
                MSG.ALREADY_PURCHASED.format(
                    name    = course["name"],
                    support = SUPPORT_USERNAME,
                ),
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

    # ══════════════════════════════════════════════════════════
    #  Back to Payment Methods
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(
        filters.regex(r"^cpay:back:([a-f0-9]{24})$")
    )
    async def cb_payment_back(
        client: Client, callback: CallbackQuery
    ):
        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)
        if not course:
            return await callback.answer(
                MSG.ERROR_COURSE_NOT_FOUND, show_alert=True
            )
        # proof state clear করো
        uid = callback.from_user.id
        _proof_state.pop(uid, None)
        _pending_methods.pop(
            f"{uid}:{course_id}", None
        )

        await callback.message.edit_text(
            _payment_menu_text(course),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=payment_methods_kb(course_id),
        )
        await callback.answer()

    # ══════════════════════════════════════════════════════════
    #  Stars Payment
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(
        filters.regex(r"^cpay:stars:([a-f0-9]{24})$")
    )
    async def cb_pay_stars(
        client: Client, callback: CallbackQuery
    ):
        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)
        if not course:
            return await callback.answer(
                MSG.ERROR_COURSE_NOT_FOUND, show_alert=True
            )
        await callback.answer("⭐ Invoice তৈরি হচ্ছে...")
        await _send_stars_invoice(
            client,
            callback.message.chat.id,
            callback.from_user.id,
            course,
            course_id,
        )

    # ══════════════════════════════════════════════════════════
    #  bKash — Instructions + Phone Number চাও
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(
        filters.regex(r"^cpay:bkash:([a-f0-9]{24})$")
    )
    async def cb_pay_bkash(
        client: Client, callback: CallbackQuery
    ):
        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)
        if not course:
            return await callback.answer(
                MSG.ERROR_COURSE_NOT_FOUND, show_alert=True
            )
        uid = callback.from_user.id
        _pending_methods[f"{uid}:{course_id}"] = "bkash"
        _proof_state[uid] = {
            "course_id": course_id,
            "method":    "bKash",
            "step":      "phone",
            "phone":     None,
        }

        await callback.message.edit_text(
            _bkash_text(course, uid),
            parse_mode=ParseMode.MARKDOWN,
        )
        # Phone চাও
        await callback.message.reply_text(
            MSG.PROOF_ASK_PHONE.format(
                course_name = course["name"],
                currency    = course["currency"],
                price       = course["price"],
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=proof_phone_kb(course_id),
        )
        await callback.answer("📲 bKash নির্দেশনা")

    # ══════════════════════════════════════════════════════════
    #  Nagad — Instructions + Phone Number চাও
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(
        filters.regex(r"^cpay:nagad:([a-f0-9]{24})$")
    )
    async def cb_pay_nagad(
        client: Client, callback: CallbackQuery
    ):
        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)
        if not course:
            return await callback.answer(
                MSG.ERROR_COURSE_NOT_FOUND, show_alert=True
            )
        uid = callback.from_user.id
        _pending_methods[f"{uid}:{course_id}"] = "nagad"
        _proof_state[uid] = {
            "course_id": course_id,
            "method":    "Nagad",
            "step":      "phone",
            "phone":     None,
        }

        await callback.message.edit_text(
            _nagad_text(course, uid),
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.message.reply_text(
            MSG.PROOF_ASK_PHONE.format(
                course_name = course["name"],
                currency    = course["currency"],
                price       = course["price"],
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=proof_phone_kb(course_id),
        )
        await callback.answer("📲 Nagad নির্দেশনা")

    # ══════════════════════════════════════════════════════════
    #  Crypto
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(
        filters.regex(r"^cpay:crypto:([a-f0-9]{24})$")
    )
    async def cb_pay_crypto(
        client: Client, callback: CallbackQuery
    ):
        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)
        if not course:
            return await callback.answer(
                MSG.ERROR_COURSE_NOT_FOUND, show_alert=True
            )
        uid = callback.from_user.id
        _pending_methods[f"{uid}:{course_id}"] = "crypto"
        _proof_state[uid] = {
            "course_id": course_id,
            "method":    "Binance/USDT",
            "step":      "phone",
            "phone":     None,
        }

        await callback.message.edit_text(
            _crypto_text(course, uid),
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.message.reply_text(
            MSG.PROOF_ASK_PHONE.format(
                course_name = course["name"],
                currency    = course["currency"],
                price       = course["price"],
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=proof_phone_kb(course_id),
        )
        await callback.answer("🪙 Crypto নির্দেশনা")

    # ══════════════════════════════════════════════════════════
    #  Admin Contact — No Direct Payment
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(
        filters.regex(r"^cpay:admin:([a-f0-9]{24})$")
    )
    async def cb_pay_admin(
        client: Client, callback: CallbackQuery
    ):
        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)
        if not course:
            return await callback.answer(
                MSG.ERROR_COURSE_NOT_FOUND, show_alert=True
            )

        # Direct payment বন্ধ — শুধু technical support
        await callback.message.edit_text(
            MSG.NO_DIRECT_PAYMENT.format(
                support=SUPPORT_USERNAME
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔧 Technical Support Only",
                            url=f"https://t.me/"
                            f"{SUPPORT_USERNAME.lstrip('@')}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔙 Payment Method এ ফিরুন",
                            callback_data=f"cpay:back:{course_id}",
                        )
                    ],
                ]
            ),
            disable_web_page_preview=True,
        )
        await callback.answer()

    # ══════════════════════════════════════════════════════════
    #  Skip Phone Number
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(
        filters.regex(r"^proof:skip_phone:([a-f0-9]{24})$")
    )
    async def cb_skip_phone(
        client: Client, callback: CallbackQuery
    ):
        course_id = callback.matches[0].group(1)
        uid       = callback.from_user.id
        course    = await db.get_course_by_id(course_id)
        if not course:
            return await callback.answer(
                MSG.ERROR_COURSE_NOT_FOUND, show_alert=True
            )

        state = _proof_state.get(uid)
        if not state:
            return await callback.answer(
                "Session expired. আবার শুরু করুন।",
                show_alert=True,
            )

        state["phone"] = None
        state["step"]  = "screenshot"

        await callback.message.edit_text(
            MSG.PROOF_ASK_SCREENSHOT.format(
                course_name = course["name"],
                currency    = course["currency"],
                price       = course["price"],
                method      = state["method"],
                phone_line  = "",
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=proof_cancel_kb(course_id),
        )
        await callback.answer("⏭ Phone skip করা হয়েছে")

    # ══════════════════════════════════════════════════════════
    #  Message Handler — Phone Number & Screenshot
    # ══════════════════════════════════════════════════════════

    @app.on_message(
        filters.private
        & (filters.text | filters.photo | filters.document),
        group=15,
    )
    async def proof_input_handler(
        client: Client, message: Message
    ):
        uid   = message.from_user.id
        state = _proof_state.get(uid)

        if not state:
            return  # Proof flow এ নেই

        course_id = state.get("course_id")
        course    = await db.get_course_by_id(course_id)
        if not course:
            _proof_state.pop(uid, None)
            return

        step = state.get("step")

        # ── Step 1: Phone Number ───────────────────────────────
        if step == "phone" and message.text:
            phone = message.text.strip()

            # Basic validation
            if not (
                phone.startswith("01")
                and len(phone) == 11
                and phone.isdigit()
            ) and not (
                phone.startswith("+")
                and len(phone) > 8
            ):
                await message.reply_text(
                    "⚠️ Valid Phone Number দিন।\n"
                    "_e.g. 01712345678_\n\n"
                    "অথবা Skip করুন।",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=proof_phone_kb(course_id),
                )
                return

            state["phone"] = phone
            state["step"]  = "screenshot"

            phone_line = f"📱 **Phone:** `{phone}`\n"

            await message.reply_text(
                MSG.PROOF_ASK_SCREENSHOT.format(
                    course_name = course["name"],
                    currency    = course["currency"],
                    price       = course["price"],
                    method      = state["method"],
                    phone_line  = phone_line,
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=proof_cancel_kb(course_id),
            )

        # ── Step 2: Screenshot ─────────────────────────────────
        elif step == "screenshot" and (
            message.photo or message.document
        ):
            # File ID নাও
            if message.photo:
                file_id = message.photo.file_id
            else:
                file_id = message.document.file_id

            caption = message.caption or "No caption"
            phone   = state.get("phone") or "N/A"
            method  = state.get("method", "manual")
            user    = message.from_user

            username_str = (
                f"@{user.username}"
                if user.username else "@N/A"
            )

            # ── Duplicate proof check ──────────────────────────
            existing_proofs = await db.get_user_proofs(uid)
            pending = [
                p for p in existing_proofs
                if p.get("status") == "pending"
                and str(p.get("course_id")) == str(course_id)
            ]
            if pending:
                proof_id = str(pending[0]["_id"])
                await message.reply_text(
                    MSG.PROOF_ALREADY_PENDING.format(
                        course_name = course["name"],
                        proof_id    = proof_id[-8:],
                        support     = SUPPORT_USERNAME,
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )
                _proof_state.pop(uid, None)
                return

            # ── Proof save করো ────────────────────────────────
            proof_id = await db.save_payment_proof(
                {
                    "user_id":       uid,
                    "user_name":     user.first_name,
                    "username":      username_str,
                    "course_id":     course_id,
                    "course_name":   course["name"],
                    "amount":        course["price"],
                    "currency":      course["currency"],
                    "method":        method,
                    "phone_number":  phone,
                    "proof_file_id": file_id,
                    "proof_caption": caption,
                }
            )

            _proof_state.pop(uid, None)
            _pending_methods.pop(
                f"{uid}:{course_id}", None
            )

            LOGGER.info(
                f"[Proof] Submitted | "
                f"user={uid} course={course['name']} "
                f"method={method} proof={proof_id}"
            )

            # ── User কে confirm করো ───────────────────────────
            await message.reply_text(
                MSG.PROOF_SUBMITTED.format(
                    course_name = course["name"],
                    method      = method,
                    phone       = phone,
                    proof_id    = proof_id[-8:],
                    support     = SUPPORT_USERNAME,
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🏠 Main Menu",
                                callback_data="back:main",
                            )
                        ]
                    ]
                ),
            )

            # ── Admin দের proof পাঠাও ─────────────────────────
            admin_text = MSG.ADMIN_NEW_PROOF.format(
                user_name   = user.first_name,
                user_id     = uid,
                username    = username_str,
                phone       = phone,
                course_name = course["name"],
                currency    = course["currency"],
                price       = course["price"],
                method      = method,
                proof_id    = proof_id[-8:],
                caption     = caption,
            )

            for admin_id in ADMIN_IDS:
                try:
                    # Screenshot পাঠাও caption সহ
                    if message.photo:
                        await client.send_photo(
                            admin_id,
                            file_id,
                            caption=admin_text,
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=admin_proof_actions_kb(
                                proof_id
                            ),
                        )
                    else:
                        await client.send_document(
                            admin_id,
                            file_id,
                            caption=admin_text,
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=admin_proof_actions_kb(
                                proof_id
                            ),
                        )
                except Exception as e:
                    LOGGER.warning(
                        f"[Proof] Admin {admin_id} notify failed: {e}"
                    )

        # ── Text এসেছে কিন্তু screenshot step এ ──────────────
        elif step == "screenshot" and message.text:
            await message.reply_text(
                "⚠️ Screenshot বা Document পাঠান।\n"
                "Text দিয়ে হবে না।",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=proof_cancel_kb(course_id),
            )

    # ══════════════════════════════════════════════════════════
    #  Raw Update — Stars
    # ══════════════════════════════════════════════════════════

    app.add_handler(
        RawUpdateHandler(_raw_update_handler),
        group=5,
    )

    LOGGER.info("[Payment] Plugin loaded ✅")
