# plugins/dynamic_buttons.py
# Copyright @YourChannel
# ─────────────────────────────────────────────────────────────
# Dynamic Button System
#
# Admin থেকে:
#   - নতুন বাটন তৈরি করা যাবে (নাম + content)
#   - বাটনের নাম পরিবর্তন করা যাবে
#   - বাটন মুছে ফেলা যাবে
#
# User এর কাছে:
#   - Reply Keyboard এ dynamic বাটনগুলো দেখাবে
#   - ক্লিক করলে সেই বাটনের content দেখাবে
# ─────────────────────────────────────────────────────────────

import uuid

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

import db
from auth import is_admin
from misc.keyboards import main_menu_inline
from utils import LOGGER

# ── State store for button editor FSM ─────────────────────────
_btn_edit_state: dict = {}


# ════════════════════════════════════════════════════════════
#  HELPER — Dynamic Reply Keyboard তৈরি করো
# ════════════════════════════════════════════════════════════

async def build_dynamic_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    DB থেকে dynamic buttons এনে Reply Keyboard তৈরি করো।
    Static বাটনগুলোর পর dynamic বাটন যোগ হবে।
    """
    buttons = await db.get_dynamic_buttons()

    rows = [
        [KeyboardButton("💸 PAYMENT REQUEST"), KeyboardButton("🛒 MY ORDERS")],
        [KeyboardButton("👤 MY PROFILE"),       KeyboardButton("☎️ HELPLINE")],
    ]

    # Dynamic বাটনগুলো ২ করে row এ রাখো
    dyn_labels = [b["label"] for b in buttons]
    for i in range(0, len(dyn_labels), 2):
        row = [KeyboardButton(dyn_labels[i])]
        if i + 1 < len(dyn_labels):
            row.append(KeyboardButton(dyn_labels[i + 1]))
        rows.append(row)

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


# ════════════════════════════════════════════════════════════
#  ADMIN PANEL — Button Editor Keyboards
# ════════════════════════════════════════════════════════════

def _btn_editor_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➕ নতুন বাটন তৈরি করুন", callback_data="btnedit:new")],
            [InlineKeyboardButton("📋 বাটনের তালিকা",       callback_data="btnedit:list")],
            [InlineKeyboardButton("🔙 Admin Panel এ ফিরুন", callback_data="admin:panel")],
        ]
    )


def _btn_list_kb(buttons: list) -> InlineKeyboardMarkup:
    rows = []
    for b in buttons:
        rows.append(
            [
                InlineKeyboardButton(
                    f"✏️ {b['label']}", callback_data=f"btnedit:view:{b['button_id']}"
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton("🔙 ফিরুন", callback_data="btnedit:main")]
    )
    return InlineKeyboardMarkup(rows)


def _btn_single_kb(button_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✏️ নাম পরিবর্তন করুন",
                    callback_data=f"btnedit:rename:{button_id}",
                ),
                InlineKeyboardButton(
                    "📝 Content পরিবর্তন করুন",
                    callback_data=f"btnedit:editcontent:{button_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🗑 Delete করুন",
                    callback_data=f"btnedit:delete:{button_id}",
                )
            ],
            [InlineKeyboardButton("🔙 তালিকায় ফিরুন", callback_data="btnedit:list")],
        ]
    )


def _btn_confirm_delete_kb(button_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ হ্যাঁ, Delete করুন",
                    callback_data=f"btnedit:confirmdelete:{button_id}",
                ),
                InlineKeyboardButton(
                    "❌ না, রাখুন",
                    callback_data=f"btnedit:view:{button_id}",
                ),
            ]
        ]
    )


# ════════════════════════════════════════════════════════════
#  setup(app)
# ════════════════════════════════════════════════════════════

def setup(app: Client) -> None:

    # ── Admin: Button Editor Entry ─────────────────────────────
    @app.on_callback_query(filters.regex(r"^admin:button_editor$"))
    async def cb_btn_editor(client: Client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        await callback.message.edit_text(
            "🎛 **Button Editor**\n\n"
            "এখান থেকে User এর Reply Keyboard এ নতুন বাটন যোগ করুন,\n"
            "নাম পরিবর্তন করুন বা মুছে ফেলুন।",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_btn_editor_main_kb(),
        )
        await callback.answer()

    # ── Main button editor menu ────────────────────────────────
    @app.on_callback_query(filters.regex(r"^btnedit:main$"))
    async def cb_btnedit_main(client: Client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        await callback.message.edit_text(
            "🎛 **Button Editor**\n\n"
            "এখান থেকে User এর Reply Keyboard এ নতুন বাটন যোগ করুন,\n"
            "নাম পরিবর্তন করুন বা মুছে ফেলুন।",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_btn_editor_main_kb(),
        )
        await callback.answer()

    # ── List buttons ───────────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^btnedit:list$"))
    async def cb_btnedit_list(client: Client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        buttons = await db.get_dynamic_buttons()
        if not buttons:
            await callback.message.edit_text(
                "📋 **বাটনের তালিকা**\n\nএখনো কোনো dynamic বাটন নেই।",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("➕ নতুন বাটন", callback_data="btnedit:new")],
                        [InlineKeyboardButton("🔙 ফিরুন",     callback_data="btnedit:main")],
                    ]
                ),
            )
        else:
            await callback.message.edit_text(
                f"📋 **বাটনের তালিকা** ({len(buttons)} টি)\n\nএকটি বাটন বেছে নিন:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=_btn_list_kb(buttons),
            )
        await callback.answer()

    # ── View single button ─────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^btnedit:view:(.+)$"))
    async def cb_btnedit_view(client: Client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        button_id = callback.matches[0].group(1)
        btn       = await db.get_dynamic_button(button_id)
        if not btn:
            return await callback.answer("বাটন পাওয়া যায়নি!", show_alert=True)

        await callback.message.edit_text(
            f"🔘 **বাটনের বিবরণ**\n\n"
            f"🏷 **নাম:** `{btn['label']}`\n"
            f"📝 **Content:**\n{btn['content']}\n\n"
            f"🆔 **ID:** `{button_id}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_btn_single_kb(button_id),
        )
        await callback.answer()

    # ── New button — start ─────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^btnedit:new$"))
    async def cb_btnedit_new(client: Client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        uid = callback.from_user.id
        _btn_edit_state[uid] = {"step": "new_label"}

        await callback.message.edit_text(
            "➕ **নতুন বাটন তৈরি করুন**\n\n"
            "**ধাপ ১/২ — বাটনের নাম দিন:**\n\n"
            "_e.g. 📘 Study Tips, 🎯 Free Resources_\n\n"
            "❌ বাতিল করতে /cancel দিন।",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ বাতিল", callback_data="btnedit:main")]]
            ),
        )
        await callback.answer()

    # ── Rename button ──────────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^btnedit:rename:(.+)$"))
    async def cb_btnedit_rename(client: Client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        button_id = callback.matches[0].group(1)
        uid       = callback.from_user.id
        _btn_edit_state[uid] = {"step": "rename", "button_id": button_id}

        await callback.message.edit_text(
            "✏️ **বাটনের নাম পরিবর্তন করুন**\n\n"
            "নতুন নামটি টাইপ করুন:\n\n"
            "❌ বাতিল করতে /cancel দিন।",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ বাতিল", callback_data=f"btnedit:view:{button_id}")]]
            ),
        )
        await callback.answer()

    # ── Edit content ───────────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^btnedit:editcontent:(.+)$"))
    async def cb_btnedit_editcontent(client: Client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        button_id = callback.matches[0].group(1)
        uid       = callback.from_user.id
        _btn_edit_state[uid] = {"step": "edit_content", "button_id": button_id}

        await callback.message.edit_text(
            "📝 **বাটনের Content পরিবর্তন করুন**\n\n"
            "নতুন content টাইপ করুন:\n"
            "_(Markdown supported)_\n\n"
            "❌ বাতিল করতে /cancel দিন।",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ বাতিল", callback_data=f"btnedit:view:{button_id}")]]
            ),
        )
        await callback.answer()

    # ── Delete button ──────────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^btnedit:delete:(.+)$"))
    async def cb_btnedit_delete(client: Client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        button_id = callback.matches[0].group(1)
        btn       = await db.get_dynamic_button(button_id)
        if not btn:
            return await callback.answer("বাটন পাওয়া যায়নি!", show_alert=True)

        await callback.message.edit_text(
            f"⚠️ **নিশ্চিত করুন**\n\n"
            f"**`{btn['label']}`** বাটনটি delete করবেন?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_btn_confirm_delete_kb(button_id),
        )
        await callback.answer()

    # ── Confirm delete ─────────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^btnedit:confirmdelete:(.+)$"))
    async def cb_btnedit_confirmdelete(client: Client, callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return await callback.answer("⛔ Admins only!", show_alert=True)

        button_id = callback.matches[0].group(1)
        ok        = await db.delete_dynamic_button(button_id)

        if ok:
            await callback.message.edit_text(
                "✅ **বাটন Delete হয়েছে!**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 তালিকায় ফিরুন", callback_data="btnedit:list")]]
                ),
            )
            await callback.answer("Deleted!")
        else:
            await callback.answer("Delete ব্যর্থ হয়েছে!", show_alert=True)

    # ── FSM Message Handler (Admin) ────────────────────────────
    @app.on_message(
        filters.private & filters.text,
        group=12,
    )
    async def btnedit_fsm_handler(client: Client, message: Message):
        uid   = message.from_user.id
        state = _btn_edit_state.get(uid)
        if not state:
            return
        if not is_admin(uid):
            _btn_edit_state.pop(uid, None)
            return

        step = state.get("step")
        text = message.text.strip()

        if step == "new_label":
            state["label"] = text
            state["step"]  = "new_content"
            await message.reply_text(
                f"✅ **নাম:** `{text}`\n\n"
                f"**ধাপ ২/২ — এই বাটন ক্লিক করলে কী দেখাবে?**\n\n"
                f"Content লিখুন:\n_(Markdown supported)_",
                parse_mode=ParseMode.MARKDOWN,
            )

        elif step == "new_content":
            label   = state.get("label", "Button")
            buttons = await db.get_dynamic_buttons()
            pos     = len(buttons) + 1
            bid     = uuid.uuid4().hex[:12]

            ok = await db.add_dynamic_button(bid, label, text, pos)
            _btn_edit_state.pop(uid, None)

            if ok:
                await message.reply_text(
                    f"✅ **নতুন বাটন তৈরি হয়েছে!**\n\n"
                    f"🏷 **নাম:** `{label}`\n"
                    f"📝 **Content:** সংরক্ষিত হয়েছে।\n\n"
                    f"User দের কাছে Reply Keyboard এ দেখাবে।",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🎛 Button Editor", callback_data="admin:button_editor")]]
                    ),
                )
            else:
                await message.reply_text("❌ বাটন তৈরি ব্যর্থ হয়েছে।")

        elif step == "rename":
            button_id = state.get("button_id")
            ok        = await db.update_dynamic_button(button_id, label=text)
            _btn_edit_state.pop(uid, None)

            if ok:
                await message.reply_text(
                    f"✅ **বাটনের নাম পরিবর্তন হয়েছে!**\n\n"
                    f"🏷 **নতুন নাম:** `{text}`",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🔙 ফিরুন", callback_data=f"btnedit:view:{button_id}")]]
                    ),
                )
            else:
                await message.reply_text("❌ নাম পরিবর্তন ব্যর্থ হয়েছে।")

        elif step == "edit_content":
            button_id = state.get("button_id")
            ok        = await db.update_dynamic_button(button_id, content=text)
            _btn_edit_state.pop(uid, None)

            if ok:
                await message.reply_text(
                    f"✅ **Content পরিবর্তন হয়েছে!**",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🔙 ফিরুন", callback_data=f"btnedit:view:{button_id}")]]
                    ),
                )
            else:
                await message.reply_text("❌ Content পরিবর্তন ব্যর্থ হয়েছে।")

    # ── User: Dynamic Button Press ─────────────────────────────
    @app.on_message(
        filters.private & filters.text,
        group=25,
    )
    async def user_dynamic_btn_handler(client: Client, message: Message):
        uid   = message.from_user.id
        label = message.text.strip() if message.text else ""

        # Static বাটনগুলো skip করো
        static_labels = {
            "💸 PAYMENT REQUEST", "🛒 MY ORDERS",
            "👤 MY PROFILE",       "☎️ HELPLINE",
        }
        if label in static_labels:
            return

        # Dynamic button এ match করো
        buttons = await db.get_dynamic_buttons()
        for btn in buttons:
            if btn["label"] == label:
                await message.reply_text(
                    btn["content"],
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=main_menu_inline(),
                )
                return

    LOGGER.info("[DynamicButtons] Plugin loaded ✅")
