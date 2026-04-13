# auth/force_sub.py
# Copyright @YourChannel
# ─────────────────────────────────────────────────────────────
# Force Subscribe System
# ✅ FIXED: setup_force_sub_handler এখন _AUTH_SETUPS এ আছে
# ✅ FIXED: stop_propagation() সঠিক জায়গায়
# ✅ OPTIMIZED: TTL cache (member=5min, non-member=15sec)
# ✅ OPTIMIZED: API timeout with asyncio.wait_for()
# ─────────────────────────────────────────────────────────────

import asyncio
import time

from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.errors import (
    ChannelPrivate,
    ChatAdminRequired,
    FloodWait,
    PeerIdInvalid,
    UserNotParticipant,
)
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import ADMIN_IDS, FORCE_SUB_CHANNEL, SUPPORT_USERNAME
from utils import LOGGER

# ═══════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════

CACHE_TTL            = 300   # 5 মিনিট — member user
NOT_JOINED_CACHE_TTL = 15    # 15 সেকেন্ড — non-member
API_TIMEOUT          = 5.0
_CHECK_CB            = "fsub_check"

# ═══════════════════════════════════════════════
#  CHANNEL SETUP
# ═══════════════════════════════════════════════

_raw = str(FORCE_SUB_CHANNEL).strip() if FORCE_SUB_CHANNEL else None

if _raw:
    if _raw.startswith("-100"):
        # Private channel — numeric ID
        API_CHANNEL  = int(_raw)
        CHANNEL_LINK = f"https://t.me/c/{_raw.lstrip('-100')}"
    elif _raw.startswith("@"):
        API_CHANNEL  = _raw
        CHANNEL_LINK = f"https://t.me/{_raw.lstrip('@')}"
    else:
        API_CHANNEL  = f"@{_raw}"
        CHANNEL_LINK = f"https://t.me/{_raw}"
else:
    API_CHANNEL  = None
    CHANNEL_LINK = ""

# ═══════════════════════════════════════════════
#  IN-MEMORY TTL CACHE
# ═══════════════════════════════════════════════

_cache: dict[int, tuple[bool, float]] = {}


def _cache_get(user_id: int) -> bool | None:
    entry = _cache.get(user_id)
    if entry is None:
        return None
    is_sub, ts = entry
    ttl = CACHE_TTL if is_sub else NOT_JOINED_CACHE_TTL
    if time.monotonic() - ts < ttl:
        return is_sub
    _cache.pop(user_id, None)
    return None


def _cache_set(user_id: int, is_sub: bool) -> None:
    _cache[user_id] = (is_sub, time.monotonic())


def _cache_clear(user_id: int) -> None:
    _cache.pop(user_id, None)


# ═══════════════════════════════════════════════
#  CORE CHECK
# ═══════════════════════════════════════════════

async def check_subscription(
    client: Client,
    user_id: int,
    refresh: bool = False,
) -> bool:
    """
    True  → member অথবা Force Sub disabled
    False → member না
    """
    if not API_CHANNEL:
        return True

    if user_id in ADMIN_IDS:
        return True

    if not refresh:
        cached = _cache_get(user_id)
        if cached is not None:
            return cached

    try:
        member = await asyncio.wait_for(
            client.get_chat_member(API_CHANNEL, user_id),
            timeout=API_TIMEOUT,
        )
        is_sub = member.status not in (
            ChatMemberStatus.BANNED,
            ChatMemberStatus.LEFT,
        )
        _cache_set(user_id, is_sub)
        return is_sub

    except UserNotParticipant:
        _cache_set(user_id, False)
        return False

    except (ChatAdminRequired, ChannelPrivate, PeerIdInvalid) as e:
        LOGGER.error(f"[ForceSub] Channel error | channel={API_CHANNEL} | {e}")
        return True  # Fail open

    except FloodWait as e:
        wait = min(e.value, 5)
        LOGGER.warning(f"[ForceSub] FloodWait {e.value}s | user={user_id}")
        await asyncio.sleep(wait)
        return True

    except asyncio.TimeoutError:
        LOGGER.warning(f"[ForceSub] API timeout | user={user_id}")
        return True

    except Exception as e:
        LOGGER.error(f"[ForceSub] Unexpected error | user={user_id} | {e}")
        return True


