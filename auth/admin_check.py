# auth/admin_check.py
# Copyright @YourChannel
# ─────────────────────────────────────────────────────────────
# setup(app) → auth/__init__.py call করে
# is_admin, admin_required, admin_callback_required
#   → সরাসরি import করা যায় auth থেকে
# ─────────────────────────────────────────────────────────────

from functools import wraps
from typing import Callable

from pyrogram import Client
from pyrogram.types import CallbackQuery, Message

from config import ADMIN_IDS


def is_admin(user_id: int) -> bool:
    """True যদি user_id admin list এ থাকে।"""
    return user_id in ADMIN_IDS


# ── Message handler decorator ─────────────────────────────────

def admin_required(func: Callable):
    @wraps(func)
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        if not is_admin(message.from_user.id):
            await message.reply_text(
                "⛔ **Access Denied**\n\n"
                "Admins only."
            )
            return
        return await func(client, message, *args, **kwargs)
    return wrapper


# ── Callback handler decorator ────────────────────────────────

def admin_callback_required(func: Callable):
    @wraps(func)
    async def wrapper(client: Client, callback: CallbackQuery, *args, **kwargs):
        if not is_admin(callback.from_user.id):
            await callback.answer("⛔ Admins only!", show_alert=True)
            return
        return await func(client, callback, *args, **kwargs)
    return wrapper


# ── setup() ───────────────────────────────────────────────────

def setup(app: Client) -> None:
    """
    auth/__init__.py এর _AUTH_SETUPS থেকে call হয়।
    এই মুহূর্তে admin_check এ কোনো handler নেই —
    শুধু decorator/utility functions।
    ভবিষ্যতে handler যোগ করলে এখানে লিখো।
    """
    pass  # decorators already available via import
