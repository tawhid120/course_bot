# auth/force_sub.py
# Copyright @YourChannel
# ─────────────────────────────────────────────────────────────
# Force Subscribe System
#
# কীভাবে কাজ করে:
#   • Bot এ যেকোনো message/button আসলে আগে check করে
#     user ঐ channel এ member কিনা
#   • Member না হলে Join করতে বলে — বট block হয়
#   • "I Joined" বাটনে click করলে fresh check করে
#   • In-memory TTL cache — একই user বারবার check হয় না
#
# Features:
#   ✅ TTL Cache (5 মিনিট member, 15 সেকেন্ড non-member)
#   ✅ API Timeout protection
#   ✅ FloodWait handling
#   ✅ Admin সবসময় bypass করতে পারে
#   ✅ Disabled করা যায় .env থেকে
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

# ═════════════════════════════════════════════════════════════
#  CONFIG
# ═════════════════════════════════════════════════════════════

# Cache lifetime
CACHE_TTL             = 300   # 5 মিনিট — member user
NOT_JOINED_CACHE_TTL  = 15    # 15 সেকেন্ড — non-member user

# API timeout
API_TIMEOUT = 5.0

# Callback data
_CHECK_CB = "fsub_check"

# ═════════════════════════════════════════════════════════════
#  CHANNEL SETUP
# ═════════════════════════════════════════════════════════════

if FORCE_SUB_CHANNEL:
    _raw = str(FORCE_SUB_CHANNEL).strip()

    # API call এর জন্য @ prefix দরকার
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

# ═════════════════════════════════════════════════════════════
#  IN-MEMORY TTL CACHE
#  Structure: { user_id: (is_subscribed, timestamp) }
# ═════════════════════════════════════════════════════════════

_cache: dict[int, tuple[bool, float]] = {}


def _cache_get(user_id: int) -> bool | None:
    """Cache থেকে result পড়ো। Miss হলে None।"""
    entry = _cache.get(user_id)
    if entry is None:
        return None
    is_sub, ts = entry
    ttl = CACHE_TTL if is_sub else NOT_JOINED_CACHE_TTL
    if time.monotonic() - ts < ttl:
        return is_sub
    # Expired
    _cache.pop(user_id, None)
    return None


def _cache_set(user_id: int, is_sub: bool) -> None:
    _cache[user_id] = (is_sub, time.monotonic())


def _cache_clear(user_id: int) -> None:
    """User join করলে বা fresh check দরকার হলে clear করো।"""
    _cache.pop(user_id, None)


# ═════════════════════════════════════════════════════════════
#  CORE CHECK FUNCTION
# ═════════════════════════════════════════════════════════════

async def check_subscription(
    client: Client,
    user_id: int,
    refresh: bool = False,
) -> bool:
    """
    User ঐ channel এ member কিনা check করে।

    Args:
        client  : Pyrogram Client
        user_id : Telegram User ID
        refresh : True হলে cache bypass করে fresh check

    Returns:
        True  → member অথবা Force Sub disabled
        False → member না
    """
    # Force Sub disabled থাকলে সবাইকে allow করো
    if not API_CHANNEL:
        return True

    # Admin সবসময় allowed
    if user_id in ADMIN_IDS:
        return True

    # Cache check (refresh=False হলে)
    if not refresh:
        cached = _cache_get(user_id)
        if cached is not None:
            return cached

    # ── Telegram API Call ─────────────────────────────────────
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
        # Bot channel এ admin নয় বা channel ভুল
        # Fail open — user কে allow করো
        LOGGER.error(
            f"[ForceSub] Channel error | "
            f"channel={API_CHANNEL} error={e}"
        )
        return True

    except FloodWait as e:
        wait = min(e.value, 5)
        LOGGER.warning(
            f"[ForceSub] FloodWait {e.value}s | "
            f"user={user_id} — allowing after {wait}s"
        )
        await asyncio.sleep(wait)
        return True  # Flood এ user block না করে allow করো

    except asyncio.TimeoutError:
        LOGGER.warning(
            f"[ForceSub] API timeout | "
            f"user={user_id} — allowing"
        )
        return True  # Timeout এ allow করো

    except Exception as e:
        LOGGER.error(
            f"[ForceSub] Unexpected error | "
            f"user={user_id} error={e}"
        )
        return True  # Unknown error — fail open


# ═════════════════════════════════════════════════════════════
#  UI — Keyboard & Message
# ═════════════════════════════════════════════════════════════