# ═══════════════════════════════════════════════
#  UI
# ═══════════════════════════════════════════════

def _join_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "📢 Channel এ Join করুন",
            url=CHANNEL_LINK,
        )],
        [InlineKeyboardButton(
            "✅ Join করেছি — Continue",
            callback_data=_CHECK_CB,
        )],
    ])


_NOT_SUBSCRIBED_TEXT = (
    "🔒 **Access Restricted**\n\n"
    "এই Bot ব্যবহার করতে আমাদের\n"
    "Official Channel এ Join করতে হবে।\n\n"
    "👇 নিচের বাটনে ক্লিক করে Join করুন,\n"
    "তারপর **✅ Join করেছি — Continue** চাপুন।\n\n"
    f"📞 সাহায্য: {SUPPORT_USERNAME}"
)


# ═══════════════════════════════════════════════
#  SETUP — main entry point
# ═══════════════════════════════════════════════

def setup_force_sub_handler(app: Client) -> None:
    """
    auth/__init__.py → _AUTH_SETUPS থেকে call হয়।
    group=-1 → সব handler এর আগে চলে (interceptor)
    group=0  → normal ("I Joined" button)
    """
    if not API_CHANNEL:
        LOGGER.info("[ForceSub] Disabled — FORCE_SUB_CHANNEL not set")
        return

    # ── Message Interceptor ──────────────────────

    @app.on_message(
        filters.private & ~filters.service,
        group=-1,
    )
    async def _msg_interceptor(client: Client, message: Message):
        if not message.from_user:
            return

        user_id = message.from_user.id

        if user_id in ADMIN_IDS:
            return

        is_sub = await check_subscription(client, user_id)

        if not is_sub:
            await message.reply_text(
                _NOT_SUBSCRIBED_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=_join_keyboard(),
                disable_web_page_preview=True,
            )
            message.stop_propagation()  # ✅

    # ── Callback Interceptor ─────────────────────

    @app.on_callback_query(
        ~filters.regex(f"^{_CHECK_CB}$"),
        group=-1,
    )
    async def _cb_interceptor(client: Client, callback: CallbackQuery):
        if not callback.from_user:
            return

        user_id = callback.from_user.id

        if user_id in ADMIN_IDS:
            return

        is_sub = await check_subscription(client, user_id)

        if not is_sub:
            await callback.answer(
                "📢 আগে Channel এ Join করুন!",
                show_alert=True,
            )
            try:
                await callback.message.reply_text(
                    _NOT_SUBSCRIBED_TEXT,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=_join_keyboard(),
                    disable_web_page_preview=True,
                )
            except Exception:
                pass
            callback.stop_propagation()  # ✅

    # ── "Join করেছি" Button Handler ──────────────

    @app.on_callback_query(
        filters.regex(f"^{_CHECK_CB}$"),
        group=0,
    )
    async def _check_joined(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id

        _cache_clear(user_id)
        is_sub = await check_subscription(client, user_id, refresh=True)

        if is_sub:
            try:
                await callback.message.delete()
            except Exception:
                pass

            await callback.answer(
                "✅ Verified! এখন Bot ব্যবহার করতে পারবেন।",
                show_alert=True,
            )
            LOGGER.info(f"[ForceSub] ✅ Verified | user={user_id}")

            try:
                await client.send_message(
                    user_id,
                    "✅ **Channel Verification সফল!**\n\n"
                    "এখন Bot এর সব Feature ব্যবহার করতে পারবেন। 🎉",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            "🏠 Main Menu",
                            callback_data="back:main",
                        )],
                    ]),
                )
            except Exception as e:
                LOGGER.warning(f"[ForceSub] Welcome msg failed | user={user_id}: {e}")

        else:
            await callback.answer(
                "❌ এখনো Channel এ Join করেননি!\nJoin করুন তারপর আবার try করুন।",
                show_alert=True,
            )
            LOGGER.info(f"[ForceSub] ❌ Not joined | user={user_id}")

    LOGGER.info(
        f"[ForceSub] ✅ Enabled | Channel: {API_CHANNEL} | Link: {CHANNEL_LINK}"
    )
