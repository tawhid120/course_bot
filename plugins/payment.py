# plugins/payment.py
# Copyright @YourChannel
# ─────────────────────────────────────────────────────────────
# Course Payment System
#
# Flow:
#   course detail → Buy Now → Payment Methods (buttons)
#     ├── ⭐ Telegram Stars  → auto invoice → auto activate
#     ├── 📲 bKash           → instructions → admin verify
#     ├── 📲 Nagad           → instructions → admin verify
#     ├── 🪙 Binance USDT    → instructions → admin verify
#     └── 💬 Contact Admin   → direct link  → manual
#
# Callback data pattern:
#   cpay:method:course_id
#   e.g. cpay:stars:64f1a2b3c4d5e6f7a8b9c0d1
#        cpay:bkash:64f1a2b3c4d5e6f7a8b9c0d1
#        cpay:nagad:64f1a2b3c4d5e6f7a8b9c0d1
#        cpay:crypto:64f1a2b3c4d5e6f7a8b9c0d1
#        cpay:admin:64f1a2b3c4d5e6f7a8b9c0d1
#        cpay:done:course_id        (manual payment submitted)
#        cpay:back:course_id        (back to method selection)
# ─────────────────────────────────────────────────────────────

import hashlib
import time
import uuid
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.handlers import RawUpdateHandler
from pyrogram.raw.functions.messages import SendMedia, SetBotPrecheckoutResults
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
from misc import (
    States,
    clear_state,
    course_detail_inline,
    main_menu_inline,
)
from utils import LOGGER

# ═════════════════════════════════════════════════════════════
#  In-memory invoice tracker (prevent duplicate invoices)
# ═════════════════════════════════════════════════════════════
_active_invoices: dict = {}


# ═════════════════════════════════════════════════════════════
#  KEYBOARDS
# ═════════════════════════════════════════════════════════════

def payment_methods_kb(course_id: str) -> InlineKeyboardMarkup:
    """
    সব payment method বাটন হিসেবে দেখায়।
    প্রতিটা বাটন আলাদা method এর জন্য।
    """
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⭐ Telegram Stars — তাৎক্ষণিক",
                    callback_data=f"cpay:stars:{course_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "📲 bKash",
                    callback_data=f"cpay:bkash:{course_id}",
                ),
                InlineKeyboardButton(
                    "📲 Nagad",
                    callback_data=f"cpay:nagad:{course_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🪙 Binance / USDT (TRC20)",
                    callback_data=f"cpay:crypto:{course_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "💬 সরাসরি Admin কে Message করুন",
                    callback_data=f"cpay:admin:{course_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Course এ ফিরে যাও",
                    callback_data=f"course:{course_id}",
                )
            ],
        ]
    )


def after_manual_payment_kb(course_id: str) -> InlineKeyboardMarkup:
    """Manual payment submit করার পর দেখায়।"""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Payment করেছি — Confirm করুন",
                    callback_data=f"cpay:done:{course_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Payment Method বেছে নিন",
                    callback_data=f"cpay:back:{course_id}",
                )
            ],
        ]
    )


def admin_order_kb(order_id: str) -> InlineKeyboardMarkup:
    """Admin দের জন্য order approve/reject বাটন।"""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Approve করুন",
                    callback_data=f"admin:approve_order:{order_id}",
                ),
                InlineKeyboardButton(
                    "❌ Reject করুন",
                    callback_data=f"admin:reject_order:{order_id}",
                ),
            ]
        ]
    )


# ═════════════════════════════════════════════════════════════
#  TEXT TEMPLATES
# ═════════════════════════════════════════════════════════════

def _payment_menu_text(course: dict) -> str:
    return (
        f"💳 **Payment — {course['name']}**\n\n"
        f"💰 **মূল্য:** `{course['currency']} {course['price']}`\n\n"
        f"নিচের যেকোনো পদ্ধতিতে পেমেন্ট করুন 👇\n\n"
        f"⭐ **Telegram Stars** — পেমেন্টের সাথে সাথেই একটিভ হবে\n"
        f"📲 **bKash / Nagad** — বাংলাদেশী মোবাইল ব্যাংকিং\n"
        f"🪙 **Binance USDT** — Crypto পেমেন্ট\n"
        f"💬 **Admin Contact** — অন্য যেকোনো ব্যবস্থা\n\n"
        f"💬 সাহায্যের জন্য: {ADMIN_USERNAME}"
    )


