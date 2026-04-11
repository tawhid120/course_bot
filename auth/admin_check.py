# auth/admin_check.py
# Copyright @YourChannel

from functools import wraps
from typing import Callable

from pyrogram import Client
from pyrogram.types import CallbackQuery, Message

from config import ADMIN_IDS


def is_admin(user_id: int) -> bool:
    """Return True if user_id is a configured admin."""
    return user_id in ADMIN_IDS


# ─── Message Handler Decorator ───────────────────────────────────────────────

def admin_required(func: Callable):
    @wraps(func)
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        if not is_admin(message.from_user.id):
            await message.reply_text(
                "⛔ **Access Denied**\n\n"
                "This command is restricted to administrators only."
            )
            return
        return await func(client, message, *args, **kwargs)
    return wrapper


# ─── Callback Handler Decorator ──────────────────────────────────────────────

def admin_callback_required(func: Callable):
    @wraps(func)
    async def wrapper(client: Client, callback: CallbackQuery, *args, **kwargs):
        if not is_admin(callback.from_user.id):
            await callback.answer(
                "⛔ Admins only!", show_alert=True
            )
            return
        return await func(client, callback, *args, **kwargs)
    return wrapper