def _join_keyboard() -> InlineKeyboardMarkup:
    """Channel join বাটন + verification বাটন।"""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📢 Channel এ Join করুন",
                    url=CHANNEL_LINK,
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ Join করেছি — Continue",
                    callback_data=_CHECK_CB,
                )
            ],
        ]
    )


_NOT_SUBSCRIBED_TEXT = (
    "🔒 **Access Restricted**\n\n"
    "এই Bot ব্যবহার করতে আমাদের\n"
    "Official Channel এ Join করতে হবে।\n\n"
    "👇 নিচের বাটনে ক্লিক করে Join করুন,\n"
    "তারপর **✅ Join করেছি — Continue** চাপুন।\n\n"
    f"📞 সাহায্য: {SUPPORT_USERNAME}"
)


# ═════════════════════════════════════════════════════════════
#  SETUP FUNCTION
# ═════════════════════════════════════════════════════════════

def setup_force_sub_handler(app: Client) -> None:
    """
    main.py থেকে একবার call করো।
    Force Sub handlers register করে।

    Handler groups:
      group=-1 → সব handler এর আগে চলে (interceptor)
      group=0  → normal priority ("I Joined" button)
    """
    if not API_CHANNEL:
        LOGGER.info(
            "[ForceSub] Disabled — "
            "FORCE_SUB_CHANNEL not set in .env"
        )
        return

    # ══════════════════════════════════════════════════════════
    #  Message Interceptor
    #  Private message আসলে আগে subscription check করো
    # ══════════════════════════════════════════════════════════

    @app.on_message(
        filters.private & ~filters.service,
        group=-1,
    )
    async def _msg_interceptor(
        client: Client, message: Message
    ):
        """
        প্রতিটা private message এর আগে চলে।
        Cache hit হলে <1ms লাগে।
        Cache miss হলে ~200-500ms (network call)।
        """
        if not message.from_user:
            return

        user_id = message.from_user.id

        # Admin bypass
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
            message.stop_propagation()

    # ══════════════════════════════════════════════════════════
    #  Callback Interceptor
    #  Inline button click এর আগে check করো
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(
        ~filters.regex(f"^{_CHECK_CB}$"),
        group=-1,
    )
    async def _cb_interceptor(
        client: Client, callback: CallbackQuery
    ):
        """
        "Join করেছি" বাটন ছাড়া বাকি সব callback এর আগে চলে।
        """
        if not callback.from_user:
            return

        user_id = callback.from_user.id

        # Admin bypass
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
            callback.stop_propagation()

    # ══════════════════════════════════════════════════════════
    #  "Join করেছি" Button Handler
    # ══════════════════════════════════════════════════════════

    @app.on_callback_query(
        filters.regex(f"^{_CHECK_CB}$"),
        group=0,
    )
    async def _check_joined(
        client: Client, callback: CallbackQuery
    ):
        """
        User "Join করেছি" বাটনে click করলে
        cache clear করে fresh API check করে।
        """
        user_id = callback.from_user.id

        # Cache clear করো — fresh check এর জন্য
        _cache_clear(user_id)
        is_sub = await check_subscription(
            client, user_id, refresh=True
        )

        if is_sub:
            # ✅ Verified — restriction message delete করো
            try:
                await callback.message.delete()
            except Exception:
                pass

            await callback.answer(
                "✅ Verified! এখন Bot ব্যবহার করতে পারবেন।",
                show_alert=True,
            )

            LOGGER.info(
                f"[ForceSub] ✅ Verified | user={user_id}"
            )

            # User কে welcome করো
            try:
                await client.send_message(
                    user_id,
                    "✅ **Channel Verification সফল!**\n\n"
                    "এখন Bot এর সব Feature ব্যবহার করতে পারবেন।\n\n"
                    "📚 Course দেখতে নিচের বাটনে ক্লিক করুন 👇",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "📚 Courses দেখুন",
                                    callback_data="browse_courses",
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
            except Exception as e:
                LOGGER.warning(
                    f"[ForceSub] Welcome msg failed "
                    f"user={user_id}: {e}"
                )

        else:
            # ❌ এখনো join করেননি
            await callback.answer(
                "❌ আপনি এখনো Channel এ Join করেননি!\n"
                "Join করুন তারপর আবার try করুন।",
                show_alert=True,
            )

            LOGGER.info(
                f"[ForceSub] ❌ Not joined | user={user_id}"
            )

    LOGGER.info(
        f"[ForceSub] ✅ Enabled | "
        f"Channel: {API_CHANNEL} | "
        f"Link: {CHANNEL_LINK}"
    )