def _bkash_text(course: dict, user_id: int) -> str:
    return (
        f"📲 **bKash Payment**\n\n"
        f"**━━━━━━━━━━━━━━━━━━━━━**\n"
        f"📦 **Course:** `{course['name']}`\n"
        f"💰 **Amount:** `{course['price']} {course['currency']}`\n"
        f"**━━━━━━━━━━━━━━━━━━━━━**\n\n"
        f"📲 **bKash নম্বর:** `{BKASH_NUMBER}`\n"
        f"📋 **Type:** `Send Money`\n"
        f"📝 **Reference:** `{user_id}`\n\n"
        f"**📌 ধাপে ধাপে নির্দেশনা:**\n"
        f"1️⃣ bKash App খুলুন\n"
        f"2️⃣ **Send Money** তে tap করুন\n"
        f"3️⃣ নম্বর দিন: `{BKASH_NUMBER}`\n"
        f"4️⃣ পরিমাণ দিন: `{course['price']} {course['currency']}`\n"
        f"5️⃣ Reference এ দিন: `{user_id}`\n"
        f"6️⃣ পেমেন্ট সম্পন্ন করুন\n\n"
        f"✅ পেমেন্টের পর নিচের বাটনে ক্লিক করুন\n\n"
        f"📞 সাহায্য: {ADMIN_USERNAME}"
    )


def _nagad_text(course: dict, user_id: int) -> str:
    return (
        f"📲 **Nagad Payment**\n\n"
        f"**━━━━━━━━━━━━━━━━━━━━━**\n"
        f"📦 **Course:** `{course['name']}`\n"
        f"💰 **Amount:** `{course['price']} {course['currency']}`\n"
        f"**━━━━━━━━━━━━━━━━━━━━━**\n\n"
        f"📲 **Nagad নম্বর:** `{NAGAD_NUMBER}`\n"
        f"📋 **Type:** `Send Money`\n"
        f"📝 **Reference:** `{user_id}`\n\n"
        f"**📌 ধাপে ধাপে নির্দেশনা:**\n"
        f"1️⃣ Nagad App খুলুন\n"
        f"2️⃣ **Send Money** তে tap করুন\n"
        f"3️⃣ নম্বর দিন: `{NAGAD_NUMBER}`\n"
        f"4️⃣ পরিমাণ দিন: `{course['price']} {course['currency']}`\n"
        f"5️⃣ Reference এ দিন: `{user_id}`\n"
        f"6️⃣ পেমেন্ট সম্পন্ন করুন\n\n"
        f"✅ পেমেন্টের পর নিচের বাটনে ক্লিক করুন\n\n"
        f"📞 সাহায্য: {ADMIN_USERNAME}"
    )


def _crypto_text(course: dict, user_id: int) -> str:
    return (
        f"🪙 **Binance / USDT (TRC20) Payment**\n\n"
        f"**━━━━━━━━━━━━━━━━━━━━━**\n"
        f"📦 **Course:** `{course['name']}`\n"
        f"💰 **Amount:** `{course['price']} {course['currency']}`\n"
        f"**━━━━━━━━━━━━━━━━━━━━━**\n\n"
        f"🆔 **Binance UID:** `{BINANCE_UID}`\n"
        f"📬 **TRC20 Address:**\n`{BINANCE_ADDRESS}`\n"
        f"🔗 **Network:** `USDT (TRC20)`\n"
        f"📝 **Memo / Note:** `{user_id}`\n\n"
        f"**📌 ধাপে ধাপে নির্দেশনা:**\n"
        f"1️⃣ Binance বা যেকোনো USDT wallet খুলুন\n"
        f"2️⃣ **Send / Transfer** এ যান\n"
        f"3️⃣ **USDT** → **TRC20** নেটওয়ার্ক বেছে নিন\n"
        f"4️⃣ Address দিন: `{BINANCE_ADDRESS}`\n"
        f"5️⃣ Amount দিন: `{course['price']} {course['currency']}`\n"
        f"6️⃣ Memo তে দিন: `{user_id}`\n"
        f"7️⃣ Transaction সম্পন্ন করুন\n\n"
        f"✅ পেমেন্টের পর নিচের বাটনে ক্লিক করুন\n\n"
        f"📞 সাহায্য: {ADMIN_USERNAME}"
    )


