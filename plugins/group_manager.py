# plugins/group_manager.py
# Copyright @YourChannel
# ─────────────────────────────────────────────────────────────
# One-Time Invite Link System
#
# কাজ:
#   1. Course এ group_id store থাকে
#   2. Admin approve করলে bot ঐ group এ OTL বানায়
#   3. OTL শুধু একজনই use করতে পারবে (member_limit=1)
#   4. Link expire হয় 24 ঘন্টায়
#   5. Bot সেই link user কে পাঠায়
#   6. Bot check করে সে group এ admin কিনা
# ─────────────────────────────────────────────────────────────

from datetime import datetime, timedelta

from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.errors import (
    ChatAdminRequired,
    ChatWriteForbidden,
    PeerIdInvalid,
    UserNotParticipant,
)
from pyrogram.types import CallbackQuery, Message

import db
from auth import is_admin
from config import ADMIN_IDS, ADMIN_USERNAME
from misc import admin_back_panel_inline, admin_panel_inline
from utils import LOGGER


# ═════════════════════════════════════════════════════════════
#  CORE FUNCTION — One-Time Invite Link বানাও
# ═════════════════════════════════════════════════════════════

async def generate_one_time_link(
    client: Client,
    group_id: int,
    user_id: int,
    course_name: str,
) -> str | None:
    """
    group_id তে একটা One-Time Invite Link বানায়।

    Requirements:
      - Bot ঐ group/channel এ admin থাকতে হবে
      - Bot এর "Invite Users via Link" permission থাকতে হবে

    Returns:
      - invite_link (str) যদি সফল হয়
      - None যদি ব্যর্থ হয়
    """
    try:
        # ── Bot admin কিনা check করো ──────────────────────────
        bot_member = await client.get_chat_member(
            group_id,
            (await client.get_me()).id,
        )

        if bot_member.status not in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        ):
            LOGGER.error(
                f"[OTL] Bot is NOT admin in group {group_id}"
            )
            return None

        # ── One-Time Link generate করো ───────────────────────
        # member_limit=1 → শুধু একজনই join করতে পারবে
        # expire_date   → 24 ঘন্টা পর expire
        link = await client.create_chat_invite_link(
            chat_id=group_id,
            name=f"Course: {course_name} | User: {user_id}",
            expire_date=datetime.utcnow() + timedelta(hours=24),
            member_limit=1,
            creates_join_request=False,
        )

        LOGGER.info(
            f"[OTL] Generated | "
            f"group={group_id} user={user_id} "
            f"link={link.invite_link}"
        )
        return link.invite_link

    except ChatAdminRequired:
        LOGGER.error(
            f"[OTL] Bot lacks admin rights in group {group_id}"
        )
        return None
    except Exception as e:
        LOGGER.error(f"[OTL] Failed to generate link: {e}")
        return None


async def check_bot_is_admin(
    client: Client, group_id: int
) -> dict:
    """
    Bot ঐ group এ admin কিনা এবং
    invite link permission আছে কিনা check করে।

    Returns dict:
    {
        "is_admin": bool,
        "can_invite": bool,
        "error": str | None,
    }
    """
    result = {
        "is_admin":  False,
        "can_invite": False,
        "error":     None,
    }
    try:
        me = await client.get_me()
        member = await client.get_chat_member(group_id, me.id)

        if member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        ):
            result["is_admin"] = True
            # Pyrogram privileges object check
            if member.status == ChatMemberStatus.OWNER:
                result["can_invite"] = True
            elif member.privileges:
                result["can_invite"] = (
                    member.privileges.can_invite_users or False
                )
    except PeerIdInvalid:
        result["error"] = (
            "Group/Channel ID ভুল অথবা Bot সেই group এ নেই।"
        )
    except UserNotParticipant:
        result["error"] = (
            "Bot ঐ Group/Channel এ member না।\n"
            "আগে Bot কে group এ add করুন তারপর admin বানান।"
        )
    except Exception as e:
        result["error"] = str(e)

    return result


