# misc/messages.py
# Copyright @YourChannel
# ─────────────────────────────────────────────────────────────
# সব User-facing Message Template এক জায়গায়।
#
# কীভাবে edit করবে:
#   • শুধু এই ফাইল খুলো
#   • যে message টা পরিবর্তন করতে চাও সেটা খোঁজো
#   • Text পরিবর্তন করো
#   • {variable} গুলো একই রাখো — ওগুলো runtime এ fill হয়
#
# কীভাবে অন্য ফাইলে use করবে:
#   from misc.messages import MSG
#   text = MSG.WELCOME.format(name="Rahim")
# ─────────────────────────────────────────────────────────────

from config import ADMIN_USERNAME, BOT_NAME, SUPPORT_USERNAME


class MSG:
    """
    সব message template এখানে।
    Class variable হিসেবে define করা —
    import করে সরাসরি use করো।

    ── Sections ──────────────────────────────────────────────
    1.  START & WELCOME
    2.  MAIN MENU & NAVIGATION
    3.  HELP & SUPPORT
    4.  COURSE BROWSING
    5.  COURSE DETAIL
    6.  PAYMENT — METHOD SELECTION
    7.  PAYMENT — BKASH
    8.  PAYMENT — NAGAD
    9.  PAYMENT — BINANCE/USDT
    10. PAYMENT — ADMIN CONTACT
    11. PAYMENT — SUBMITTED (Manual)
    12. PAYMENT — SUCCESS (Stars Auto)
    13. PAYMENT — APPROVED (Admin approves)
    14. PAYMENT — REJECTED (Admin rejects)
    15. ONE-TIME INVITE LINK
    16. MY ORDERS
    17. PROFILE
    18. ERROR MESSAGES
    19. ADMIN NOTIFICATIONS
    20. GENERAL
    """

    # ══════════════════════════════════════════════════════════
    #  1. START & WELCOME
    # ══════════════════════════════════════════════════════════

    WELCOME = (
        "👋 **{bot_name} তে স্বাগতম, {name}!**\n\n"
        "🎓 আমাদের Premium Course গুলো Browse করুন\n"
        "এবং সহজেই কিনুন।\n\n"
        "নিচের বাটনে ক্লিক করে শুরু করুন 👇"
    )

    WELCOME_ADMIN = (
        "👋 **{bot_name} তে স্বাগতম, {name}!**\n\n"
        "🎓 আমাদের Premium Course গুলো Browse করুন\n"
        "এবং সহজেই কিনুন।\n\n"
        "🔑 *আপনি একজন Admin।*\n"
        "**🛠 Admin Panel** বাটনে ক্লিক করুন।\n\n"
        "নিচের বাটনে ক্লিক করে শুরু করুন 👇"
    )

    KEYBOARD_LOADED = (
        "_Keyboard লোড হয়েছে।_"
    )

    # ══════════════════════════════════════════════════════════
    #  2. MAIN MENU & NAVIGATION
    # ══════════════════════════════════════════════════════════

    MAIN_MENU = (
        "🏠 **Main Menu**\n\n"
        "কী করতে চান বেছে নিন 👇"
    )

    MAIN_MENU_WITH_NAME = (
        "🏠 **Main Menu** — হ্যালো {name}!\n\n"
        "কী করতে চান বেছে নিন 👇"
    )

    CANCELLED = (
        "✅ **বাতিল করা হয়েছে।**\n\n"
        "Main Menu তে ফিরে এসেছেন।"
    )

    NOTHING_TO_CANCEL = (
        "ℹ️ কোনো চলমান কাজ নেই।"
    )

    # ══════════════════════════════════════════════════════════
    #  3. HELP & SUPPORT
    # ══════════════════════════════════════════════════════════

    HELP = (
        "❓ **Help & Support**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📚 **Course কিনতে:**\n"
        "• 📚 Courses বাটনে ক্লিক করুন\n"
        "• পছন্দের Course বেছে নিন\n"
        "• **🛒 Buy Now** তে ক্লিক করুন\n"
        "• Payment করুন\n"
        "• Admin verify করে Access দেবেন\n\n"
        "━━━━━━━���━━━━━━━━━━━━━\n"
        "💬 **সাহায্যের জন্য:**\n"
        "{support}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "**Commands:**\n"
        "`/start` — Main menu\n"
        "`/cancel` — চলমান কাজ বাতিল করুন"
    )

    # ══════════════════════════════════════════════════════════
    #  4. COURSE BROWSING
    # ══════════════════════════════════════════════════════════

    NO_COURSES_AVAILABLE = (
        "😔 **এখন কোনো Course পাওয়া যাচ্ছে না।**\n\n"
        "শীঘ্রই নতুন Course আসছে!\n"
        "আপডেটের জন্য অপেক্ষা করুন।\n\n"
        "📞 যোগাযোগ: {support}"
    )

    SELECT_BRAND = (
        "🏷 **Brand বেছে নিন**\n\n"
        "কোন Institute এর Course দেখতে চান?"
    )

    SELECT_BATCH = (
        "📦 **Batch বেছে নিন**\n\n"
        "🏷 *Brand:* `{brand}`\n\n"
        "কোন Batch এর Course দেখতে চান?"
    )

    SELECT_CATEGORY = (
        "📂 **Category বেছে নিন**\n\n"
        "🏷 *Brand:* `{brand}`\n"
        "📦 *Batch:* `{batch}`\n\n"
        "কোন Category দেখতে চান?"
    )

    SELECT_SUBJECT = (
        "📖 **Subject বেছে নিন**\n\n"
        "🏷 *Brand:* `{brand}`\n"
        "📦 *Batch:* `{batch}`\n"
        "📂 *Category:* `{category}`\n\n"
        "কোন Subject এর Course দেখতে চান?"
    )

    SELECT_COURSE = (
        "🎓 **Available Courses**\n\n"
        "*{brand}* › *{batch}* › *{category}* › *{subject}*\n\n"
        "একটা Course বেছে নিন 👇"
    )

    NO_BATCHES = (
        "⚠️ এই Brand এ কোনো Batch পাওয়া যায়নি।"
    )

    NO_CATEGORIES = (
        "⚠️ এই Batch এ কোনো Category পাওয়া যায়নি।"
    )

    NO_SUBJECTS = (
        "⚠️ এই Category তে কোনো Subject পাওয়া যায়নি।"
    )

    NO_COURSES = (
        "⚠️ এই Subject এ কোনো Course পাওয়া যায়নি।"
    )

    # ══════════════════════════════════════════════════════════
    #  5. COURSE DETAIL
    # ══════════════════════════════════════════════════════════

    COURSE_DETAIL = (
        "🎓 **{name}**\n\n"
        "🏷 *Brand:*    `{brand}`\n"
        "📦 *Batch:*    `{batch}`\n"
        "📂 *Category:* `{category}`\n"
        "📖 *Subject:*  `{subject}`\n\n"
        "📝 **বিস্তারিত:**\n"
        "{description}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "💰 **মূল্য:** `{currency} {price}`\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )

    COURSE_NOT_FOUND = (
        "⚠️ **Course টি পাওয়া যায়নি।**\n\n"
        "হয়তো Course টি সরিয়ে নেওয়া হয়েছে।\n"
        "অন্য Course দেখুন।"
    )

    ALREADY_PURCHASED = (
        "✅ **আপনি এই Course টি আগেই কিনেছেন!**\n\n"
        "📦 Course: `{name}`\n\n"
        "আপনার Group access আগেই দেওয়া হয়েছে।\n"
        "সাহায্যের জন্য: {support}"
    )

    # ══════════════════════════════════════════════════════════
    #  6. PAYMENT — METHOD SELECTION
    # ══════════════════════════════════════════════════════════

    PAYMENT_METHOD_SELECT = (
        "💳 **Payment করুন**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 **Course:** `{name}`\n"
        "💰 **মূল্য:** `{currency} {price}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "নিচের যেকোনো পদ্ধতিতে Payment করুন 👇\n\n"
        "⭐ **Telegram Stars**\n"
        "└ পেমেন্টের সাথে সাথেই Access একটিভ!\n\n"
        "📲 **bKash / Nagad**\n"
        "└ বাংলাদেশী Mobile Banking\n\n"
        "🪙 **Binance / USDT (TRC20)**\n"
        "└ Crypto Payment\n\n"
        "💬 **সরাসরি Admin কে Message**\n"
        "└ অন্য যেকোনো ব্যবস্থা\n\n"
        "📞 সাহায্য: {support}"
    )

    # ══════════════════════════════════════════════════════════
    #  7. PAYMENT — BKASH
    # ══════════════════════════════════════════════════════════

    PAYMENT_BKASH = (
        "📲 **bKash Payment**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 **Course:** `{course_name}`\n"
        "💰 **পরিমাণ:** `{price} {currency}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📲 **bKash নম্বর:** `{bkash_number}`\n"
        "📋 **Type:** `Send Money`\n"
        "📝 **Reference/Note:** `{user_id}`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 **ধাপে ধাপে নির্দেশনা:**\n\n"
        "1️⃣ bKash App খুলুন\n"
        "2️⃣ **Send Money** তে tap করুন\n"
        "3️⃣ নম্বর দিন: `{bkash_number}`\n"
        "4️⃣ পরিমাণ দিন: `{price} {currency}`\n"
        "5️⃣ Reference এ দিন: `{user_id}`\n"
        "6️⃣ Payment সম্পন্ন করুন\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ **Payment করার পর** নিচের বাটনে ক্লিক করুন\n\n"
        "📞 সাহায্য: {support}"
    )

    # ══════════════════════════════════════════════════════════
    #  8. PAYMENT — NAGAD
    # ══════════════════════════════════════════════════════════

    PAYMENT_NAGAD = (
        "📲 **Nagad Payment**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 **Course:** `{course_name}`\n"
        "💰 **পরিমাণ:** `{price} {currency}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📲 **Nagad নম্বর:** `{nagad_number}`\n"
        "📋 **Type:** `Send Money`\n"
        "📝 **Reference/Note:** `{user_id}`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 **ধাপে ধাপে নির্দেশনা:**\n\n"
        "1️⃣ Nagad App খুলুন\n"
        "2️⃣ **Send Money** তে tap করুন\n"
        "3️⃣ নম্বর দিন: `{nagad_number}`\n"
        "4️⃣ পরিমাণ দিন: `{price} {currency}`\n"
        "5️⃣ Reference এ দিন: `{user_id}`\n"
        "6️⃣ Payment সম্পন্ন করুন\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ **Payment করার পর** নিচের বাটনে ক্লিক করুন\n\n"
        "📞 সাহায্য: {support}"
    )

    # ══════════════════════════════════════════════════════════
    #  9. PAYMENT — BINANCE / USDT
    # ══════════════════════════════════════════════════════════

    PAYMENT_CRYPTO = (
        "🪙 **Binance / USDT (TRC20) Payment**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 **Course:** `{course_name}`\n"
        "💰 **পরিমাণ:** `{price} {currency}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🆔 **Binance UID:** `{binance_uid}`\n"
        "📬 **TRC20 Address:**\n"
        "`{binance_address}`\n"
        "🔗 **Network:** `USDT (TRC20)`\n"
        "📝 **Memo/Note:** `{user_id}`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 **ধাপে ধাপে নির্দেশনা:**\n\n"
        "1️⃣ Binance বা যেকোনো USDT Wallet খুলুন\n"
        "2️⃣ **Send/Transfer** এ যান\n"
        "3️⃣ **USDT** → **TRC20** Network বেছে নিন\n"
        "4️⃣ Address: `{binance_address}`\n"
        "5️⃣ Amount: `{price} {currency}`\n"
        "6️⃣ Memo তে দিন: `{user_id}`\n"
        "7️⃣ Transaction সম্পন্ন করুন\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ **Payment করার পর** নিচের বাটনে ক্লিক করুন\n\n"
        "📞 সাহায্য: {support}"
    )

    # ══════════════════════════════════════════════════════════
    #  10. PAYMENT — ADMIN CONTACT
    # ══════════════════════════════════════════════════════════

    PAYMENT_ADMIN_CONTACT = (
        "💬 **Admin কে সরাসরি Message করুন**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 **Course:** `{course_name}`\n"
        "💰 **মূল্য:** `{currency} {price}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "উপরের কোনো পদ্ধতি Suitable না?\n"
        "Admin কে সরাসরি Message করুন।\n\n"
        "👤 **Admin:** {support}\n\n"
        "💡 **অন্যান্য গ্রহণযোগ্য পদ্ধতি:**\n"
        "• 🏦 Bank Transfer\n"
        "• 💵 অন্যান্য Mobile Banking\n"
        "• 🤝 পারস্পরিক সমঝোতায় যেকোনো ব্যবস্থা\n\n"
        "🇧🇩 আমরা বাংলাদেশি — সাহায্য করতে সদা প্রস্তুত!"
    )

    # ══════════════════════════════════════════════════════════
    #  11. PAYMENT — SUBMITTED (Manual payment এর পর)
    # ══════════════════════════════════════════════════════════

    PAYMENT_SUBMITTED = (
        "✅ **Payment Submit হয়েছে!**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 **Course:** `{course_name}`\n"
        "💳 **Method:** `{method}`\n"
        "👤 **আপনার ID:** `{user_id}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⏳ **Admin আপনার Payment verify করছেন।**\n"
        "সাধারণত কয়েক মিনিটের মধ্যে Confirm হবে।\n\n"
        "Confirm হলে আপনি এখানে notification পাবেন।\n\n"
        "📞 সাহায্য: {support}"
    )

    PAYMENT_ALREADY_PENDING = (
        "⚠️ **আপনার আগের Payment এখনো Pending আছে!**\n\n"
        "📦 Course: `{course_name}`\n\n"
        "Admin verify করা পর্যন্ত অপেক্ষা করুন।\n"
        "📞 সাহায্য: {support}"
    )

    # ══════════════════════════════════════════════════════════
    #  12. PAYMENT — SUCCESS (Telegram Stars auto payment)
    # ══════════════════════════════════════════════════════════

    PAYMENT_STARS_SUCCESS = (
        "🎉 **Payment সফল! Stars দিয়ে কেনা হয়েছে!**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "👤 **নাম:** {user_name}\n"
        "📦 **Course:** `{course_name}`\n"
        "⭐ **Stars:** `{stars_amount}`\n"
        "🧾 **Transaction ID:** `{tx_id}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🚀 আপনার Course Access এখনই দেওয়া হচ্ছে!\n"
        "একটু অপেক্ষা করুন...\n\n"
        "📞 সাহায্য: {support}"
    )

    STARS_INVOICE_GENERATING = (
        "⏳ **{course_name} এর Stars Invoice তৈরি হচ্ছে...**\n\n"
        "একটু অপেক্ষা করুন।"
    )

    STARS_INVOICE_READY = (
        "✅ **Invoice Ready!**\n\n"
        "📦 Course: `{course_name}`\n"
        "⭐ Amount: `{stars_amount} Stars`\n\n"
        "উপরের **Pay** বাটনে tap করুন।\n"
        "পেমেন্টের সাথে সাথেই Access একটিভ হবে! 🚀"
    )

    STARS_INVOICE_FAILED = (
        "❌ **Stars Invoice তৈরি করা যায়নি।**\n\n"
        "অন্য Payment পদ্ধতি ব্যবহার করুন।\n"
        "📞 সাহায্য: {support}"
    )

    STARS_DUPLICATE_INVOICE = (
        "⚠️ **আরেকটি Invoice ইতিমধ্যে Active আছে!**\n\n"
        "আগের Invoice complete বা cancel করুন।"
    )

    # ══════════════════════════════════════════════════════════
    #  13. PAYMENT — APPROVED (Admin approve করলে user পাবে)
    # ══════════════════════════════════════════════════════════

    PAYMENT_APPROVED = (
        "✅ **Payment Approved! আপনার Course Access Ready!**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 **Course:** `{course_name}`\n"
        "🏷 **Brand:** `{brand}`\n"
        "📖 **Subject:** `{subject}`\n"
        "🆔 **Order ID:** `{order_id}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎉 **অভিনন্দন!** আপনার Payment Verify হয়েছে!\n\n"
        "নিচের বাটনে ক্লিক করে Private Group এ Join করুন 👇\n\n"
        "📞 সাহায্য: {support}"
    )

    PAYMENT_APPROVED_NO_GROUP = (
        "✅ **Payment Approved!**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 **Course:** `{course_name}`\n"
        "🆔 **Order ID:** `{order_id}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎉 আপনার Payment Verify হয়েছে!\n\n"
        "Admin শীঘ্রই আপনাকে Group এ যোগ করবেন।\n\n"
        "📞 সাহায্য: {support}"
    )

    # ══════════════════════════════════════════════════════════
    #  14. PAYMENT — REJECTED (Admin reject করলে user পাবে)
    # ══════════════════════════════════════════════════════════

    PAYMENT_REJECTED = (
        "❌ **Payment Rejected!**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 **Course:** `{course_name}`\n"
        "🆔 **Order ID:** `{order_id}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "দুঃখিত! আপনার Payment Verify করা সম্ভব হয়নি।\n\n"
        "কারণ হতে পারে:\n"
        "• Payment Amount ঠিক ছিল না\n"
        "• Transaction Verify করা যায়নি\n"
        "• Reference Number দেননি\n\n"
        "সাহায্যের জন্য যোগাযোগ করুন:\n"
        "📞 {support}"
    )

    # ══════════════════════════════════════════════════════════
    #  15. ONE-TIME INVITE LINK
    # ══════════════════════════════════════════════════════════

    INVITE_LINK_MESSAGE = (
        "🔗 **আপনার Private Group Invite Link**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 **Course:** `{course_name}`\n"
        "🆔 **Order ID:** `{order_id}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👇 নিচের বাটনে ক্লিক করে Group এ Join করুন\n\n"
        "⚠️ **গুরুত্বপূর্ণ সতর্কতা:**\n"
        "• এই Link শুধু **একবারই** কাজ করবে\n"
        "• **২৪ ঘন্টার** মধ্যে Join করতে হবে\n"
        "• Link কারো সাথে **Share করবেন না**\n"
        "• Link Share করলে আপনি Join করতে পারবেন না\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📞 সমস্যা হলে: {support}"
    )

    INVITE_LINK_EXPIRED = (
        "⚠️ **Link Expired বা Already Used!**\n\n"
        "আপনার Invite Link আর কাজ করছে না।\n\n"
        "নতুন Link এর জন্য যোগাযোগ করুন:\n"
        "📞 {support}\n\n"
        "Order ID: `{order_id}`"
    )

    # ══════════════════════════════════════════════════════════
    #  16. MY ORDERS
    # ══════════════════════════════════════════════════════════

    MY_ORDERS_EMPTY = (
        "🛒 **আমার Orders**\n\n"
        "আপনি এখনো কোনো Course কেনেননি।\n\n"
        "📚 Course দেখতে **Browse Courses** বাটনে ক্লিক করুন।"
    )

    MY_ORDERS_HEADER = (
        "🛒 **আমার Orders**\n\n"
        "আপনার সব Order নিচে দেখানো হচ্ছে:\n"
    )

    MY_ORDERS_ITEM = (
        "{index}. **{course_name}**\n"
        "   {status_emoji} {status}\n"
        "   📅 {date}\n"
    )

    ORDER_STATUS = {
        "pending":  "⏳ Pending — Admin verify করছেন",
        "approved": "✅ Approved — Access দেওয়া হয়েছে",
        "rejected": "❌ Rejected — Payment হয়নি",
    }

    # ══════════════════════════════════════════════════════════
    #  17. PROFILE
    # ══════════════════════════════════════════════════════════

    PROFILE = (
        "👤 **আমার Profile**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🆔 **ID:** `{user_id}`\n"
        "📛 **নাম:** {full_name}\n"
        "🔖 **Username:** {username}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🎓 **কেনা Courses:** {purchased}\n"
        "🧾 **মোট Orders:** {total_orders}\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )

    # ══════════════════════════════════════════════════════════
    #  18. ERROR MESSAGES
    # ══════════════════════════════════════════════════════════

    ERROR_GENERIC = (
        "❌ **কিছু একটা সমস্যা হয়েছে।**\n\n"
        "আবার চেষ্টা করুন অথবা যোগাযোগ করুন:\n"
        "📞 {support}"
    )

    ERROR_COURSE_NOT_FOUND = (
        "❌ **Course টি পাওয়া যায়নি।**\n\n"
        "Course টি হয়তো সরিয়ে নেওয়া হয়েছে।"
    )

    ERROR_ORDER_NOT_FOUND = (
        "❌ **Order টি পাওয়া যায়নি।**\n\n"
        "Order ID: `{order_id}`"
    )

    ERROR_PAYMENT_PROCESSING = (
        "⚠️ **Payment Received কিন্তু Processing এ সমস্যা!**\n\n"
        "Transaction ID সহ Admin কে জানান:\n"
        "📞 {support}"
    )

    ERROR_ACCESS_DENIED = (
        "⛔ **Access Denied**\n\n"
        "এই কাজটি করার Permission আপনার নেই।"
    )

    ERROR_GROUP_NO_ACCESS = (
        "❌ **Group Access দেওয়া সম্ভব হয়নি!**\n\n"
        "Admin কে জানান:\n"
        "📞 {support}\n\n"
        "Order ID: `{order_id}`"
    )

    # ══════════════════════════════════════════════════════════
    #  19. ADMIN NOTIFICATIONS
    #  (Admin রা যা পাবেন — এগুলো admin দের message)
    # ══════════════════════════════════════════════════════════

    ADMIN_NEW_MANUAL_PAYMENT = (
        "🔔 **নতুন Manual Payment!**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "👤 **User:** [{user_name}](tg://user?id={user_id})"
        " (`{user_id}`)\n"
        "📛 **Username:** {username}\n"
        "📦 **Course:** {course_name}\n"
        "💰 **Amount:** {currency} {price}\n"
        "💳 **Method:** {method}\n"
        "🆔 **Order ID:** `{order_id}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⬇️ Verify করে Approve বা Reject করুন:"
    )

    ADMIN_NEW_STARS_PAYMENT = (
        "⭐ **Stars Payment Received! (Auto Approved)**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "👤 **User:** [{user_name}](tg://user?id={user_id})"
        " (`{user_id}`)\n"
        "📛 **Username:** {username}\n"
        "📦 **Course:** {course_name}\n"
        "⭐ **Stars:** {stars_amount}\n"
        "🧾 **TX ID:** `{tx_id}`\n"
        "🆔 **Order ID:** `{order_id}`\n"
        "✅ **Status:** Auto Approved\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )

    ADMIN_OTL_SUCCESS = (
        "✅ **Approved & One-Time Link Sent!**\n\n"
        "👤 **User:** [{user_name}](tg://user?id={user_id})"
        " (`{user_id}`)\n"
        "📦 **Course:** `{course_name}`\n"
        "🔗 **Link:** `{invite_link}`\n\n"
        "⚠️ Link একবারই কাজ করবে।\n"
        "24 ঘন্টায় Expire হবে।"
    )

    ADMIN_OTL_FAILED = (
        "❌ **One-Time Link তৈরি করা যায়নি!**\n\n"
        "👤 **User ID:** `{user_id}`\n"
        "📦 **Course:** `{course_name}`\n\n"
        "কারণ:\n"
        "• Bot Group এ Admin নয়\n"
        "• Invite Permission নেই\n\n"
        "Group ID: `{group_id}`\n\n"
        "Bot কে Admin করে আবার try করুন।"
    )

    ADMIN_OTL_SENT_FAILED = (
        "⚠️ **Link তৈরি হয়েছে কিন্তু User কে পাঠানো যায়নি!**\n\n"
        "👤 **User ID:** `{user_id}`\n"
        "🔗 **Link:** `{invite_link}`\n\n"
        "User কে manually এই link পাঠান।"
    )

    ADMIN_NO_GROUP_SET = (
        "⚠️ **Course এ Group Set করা নেই!**\n\n"
        "📦 **Course:** `{course_name}`\n"
        "👤 **User:** [{user_name}](tg://user?id={user_id})"
        " (`{user_id}`)\n\n"
        "Admin Panel → List Courses → এই Course এ\n"
        "Group যোগ করুন।\n\n"
        "অথবা manually User কে Link পাঠান।"
    )

    ADMIN_ORDER_APPROVED_CONFIRM = (
        "✅ Order `{order_id_short}` **Approved!**"
    )

    ADMIN_ORDER_REJECTED_CONFIRM = (
        "❌ Order `{order_id_short}` **Rejected.**"
    )

    # ══════════════════════════════════════════════════════════
    #  20. GENERAL / MISC
    # ══════════════════════════════════════════════════════════

    BROADCAST_SENDING = (
        "📢 **{total_users}** জন User কে Broadcast হচ্ছে...\n"
        "অপেক্ষা করুন।"
    )

    BROADCAST_DONE = (
        "✅ **Broadcast সম্পন্ন!**\n\n"
        "✅ Sent:   {sent}\n"
        "❌ Failed: {failed}"
    )

    GROUP_CHECK_SUCCESS = (
        "✅ **সব ঠিক আছে!**\n\n"
        "🆔 Group ID: `{group_id}`\n"
        "👑 Bot Status: Admin ✅\n"
        "🔗 Invite Permission: ✅\n\n"
        "এই Group ID টা Course এ Add করতে পারবেন।"
    )

    GROUP_CHECK_NO_INVITE = (
        "⚠️ **Bot Admin কিন্তু Invite Permission নেই!**\n\n"
        "🆔 Group ID: `{group_id}`\n"
        "👑 Bot Status: Admin ✅\n"
        "🔗 Invite Permission: ❌\n\n"
        "**সমাধান:**\n"
        "Group → Admin Settings → Bot →\n"
        "'Invite Users via Link' চালু করুন।"
    )

    GROUP_CHECK_NOT_ADMIN = (
        "❌ **Bot Admin না!**\n\n"
        "🆔 Group ID: `{group_id}`\n"
        "👑 Bot Status: Not Admin ❌\n\n"
        "**সমাধান:**\n"
        "1. Group এ যান\n"
        "2. Members → Bot → Promote to Admin\n"
        "3. 'Invite Users via Link' Permission দিন\n"
        "4. আবার `/checkgroup {group_id}` দিন"
    )

    GROUP_CHECK_ERROR = (
        "❌ **Error:**\n`{error}`\n\n"
        "**সমাধান:**\n"
        "1. Bot কে Group এ Add করুন\n"
        "2. Bot কে Admin বানান\n"
        "3. 'Invite Users via Link' Permission দিন"
    )

    GROUP_CHECKING = (
        "⏳ Group `{group_id}` check হচ্ছে..."
    )

    SUPPORT_BUTTON_LABEL = "💬 Support: {support}"

    JOIN_GROUP_BUTTON_LABEL = "🚀 Group এ Join করুন"