def _admin_contact_text(course: dict) -> str:
    return (
        f"💬 **Admin Contact — অন্য পেমেন্ট পদ্ধতি**\n\n"
        f"**━━━━━━━━━━━━━━━━━━━━━**\n"
        f"📦 **Course:** `{course['name']}`\n"
        f"💰 **Price:** `{course['currency']} {course['price']}`\n"
        f"**━━━━━━━━━━━━━━━━━━━━━**\n\n"
        f"উপরের কোনো পদ্ধতি আপনার জন্য suitable না?\n"
        f"Admin কে সরাসরি message করুন।\n\n"
        f"👤 **Admin:** {ADMIN_USERNAME}\n\n"
        f"💡 **অন্যান্য গ্রহণযোগ্য পদ্ধতি:**\n"
        f"• 🏦 Bank Transfer\n"
        f"• 💵 অন্যান্য Mobile Banking\n"
        f"• 🤝 পারস্পরিক সমঝোতায় যেকোনো ব্যবস্থা\n\n"
        f"🇧🇩 আমরা বাংলাদেশি — আপনাকে সাহায্য করতে"
        f" সর্বদা প্রস্তুত!"
    )


def _stars_success_text(
    course: dict,
    user_name: str,
    amount: int,
    tx_id: str,
) -> str:
    return (
        f"✅ **Payment সফল! Course একটিভ হয়েছে!**\n\n"
        f"🎉 ধন্যবাদ, **{user_name}**!\n\n"
        f"📦 **Course:** `{course['name']}`\n"
        f"⭐ **Stars Paid:** `{amount}`\n"
        f"🧾 **Transaction ID:** `{tx_id}`\n\n"
        f"🚀 আপনার course এখন **একটিভ**!\n\n"
        f"সাহায্যের জন্য: {ADMIN_USERNAME} 💎"
    )


def _manual_submitted_text(
    course: dict, method: str, user_id: int
) -> str:
    method_names = {
        "bkash":  "bKash",
        "nagad":  "Nagad",
        "crypto": "Binance / USDT",
    }
    return (
        f"✅ **Payment Submit হয়েছে!**\n\n"
        f"📦 **Course:** `{course['name']}`\n"
        f"💳 **Method:** `{method_names.get(method, method)}`\n"
        f"👤 **User ID:** `{user_id}`\n\n"
        f"⏳ Admin আপনার payment verify করে\n"
        f"অ্যাক্সেস দেবেন — সাধারণত কয়েক মিনিটের মধ্যে।\n\n"
        f"📞 প্রয়োজনে contact করুন: {ADMIN_USERNAME}"
    )


def _admin_manual_notify(
    course: dict,
    user_id: int,
    username: str,
    user_name: str,
    method: str,
    order_id: str,
) -> str:
    method_names = {
        "bkash":  "📲 bKash",
        "nagad":  "📲 Nagad",
        "crypto": "🪙 Binance / USDT",
    }
    return (
        f"🔔 **নতুন Manual Payment!**\n\n"
        f"👤 **User:** [{user_name}](tg://user?id={user_id})"
        f" (`{user_id}`)\n"
        f"📛 **Username:** {username}\n"
        f"📦 **Course:** {course['name']}\n"
        f"💰 **Amount:** {course['currency']} {course['price']}\n"
        f"💳 **Method:** {method_names.get(method, method)}\n"
        f"🆔 **Order ID:** `{order_id}`\n\n"
        f"⬇️ Verify করে Approve বা Reject করুন:"
    )


# ═════════════════════════════════════════════════════════════
#  Stars Invoice Generator
# ═════════════════════════════════════════════════════════════