async def send_invite_to_user(
    client: Client,
    user_id: int,
    course: dict,
    invite_link: str,
    order_id: str,
) -> bool:
    """
    User কে One-Time Invite Link পাঠায়।
    Returns True যদি সফল হয়।
    """
    from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    text = (
        f"🎉 **Payment Approved! আপনার Course Access Ready!**\n\n"
        f"📦 **Course:** `{course['name']}`\n"
        f"🏷 **Brand:** `{course['brand']}`\n"
        f"📖 **Subject:** `{course['subject']}`\n"
        f"🆔 **Order ID:** `{order_id}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 **আপনার One-Time Private Link:**\n\n"
        f"👇 নিচের বাটনে click করে Group এ যোগ দিন\n\n"
        f"⚠️ **সতর্কতা:**\n"
        f"• এই link শুধু **একবারই** কাজ করবে\n"
        f"• **২৪ ঘন্টার** মধ্যে join করতে হবে\n"
        f"• Link কারো সাথে **share করবেন না**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"সাহায্যের জন্য: {ADMIN_USERNAME}"
    )

    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🚀 Group এ Join করুন",
                    url=invite_link,
                )
            ],
            [
                InlineKeyboardButton(
                    f"💬 Support: {ADMIN_USERNAME}",
                    url=f"https://t.me/"
                    f"{ADMIN_USERNAME.lstrip('@')}",
                )
            ],
        ]
    )

    try:
        await client.send_message(
            user_id,
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb,
        )
        LOGGER.info(
            f"[OTL] Invite sent | "
            f"user={user_id} course={course['name']}"
        )
        return True
    except Exception as e:
        LOGGER.error(
            f"[OTL] Could not send invite to {user_id}: {e}"
        )
        return False


# ═════════════════════════════════════════════════════════════
#  MAIN FUNCTION — Approve হলে এটা call হয়
# ═════════════════════════════════════════════════════════════

