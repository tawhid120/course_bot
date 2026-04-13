# misc/messages.py
# Copyright @YourChannel

from config import ADMIN_USERNAME, BOT_NAME, SUPPORT_USERNAME


class MSG:

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
        "🔑 **আপনি একজন Admin।**\n"
        "**🛠 Admin Panel** বাটনে ক্লিক করুন।\n\n"
        "নিচের বাটনে ক্লিক করে শুরু করুন 👇"
    )

    KEYBOARD_LOADED = "__Keyboard লোড হয়েছে।__"

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

    NOTHING_TO_CANCEL = "ℹ️ কোনো চলমান কাজ নেই।"

    # ══════════════════════════════════════════════════════════
    #  3. HELP & SUPPORT  ← আপনার চাহিদামতো পরিবর্তিত
    # ══════════════════════════════════════════════════════════

    HELP = (
        "❓ **Help & Support**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📚 **Course কিনতে:**\n"
        "• 📚 Courses বাটনে ক্লিক করুন\n"
        "• পছন্দের Course বেছে নিন\n"
        "• **🛒 Buy Now** তে ক্লিক করুন\n"
        "• bKash বা Nagad এ Payment করুন\n"
        "• Screenshot দিন (ঐচ্ছিক)\n"
        "• Admin verify করে Access দেবেন\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "💬 **যেকোনো সাহায্যের জন্য আমাদের হেল্পলাইনে যোগাযোগ করুন:**\n"
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

    SELECT_BRAND    = "🏷 **Brand বেছে নিন**\n\nকোন Institute এর Course দেখতে চান?"
    SELECT_BATCH    = "📦 **Batch বেছে নিন**\n\n🏷 __Brand:__ `{brand}`\n\nকোন Batch এর Course দেখতে চান?"
    SELECT_CATEGORY = "📂 **Category বেছে নিন**\n\n🏷 __Brand:__ `{brand}`\n📦 __Batch:__ `{batch}`\n\nকোন Category দেখতে চান?"
    SELECT_SUBJECT  = "📖 **Subject বেছে নিন**\n\n🏷 __Brand:__ `{brand}`\n📦 __Batch:__ `{batch}`\n📂 __Category:__ `{category}`\n\nকোন Subject এর Course দেখতে চান?"
    SELECT_COURSE   = "🎓 **Available Courses**\n\n**{brand}** › **{batch}** › **{category}** › **{subject}**\n\nএকটা Course বেছে নিন 👇"

    NO_BATCHES    = "⚠️ এই Brand এ কোনো Batch পাওয়া যায়নি।"
    NO_CATEGORIES = "⚠️ এই Batch এ কোনো Category পাওয়া যায়নি।"
    NO_SUBJECTS   = "⚠️ এই Category তে কোনো Subject পাওয়া যায়নি।"
    NO_COURSES    = "⚠️ এই Subject এ কোনো Course পাওয়া যায়নি।"

    # ══════════════════════════════════════════════════════════
    #  5. COURSE DETAIL
    # ══════════════════════════════════════════════════════════

    COURSE_DETAIL = (
        "🎓 **{name}**\n\n"
        "🏷 __Brand:__    `{brand}`\n"
        "📦 __Batch:__    `{batch}`\n"
        "📂 __Category:__ `{category}`\n"
        "📖 __Subject:__  `{subject}`\n\n"
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
    #  6. PAYMENT — METHOD SELECTION (শুধু bKash ও Nagad)
    # ══════════════════════════════════════════════════════════

    PAYMENT_METHOD_SELECT = (
        "💳 **Payment করুন**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 **Course:** `{name}`\n"
        "💰 **মূল্য:** `{currency} {price}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "নিচের যেকোনো পদ্ধতিতে Payment করুন 👇\n\n"
        "📲 **bKash**\n"
        "└ বাংলাদেশী Mobile Banking\n\n"
        "📲 **Nagad**\n"
        "└ বাংলাদেশী Mobile Banking\n\n"
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
        "📞 সাহায্য: {support}"
    )

    # ══════════════════════════════════════════════════════════
    #  9. PROOF — Phone ও Screenshot চাওয়া
    # ══════════════════════════════════════════════════════════

    PROOF_ASK_PHONE = (
        "📱 **Payment এর Phone Number দিন**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 **Course:** `{course_name}`\n"
        "💰 **Amount:** `{currency} {price}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "যে নম্বর থেকে payment করেছেন সেটা দিন:\n"
        "_e.g. 01712345678_\n\n"
        "⏭ **Skip** করলে phone number ছাড়াই জমা হবে।"
    )

    PROOF_ASK_SCREENSHOT = (
        "📸 **Payment Screenshot দিন** _(ঐচ্ছিক)_\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 **Course:** `{course_name}`\n"
        "💰 **Amount:** `{currency} {price}`\n"
        "💳 **Method:** `{method}`\n"
        "{phone_line}"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Payment এর screenshot পাঠান অথবা **Skip** করুন।\n\n"
        "⏭ Screenshot না দিলেও আপনার request জমা হবে।\n"
        "Admin manually verify করবেন।"
    )

    PROOF_SUBMITTED = (
        "✅ **Payment Request জমা হয়েছে!**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 **Course:** `{course_name}`\n"
        "💳 **Method:** `{method}`\n"
        "📱 **Phone:** `{phone}`\n"
        "🆔 **Proof ID:** `#{proof_id}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⏳ Admin আপনার payment verify করছেন।\n"
        "সাধারণত কয়েক মিনিটের মধ্যে Confirm হবে।\n\n"
        "Confirm হলে এখানে notification পাবেন।\n\n"
        "📞 সাহায্য: {support}"
    )

    PROOF_ALREADY_PENDING = (
        "⚠️ **আপনার আগের Payment Request এখনো Pending!**\n\n"
        "📦 Course: `{course_name}`\n"
        "🆔 Proof ID: `#{proof_id}`\n\n"
        "Admin verify করা পর্যন্ত অপেক্ষা করুন।\n"
        "📞 সাহায্য: {support}"
    )

    NO_DIRECT_PAYMENT = (
        "ℹ️ **অন্য Payment পদ্ধতির জন্য**\n\n"
        "bKash বা Nagad ছাড়া অন্য কোনো পদ্ধতিতে\n"
        "payment করতে চাইলে সরাসরি যোগাযোগ করুন:\n\n"
        "📞 **Support:** {support}"
    )

    # ══════════════════════════════════════════════════════════
    #  10. PAYMENT APPROVED — Membership Card ← নতুন format
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
    #  MEMBERSHIP CARD  ← আপনার চাহিদামতো বিশেষ format
    # ══════════════════════════════════════════════════════════

    MEMBERSHIP_CARD = (
        "🎉 **Congratulations!** 🎉\n\n"
        "আপনি সফলভাবে আমাদের কোর্স ক্রয় করেছেন।\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 **Membership ID :** `{membership_id}`\n"
        "📌 **Name :** {name}\n"
        "📌 **Phone :** `{phone}`\n"
        "📌 **Course :** {course_name}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👉 অনুগ্রহ করে এই মেসেজটি যত্ন করে সংরক্ষণ করবেন।\n"
        "ভবিষ্যতে কোনো সমস্যার ক্ষেত্রে আপনি যে আমাদের থেকে\n"
        "কোর্স কিনছেন সেটার প্রমাণ হিসেবে দেখাতে পারবেন।\n\n"
        "আমাদের উপর বিশ্বাস রাখার জন্য আন্তরিক ধন্যবাদ। 💙"
    )

    MEMBERSHIP_CARD_NO_PHONE = (
        "🎉 **Congratulations!** 🎉\n\n"
        "আপনি সফলভাবে আমাদের কোর্স ক্রয় করেছেন।\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 **Membership ID :** `{membership_id}`\n"
        "📌 **Name :** {name}\n"
        "📌 **Course :** {course_name}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👉 অনুগ্রহ করে এই মেসেজটি যত্ন করে সংরক্ষণ করবেন।\n"
        "ভবিষ্যতে কোনো সমস্যার ক্ষেত্রে আপনি যে আমাদের থেকে\n"
        "কোর্স কিনছেন সেটার প্রমাণ হিসেবে দেখাতে পারবেন।\n\n"
        "আমাদের উপর বিশ্বাস রাখার জন্য আন্তরিক ধন্যবাদ। 💙"
    )

    # ══════════════════════════════════════════════════════════
    #  11. PAYMENT REJECTED
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
    #  12. ONE-TIME INVITE LINK
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
        "• Link কারো সাথে **Share করবেন না**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📞 সমস্যা হলে: {support}"
    )

    # ══════════════════════════════════════════════════════════
    #  13. MY ORDERS
    # ══════════════════════════════════════════════════════════

    MY_ORDERS_EMPTY = (
        "🛒 **আমার Orders**\n\n"
        "আপনি এখনো কোনো Course কেনেননি।\n\n"
        "📚 Course দেখতে **Browse Courses** বাটনে ক্লিক করুন।"
    )

    MY_ORDERS_HEADER = "🛒 **আমার Orders**\n\nআপনার সব Order নিচে দেখানো হচ্ছে:\n"

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
    #  14. PROFILE
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
    #  15. ERROR MESSAGES
    # ══════════════════════════════════════════════════════════

    ERROR_GENERIC             = "❌ **কিছু একটা সমস্যা হয়েছে।**\n\nআবার চেষ্টা করুন অথবা যোগাযোগ করুন:\n📞 {support}"
    ERROR_COURSE_NOT_FOUND    = "❌ **Course টি পাওয়া যায়নি।**\n\nCourse টি হয়তো সরিয়ে নেওয়া হয়েছে।"
    ERROR_ORDER_NOT_FOUND     = "❌ **Order টি পাওয়া যায়নি।**\n\nOrder ID: `{order_id}`"
    ERROR_PAYMENT_PROCESSING  = "⚠️ **Payment Received কিন্তু Processing এ সমস্যা!**\n\nTransaction ID সহ Admin কে জানান:\n📞 {support}"
    ERROR_ACCESS_DENIED       = "⛔ **Access Denied**\n\nএই কাজটি করার Permission আপনার নেই।"
    ERROR_GROUP_NO_ACCESS     = "❌ **Group Access দেওয়া সম্ভব হয়নি!**\n\nAdmin কে জানান:\n📞 {support}\n\nOrder ID: `{order_id}`"

    # ══════════════════════════════════════════════════════════
    #  16. ADMIN NOTIFICATIONS
    # ══════════════════════════════════════════════════════════

    # ← নতুন: কেউ কোর্স কিনলে admin কে নাম, বিকাশ নম্বর, কোর্সের নাম পাঠানো
    ADMIN_PURCHASE_LOG = (
        "🔔 **নতুন Course Purchase!**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "👤 **ID নাম:** [{user_name}](tg://user?id={user_id}) (`{user_id}`)\n"
        "📱 **বিকাশ/নগদ নম্বর:** `{phone}`\n"
        "📦 **কোর্সের নাম:** `{course_name}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🆔 **Order ID:** `{order_id}`\n"
        "💳 **Method:** `{method}`\n"
        "📅 **সময়:** {date}"
    )

    ADMIN_NEW_PROOF = (
        "🔔 **নতুন Payment Proof জমা হয়েছে!**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "👤 **User:** [{user_name}](tg://user?id={user_id}) (`{user_id}`)\n"
        "📛 **Username:** {username}\n"
        "📱 **Phone:** `{phone}`\n"
        "📦 **Course:** {course_name}\n"
        "💰 **Amount:** {currency} {price}\n"
        "💳 **Method:** {method}\n"
        "🆔 **Proof ID:** `#{proof_id}`\n"
        "📝 **Note:** {caption}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⬇️ Verify করে Approve বা Reject করুন:"
    )

    ADMIN_NEW_MANUAL_PAYMENT = (
        "🔔 **নতুন Manual Payment!**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "👤 **User:** [{user_name}](tg://user?id={user_id}) (`{user_id}`)\n"
        "📛 **Username:** {username}\n"
        "📦 **Course:** {course_name}\n"
        "💰 **Amount:** {currency} {price}\n"
        "💳 **Method:** {method}\n"
        "🆔 **Order ID:** `{order_id}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⬇️ Verify করে Approve বা Reject করুন:"
    )

    ADMIN_OTL_SUCCESS = (
        "✅ **Approved & One-Time Link Sent!**\n\n"
        "👤 **User:** [{user_name}](tg://user?id={user_id}) (`{user_id}`)\n"
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
        "👤 **User:** [{user_name}](tg://user?id={user_id}) (`{user_id}`)\n\n"
        "Admin Panel → List Courses → এই Course এ\n"
        "Group যোগ করুন।"
    )

    ADMIN_ORDER_APPROVED_CONFIRM = "✅ Order `{order_id_short}` **Approved!**"
    ADMIN_ORDER_REJECTED_CONFIRM = "❌ Order `{order_id_short}` **Rejected.**"

    # ══════════════════════════════════════════════════════════
    #  17. GENERAL / MISC
    # ══════════════════════════════════════════════════════════

    BROADCAST_SENDING = "📢 **{total_users}** জন User কে Broadcast হচ্ছে...\nঅপেক্ষা করুন।"
    BROADCAST_DONE    = "✅ **Broadcast সম্পন্ন!**\n\n✅ Sent:   {sent}\n❌ Failed: {failed}"

    GROUP_CHECK_SUCCESS   = "✅ **সব ঠিক আছে!**\n\n🆔 Group ID: `{group_id}`\n👑 Bot Status: Admin ✅\n🔗 Invite Permission: ✅\n\nএই Group ID টা Course এ Add করতে পারবেন।"
    GROUP_CHECK_NO_INVITE = "⚠️ **Bot Admin কিন্তু Invite Permission নেই!**\n\n🆔 Group ID: `{group_id}`\n\n**সমাধান:**\nGroup → Admin Settings → Bot →\n'Invite Users via Link' চালু করুন।"
    GROUP_CHECK_NOT_ADMIN = "❌ **Bot Admin না!**\n\n🆔 Group ID: `{group_id}`\n\n**সমাধান:**\n1. Group এ যান\n2. Members → Bot → Promote to Admin\n3. আবার `/checkgroup {group_id}` দিন"
    GROUP_CHECK_ERROR     = "❌ **Error:**\n`{error}`\n\n**সমাধান:**\n1. Bot কে Group এ Add করুন\n2. Bot কে Admin বানান\n3. 'Invite Users via Link' Permission দিন"
    GROUP_CHECKING        = "⏳ Group `{group_id}` check হচ্ছে..."

    SUPPORT_BUTTON_LABEL  = "💬 Support: {support}"
    JOIN_GROUP_BUTTON_LABEL = "🚀 Group এ Join করুন"
