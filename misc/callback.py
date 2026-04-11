# misc/callback.py
# Copyright @YourChannel

"""
Central callback query dispatcher.
All inline button presses flow through here first,
then get routed to the correct plugin handler.
"""

from pyrogram import Client
from pyrogram.types import CallbackQuery

from utils import LOGGER


async def handle_callback_query(client: Client, callback: CallbackQuery) -> None:
    """
    Called by the on_callback_query handler registered in main.py.
    Logs every callback and passes control to the appropriate handler.

    Individual plugin files register their own @Client.on_callback_query
    handlers — this function is the GLOBAL catch-all logger / fallback.
    """
    data    = callback.data or ""
    user_id = callback.from_user.id

    LOGGER.info(
        f"[Callback] user={user_id} data='{data}'"
    )

    # If no plugin claimed this callback, answer silently.
    # (Prevents the Telegram "loading" spinner from hanging.)
    # Individual handlers answer their own callbacks before this runs
    # because Pyrogram dispatches to ALL matching handlers in group order.
    # This function is only used as an explicit fallback in main.py.
    try:
        await callback.answer()
    except Exception:
        pass