async def _send_stars_invoice(
    client: Client,
    chat_id: int,
    user_id: int,
    course: dict,
    course_id: str,
) -> None:
    """
    Telegram Stars invoice generate করে send করে।
    Currency: XTR (Telegram Stars)
    Amount: course price (INR/BDT এর পরিবর্তে Stars সংখ্যা)
    """
    if _active_invoices.get(user_id):
        await client.send_message(
            chat_id,
            "⚠️ **আরেকটি invoice ইতিমধ্যে active আছে!**\n\n"
            "আগের invoice complete বা cancel করুন।",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Stars amount = price কে integer হিসেবে use করো
    # যদি currency INR/BDT হয় তাহলে conversion করো
    # এখানে আমরা price কে সরাসরি stars হিসেবে use করছি
    # Admin কোর্স add করার সময় currency="XTR" দিলে সরাসরি কাজ করবে
    try:
        stars_amount = int(float(course["price"]))
    except (ValueError, TypeError):
        stars_amount = 1

    loading = await client.send_message(
        chat_id,
        f"⏳ **{course['name']} এর Stars invoice তৈরি হচ্ছে...**",
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
                hashlib.sha256(payload_str.encode()).hexdigest(),
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
            recurring=False,
            test=False,
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
            f"✅ **Invoice Ready — {course['name']}**\n\n"
            f"⭐ **{stars_amount} Stars** দিয়ে কিনুন\n\n"
            f"উপরের **Pay** বাটনে tap করুন।\n"
            f"পেমেন্টের সাথে সাথেই access একটিভ হবে! 🚀",
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

        LOGGER.info(
            f"[Stars] Invoice sent | "
            f"user={user_id} course={course['name']} "
            f"stars={stars_amount}"
        )

    except Exception as e:
        LOGGER.error(
            f"[Stars] Invoice failed | user={user_id} error={e}"
        )
        await client.edit_message_text(
            chat_id,
            loading.id,
            "❌ **Stars invoice তৈরি করতে সমস্যা হয়েছে।**\n\n"
            "অন্য payment পদ্ধতি ব্যবহার করুন।",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=payment_methods_kb(course_id),
        )
    finally:
        _active_invoices.pop(user_id, None)


# ═════════════════════════════════════════════════════════════
#  Raw Update Handler — Stars Pre-checkout & Payment Success
# ═════════════════════════════════════════════════════════════

async def _raw_update_handler(
    client: Client, update, users, chats
) -> None:

    # ── Pre-checkout approve ───────────────────────────────────
    if isinstance(update, UpdateBotPrecheckoutQuery):
        try:
            await client.invoke(
                SetBotPrecheckoutResults(
                    query_id=update.query_id,
                    success=True,
                )
            )
            LOGGER.info(
                f"[PreCheckout] Approved "
                f"query_id={update.query_id} "
                f"user={update.user_id}"
            )
        except Exception as e:
            LOGGER.error(f"[PreCheckout] Failed: {e}")
            try:
                await client.invoke(
                    SetBotPrecheckoutResults(
                        query_id=update.query_id,
                        success=False,
                        error="Payment processing error. Try again.",
                    )
                )
            except Exception:
                pass
        return

    # ── Payment Success ────────────────────────────────────────
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
        # ── Resolve user_id ───────────────────────────────────
        user_id = None
        if update.message.from_id and hasattr(
            update.message.from_id, "user_id"
        ):
            user_id = update.message.from_id.user_id
        if not user_id and users:
            positives = [u for u in users if u > 0]
            user_id   = positives[0] if positives else None
        if not user_id:
            LOGGER.error("[Payment] Cannot resolve user_id")
            return

        # ── Resolve chat_id ───────────────────────────────────
        pid = update.message.peer_id
        if isinstance(pid, PeerUser):
            chat_id = pid.user_id
        elif isinstance(pid, PeerChat):
            chat_id = pid.chat_id
        elif isinstance(pid, PeerChannel):
            chat_id = pid.channel_id
        else:
            chat_id = user_id

        # ── Parse payload ─────────────────────────────────────
        payload = payment.payload.decode()
        # format: course_{course_id}_{user_id}_{stars}_{ts}_{uid}
        parts = payload.split("_")
        if len(parts) < 3 or parts[0] != "course":
            LOGGER.error(
                f"[Payment] Unknown payload: {payload}"
            )
            return

        course_id   = parts[1]
        tx_id       = payment.charge.id
        amount_paid = payment.total_amount

        # ── Get course from DB ─────────────────────────────────
        course = await db.get_course_by_id(course_id)
        if not course:
            LOGGER.error(
                f"[Payment] Course not found: {course_id}"
            )
            return

        # ── User info ─────────────────────────────────────────
        user_info = users.get(user_id)
        full_name = (
            f"{user_info.first_name} "
            f"{getattr(user_info, 'last_name', '') or ''}".strip()
            if user_info
            else "User"
        )
        username = (
            f"@{user_info.username}"
            if user_info and user_info.username
            else "@N/A"
        )

        LOGGER.info(
            f"[Payment] ⭐ Stars received | "
            f"user={user_id} course={course['name']} "
            f"amount={amount_paid} tx={tx_id}"
        )

        # ── Create approved order in DB ───────────────────────
        order_id = await db.create_order(
            {
                "user_id":     user_id,
                "user_name":   full_name,
                "username":    username,
                "course_id":   course_id,
                "course_name": course["name"],
                "amount":      amount_paid,
                "currency":    "XTR",
                "method":      "telegram_stars",
                "tx_id":       tx_id,
                "status":      "approved",  # Stars = instant approve
            }
        )

        # ── Notify user ───────────────────────────────────────
        try:
            await client.send_message(
                chat_id=chat_id,
                text=_stars_success_text(
                    course, full_name, amount_paid, tx_id
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu_inline(),
            )
        except Exception as e:
            LOGGER.error(
                f"[Payment] User notify failed: {e}"
            )

        # ── Notify admins ─────────────────────────────────────
        admin_text = (
            f"⭐ **Stars Payment Received!**\n\n"
            f"👤 **User:** [{full_name}]"
            f"(tg://user?id={user_id}) (`{user_id}`)\n"
            f"📛 **Username:** {username}\n"
            f"📦 **Course:** {course['name']}\n"
            f"⭐ **Stars:** {amount_paid}\n"
            f"🧾 **TX ID:** `{tx_id}`\n"
            f"🆔 **Order ID:** `{order_id}`\n"
            f"✅ **Status:** Auto Approved"
        )
        for admin_id in ADMIN_IDS:
            try:
                await client.send_message(
                    admin_id,
                    admin_text,
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception as e:
                LOGGER.warning(
                    f"[Payment] Admin {admin_id} notify failed: {e}"
                )

        LOGGER.info(
            f"[Payment] ✅ Auto-approved | "
            f"user={user_id} course={course['name']} "
            f"order={order_id}"
        )

    except Exception as e:
        LOGGER.error(f"[Payment] Unhandled error: {e}")
        try:
            await client.send_message(
                chat_id=user_id,
                text=(
                    "⚠️ **Payment received কিন্তু activation এ সমস্যা হয়েছে।**\n\n"
                    f"Transaction ID সহ admin কে জানান:\n"
                    f"{ADMIN_USERNAME}"
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass


# ═════════════════════════════════════════════════════════════
#  setup(app)
# ═════════════════════════════════════════════════════════════

def setup(app: Client) -> None:
    """
    plugins/__init__.py এর _PLUGIN_SETUPS থেকে call হয়।
    সব payment handler এখানে register হয়।
    """

    # ══════════════════════════════════════════════════════════
    #  Callback — Buy Now → Payment Method Screen
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(
        filters.regex(r"^buy:([a-f0-9]{24})$")
    )
    async def cb_buy_now(client: Client, callback: CallbackQuery):
        """
        course_flow.py এর buy: callback কে override করে।
        এখন payment method selection screen দেখাবে।
        """
        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)

        if not course:
            await callback.answer(
                "⚠️ Course পাওয়া যায়নি।", show_alert=True
            )
            return

        await callback.message.edit_text(
            _payment_menu_text(course),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=payment_methods_kb(course_id),
        )
        await callback.answer()

    # ══════════════════════════════════════════════════════════
    #  Callback — cpay:back → Payment Method Screen এ ফিরুন
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
            await callback.answer(
                "⚠️ Course পাওয়া যায়নি।", show_alert=True
            )
            return

        await callback.message.edit_text(
            _payment_menu_text(course),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=payment_methods_kb(course_id),
        )
        await callback.answer()

    # ══════════════════════════════════════════════════════════
    #  Callback — cpay:stars → Telegram Stars Invoice
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
            await callback.answer(
                "⚠️ Course পাওয়া যায়নি।", show_alert=True
            )
            return

        uid     = callback.from_user.id
        chat_id = callback.message.chat.id

        await callback.answer(
            f"⭐ Stars invoice তৈরি হচ্ছে..."
        )

        await _send_stars_invoice(
            client, chat_id, uid, course, course_id
        )

    # ══════════════════════════════════════════════════════════
    #  Callback — cpay:bkash → bKash Instructions
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
            await callback.answer(
                "⚠️ Course পাওয়া যায়নি।", show_alert=True
            )
            return

        uid = callback.from_user.id

        # pending_method store করো next step এর জন্য
        await _store_pending_method(uid, course_id, "bkash")

        await callback.message.edit_text(
            _bkash_text(course, uid),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=after_manual_payment_kb(course_id),
        )
        await callback.answer("📲 bKash নির্দেশনা")

    # ══════════════════════════════════════════════════════════
    #  Callback — cpay:nagad → Nagad Instructions
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
            await callback.answer(
                "⚠️ Course পাওয়া যায়নি।", show_alert=True
            )
            return

        uid = callback.from_user.id
        await _store_pending_method(uid, course_id, "nagad")

        await callback.message.edit_text(
            _nagad_text(course, uid),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=after_manual_payment_kb(course_id),
        )
        await callback.answer("📲 Nagad নির্দেশনা")

    # ══════════════════════════════════════════════════════════
    #  Callback — cpay:crypto → Binance Instructions
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
            await callback.answer(
                "⚠️ Course পাওয়া যায়নি।", show_alert=True
            )
            return

        uid = callback.from_user.id
        await _store_pending_method(uid, course_id, "crypto")

        await callback.message.edit_text(
            _crypto_text(course, uid),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=after_manual_payment_kb(course_id),
        )
        await callback.answer("🪙 Crypto নির্দেশনা")

    # ══════════════════════════════════════════════════════════
    #  Callback — cpay:admin → Admin Contact
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
            await callback.answer(
                "⚠️ Course পাওয়া যায়নি।", show_alert=True
            )
            return

        await callback.message.edit_text(
            _admin_contact_text(course),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            f"💬 {ADMIN_USERNAME} কে Message করুন",
                            url=f"https://t.me/"
                            f"{ADMIN_USERNAME.lstrip('@')}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔙 Payment Method এ ফিরুন",
                            callback_data=f"cpay:back:{course_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🏠 Main Menu",
                            callback_data="back:main",
                        )
                    ],
                ]
            ),
            disable_web_page_preview=True,
        )
        await callback.answer("💬 Admin contact")

    # ══════════════════════════════════════════════════════════
    #  Callback — cpay:done → Manual Payment Submitted
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(
        filters.regex(r"^cpay:done:([a-f0-9]{24})$")
    )
    async def cb_payment_done(
        client: Client, callback: CallbackQuery
    ):
        course_id = callback.matches[0].group(1)
        course    = await db.get_course_by_id(course_id)

        if not course:
            await callback.answer(
                "⚠️ Course পাওয়া যায়নি।", show_alert=True
            )
            return

        uid  = callback.from_user.id
        user = callback.from_user

        # কোন method use করেছে সেটা retrieve করো
        method = _get_pending_method(uid, course_id)

        # Pending order create করো
        order_id = await db.create_order(
            {
                "user_id":     uid,
                "user_name":   user.first_name,
                "username":    user.username,
                "course_id":   course_id,
                "course_name": course["name"],
                "amount":      course["price"],
                "currency":    course["currency"],
                "method":      method or "manual",
                "status":      "pending",
            }
        )

        clear_state(uid)
        _clear_pending_method(uid, course_id)

        LOGGER.info(
            f"[Payment] Manual submitted | "
            f"user={uid} course={course['name']} "
            f"method={method} order={order_id}"
        )

        # User কে confirm করো
        await callback.message.edit_text(
            _manual_submitted_text(
                course, method or "manual", uid
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            f"💬 {ADMIN_USERNAME}",
                            url=f"https://t.me/"
                            f"{ADMIN_USERNAME.lstrip('@')}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🏠 Main Menu",
                            callback_data="back:main",
                        )
                    ],
                ]
            ),
        )

        # সব admin কে notify করো
        username_str = (
            f"@{user.username}" if user.username else "@N/A"
        )
        admin_text = _admin_manual_notify(
            course, uid, username_str,
            user.first_name, method or "manual", order_id,
        )
        for admin_id in ADMIN_IDS:
            try:
                await client.send_message(
                    admin_id,
                    admin_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=admin_order_kb(order_id),
                )
            except Exception as e:
                LOGGER.warning(
                    f"[Payment] Admin {admin_id} notify failed: {e}"
                )

        await callback.answer("✅ Payment submit হয়েছে!")

    # ══════════════════════════════════════════════════════════
    #  Raw Update — Stars pre-checkout & success
    # ══════════════════════════════════════════════════════════

    app.add_handler(
        RawUpdateHandler(_raw_update_handler),
        group=5,
    )

    LOGGER.info("[Payment] Payment plugin loaded ✅")


# ═════════════════════════════════════════════════════════════
#  In-memory pending method store
#  (কোন user কোন method select করেছে track রাখে)
# ═════════════════════════════════════════════════════════════

_pending_methods: dict = {}


async def _store_pending_method(
    user_id: int, course_id: str, method: str
) -> None:
    _pending_methods[f"{user_id}:{course_id}"] = method


def _get_pending_method(
    user_id: int, course_id: str
) -> str | None:
    return _pending_methods.get(f"{user_id}:{course_id}")


def _clear_pending_method(
    user_id: int, course_id: str
) -> None:
    _pending_methods.pop(f"{user_id}:{course_id}", None)