async def approve_and_send_link(
    client: Client,
    order_id: str,
    admin_chat_id: int,
) -> None:
    """
    Admin approve করলে এই function call হয়।

    1. Order থেকে course_id ও user_id বের করে
    2. Course থেকে group_id বের করে
    3. OTL generate করে
    4. User কে link পাঠায়
    5. Admin কে status জানায়
    """
    from bson import ObjectId
    from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    db_inst = db.get_db()

    # ── Order fetch ───────────────────────────────────────────
    order = await db_inst.orders.find_one(
        {"_id": ObjectId(order_id)}
    )
    if not order:
        await client.send_message(
            admin_chat_id,
            f"❌ Order `{order_id}` পাওয়া যায়নি।",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    user_id   = order["user_id"]
    course_id = order["course_id"]
    user_name = order.get("user_name", "User")

    # ── Course fetch ──────────────────────────────────────────
    course = await db.get_course_by_id(str(course_id))
    if not course:
        await client.send_message(
            admin_chat_id,
            f"❌ Course পাওয়া যায়নি। "
            f"Order ID: `{order_id}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # ── Group ID আছে কিনা check ───────────────────────────────
    group_id = course.get("group_id")
    if not group_id:
        # Group নেই — admin কে জানাও manually দিতে বলো
        await client.send_message(
            admin_chat_id,
            f"⚠️ **Course এ Group set করা নেই!**\n\n"
            f"📦 Course: `{course['name']}`\n"
            f"👤 User: [{user_name}](tg://user?id={user_id})"
            f" (`{user_id}`)\n\n"
            f"Admin Panel → List Courses → এই course এ "
            f"Group যোগ করুন।\n\n"
            f"অথবা manually user কে link পাঠান।",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "📋 Course List",
                            callback_data="admin:list_courses",
                        )
                    ]
                ]
            ),
        )
        return

    # ── OTL Generate ──────────────────────────────────────────
    await client.send_message(
        admin_chat_id,
        f"⏳ `{course['name']}` এর জন্য "
        f"One-Time Link তৈরি হচ্ছে...",
        parse_mode=ParseMode.MARKDOWN,
    )

    invite_link = await generate_one_time_link(
        client, int(group_id), user_id, course["name"]
    )

    if not invite_link:
        await client.send_message(
            admin_chat_id,
            f"❌ **One-Time Link তৈরি করা যায়নি!**\n\n"
            f"কারণ হতে পারে:\n"
            f"• Bot ঐ Group এ admin না\n"
            f"• Bot এর Invite permission নেই\n\n"
            f"Group ID: `{group_id}`\n\n"
            f"Bot কে group এ admin করুন এবং "
            f"আবার try করুন।",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # ── Order এ link save করো ────────────────────────────────
    await db_inst.orders.update_one(
        {"_id": ObjectId(order_id)},
        {
            "$set": {
                "invite_link": invite_link,
                "link_sent_at": datetime.utcnow(),
                "status": "approved",
            }
        },
    )

    # ── User কে link পাঠাও ───────────────────────────────────
    sent = await send_invite_to_user(
        client, user_id, course, invite_link, order_id
    )

    # ── Admin কে status জানাও ────────────────────────────────
    if sent:
        await client.send_message(
            admin_chat_id,
            f"✅ **Approved & Link Sent!**\n\n"
            f"👤 User: [{user_name}](tg://user?id={user_id})"
            f" (`{user_id}`)\n"
            f"📦 Course: `{course['name']}`\n"
            f"🔗 Link: `{invite_link}`\n\n"
            f"⚠️ Link একবারই কাজ করবে।",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_back_panel_inline(),
        )
    else:
        await client.send_message(
            admin_chat_id,
            f"⚠️ **Link তৈরি হয়েছে কিন্তু user কে পাঠানো যায়নি!**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"🔗 Link: `{invite_link}`\n\n"
            f"User কে manually এই link পাঠান।",
            parse_mode=ParseMode.MARKDOWN,
        )


# ═════════════════════════════════════════════════════════════
#  setup(app)
# ═════════════════════════════════════════════════════════════

def setup(app: Client) -> None:
    """
    Admin command: /checkgroup {group_id}
    Bot ঐ group এ admin কিনা check করে।
    """

    @app.on_message(
        filters.command("checkgroup") & filters.private
    )
    async def cmd_check_group(
        client: Client, message: Message
    ):
        if not is_admin(message.from_user.id):
            return

        if len(message.command) < 2:
            await message.reply_text(
                "❌ **Usage:** `/checkgroup {group_id}`\n\n"
                "Group ID জানতে:\n"
                "• Group এ @userinfobot যোগ করুন\n"
                "• বা Group এ /id পাঠান\n"
                "• ID সাধারণত -100 দিয়ে শুরু হয়",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        raw_id = message.command[1].strip()
        try:
            group_id = int(raw_id)
        except ValueError:
            await message.reply_text(
                "❌ Group ID অবশ্যই number হতে হবে।\n"
                "_e.g. `-1001234567890`_",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        checking = await message.reply_text(
            f"⏳ Group `{group_id}` check হচ্ছে...",
            parse_mode=ParseMode.MARKDOWN,
        )

        result = await check_bot_is_admin(client, group_id)

        if result["error"]:
            await checking.edit_text(
                f"❌ **Error:**\n`{result['error']}`\n\n"
                f"**সমাধান:**\n"
                f"1. Bot কে Group এ add করুন\n"
                f"2. Bot কে Admin বানান\n"
                f"3. 'Invite Users via Link' permission দিন",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        if result["is_admin"] and result["can_invite"]:
            await checking.edit_text(
                f"✅ **সব ঠিক আছে!**\n\n"
                f"🆔 Group ID: `{group_id}`\n"
                f"👑 Bot Status: Admin ✅\n"
                f"🔗 Invite Permission: ✅\n\n"
                f"এই Group ID টা Course এ add করতে পারবেন।",
                parse_mode=ParseMode.MARKDOWN,
            )
        elif result["is_admin"] and not result["can_invite"]:
            await checking.edit_text(
                f"⚠️ **Bot Admin কিন্তু Permission নেই!**\n\n"
                f"🆔 Group ID: `{group_id}`\n"
                f"👑 Bot Status: Admin ✅\n"
                f"🔗 Invite Permission: ❌\n\n"
                f"**সমাধান:**\n"
                f"Group → Admin Settings → Bot → "
                f"'Invite Users via Link' চালু করুন।",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await checking.edit_text(
                f"❌ **Bot Admin না!**\n\n"
                f"🆔 Group ID: `{group_id}`\n"
                f"👑 Bot Status: Not Admin ❌\n\n"
                f"**সমাধান:**\n"
                f"1. Group এ যান\n"
                f"2. Members → Bot → Promote to Admin\n"
                f"3. 'Invite Users via Link' permission দিন\n"
                f"4. আবার `/checkgroup {group_id}` দিন",
                parse_mode=ParseMode.MARKDOWN,
            )

    LOGGER.info("[GroupManager] Plugin loaded ✅")
