from telebot import TeleBot, types
from telebot.types import Message, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from md2tgmd import escape
import traceback
from config import conf
import gemini
from channel_checker import check_membership, get_join_channel_markup, CHANNEL_ID
import time
from markups import get_user_reply_markup

error_info              =       conf["error_info"]
before_generate_info    =       conf["before_generate_info"]
download_pic_notify     =       conf["download_pic_notify"]
model_1                 =       conf["model_1"]
model_2                 =       conf["model_2"]

gemini_chat_dict        = gemini.gemini_chat_dict
gemini_pro_chat_dict    = gemini.gemini_pro_chat_dict
default_model_dict      = gemini.default_model_dict
gemini_draw_dict        = gemini.gemini_draw_dict

user_message_times = {}

# دیکشنری برای ذخیره state تولید محتوا برای هر کاربر
# مقدار: {'type': نوع دسته, 'last_message_id': آیدی پیام راهنما}
user_content_state = {}

def get_welcome_markup() -> InlineKeyboardMarkup:
    """
    ایجاد دکمه‌های خوش‌آمدگویی
    """
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🚀 شروع استفاده از ربات", url="https://t.me/fibonacciaibot"))
    return markup

def get_assistants_markup() -> InlineKeyboardMarkup:
    """
    ایجاد دکمه‌های دستیارها
    """
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("👨‍💻 برنامه‌نویس", callback_data="assistant_programmer"),
        InlineKeyboardButton("🎨 گرافیست", callback_data="assistant_designer")
    )
    markup.add(
        InlineKeyboardButton("📝 نویسنده", callback_data="assistant_writer"),
        InlineKeyboardButton("🎓 معلم", callback_data="assistant_teacher")
    )
    markup.add(
        InlineKeyboardButton("🌐 مترجم و زبان", callback_data="assistant_translator"),
        InlineKeyboardButton("💼 مشاور شغلی", callback_data="assistant_job")
    )
    markup.add(
        InlineKeyboardButton("📢 بازاریابی و تبلیغات", callback_data="assistant_marketing"),
        InlineKeyboardButton("📄 حقوقی و قرارداد", callback_data="assistant_legal")
    )
    markup.add(
        InlineKeyboardButton("💬 روانشناسی و انگیزشی", callback_data="assistant_psychology"),
        InlineKeyboardButton("✈️ سفر و گردشگری", callback_data="assistant_travel")
    )
    markup.add(
        InlineKeyboardButton("💰 مالی و حسابداری", callback_data="assistant_finance"),
        InlineKeyboardButton("🍏 سلامت و تغذیه", callback_data="assistant_health")
    )
    markup.add(
        InlineKeyboardButton("📚 شعر و ادبیات", callback_data="assistant_poetry"),
        InlineKeyboardButton("🧸 کودک و سرگرمی", callback_data="assistant_kids")
    )
    markup.add(
        InlineKeyboardButton("📰 اخبار و اطلاعات روز", callback_data="assistant_news")
    )
    return markup

def get_content_menu_markup() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✍️ مقاله و پست وبلاگ", callback_data="content_article"),
        InlineKeyboardButton("📱 کپشن و شبکه اجتماعی", callback_data="content_caption")
    )
    markup.add(
        InlineKeyboardButton("💡 ایده‌پردازی و عنوان‌سازی", callback_data="content_idea"),
        InlineKeyboardButton("📧 ایمیل و پیام اداری", callback_data="content_email")
    )
    markup.add(
        InlineKeyboardButton("📖 داستان و متن خلاقانه", callback_data="content_story"),
        InlineKeyboardButton("🌐 ترجمه و بومی‌سازی", callback_data="content_translate")
    )
    markup.add(
        InlineKeyboardButton("📝 ویرایش و اصلاح متن", callback_data="content_edit"),
        InlineKeyboardButton("📄 رزومه و نامه اداری", callback_data="content_resume")
    )
    markup.add(
        InlineKeyboardButton("🛒 متن سایت و فروشگاه", callback_data="content_shop"),
        InlineKeyboardButton("📢 تبلیغات و کمپین", callback_data="content_ad")
    )
    markup.add(
        InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_main_menu")
    )
    return markup

def get_support_markup() -> InlineKeyboardMarkup:
    """
    ایجاد دکمه‌های حمایت مالی
    """
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("💎 حمایت مالی", url="https://zarinp.al/707658"),
        InlineKeyboardButton("📢 کانال ما", url="https://t.me/fibonacciai")
    )
    markup.add(
        InlineKeyboardButton("📱 کانال آپارات", url="https://www.aparat.com/fibonaccii"),
        InlineKeyboardButton("📚 وبلاگ آموزشی", url="https://fibonacci.monster/blog/")
    )
    markup.add(
        InlineKeyboardButton("🤖 دستیارهای هوشمند", callback_data="show_assistants"),
        InlineKeyboardButton("📝 تولید محتوای متنی", callback_data="show_content_menu"),
        InlineKeyboardButton("🛠 ابزارهای متنی ویژه", callback_data="show_special_tools")
    )
    return markup

def get_special_tools_markup() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎤 تبدیل ویس به متن", callback_data="tool_speech2text"),
        InlineKeyboardButton("🎉 پیام تبریک و مناسبتی", callback_data="tool_congrats")
    )
    markup.add(
        InlineKeyboardButton("😂 متن طنز و شوخی", callback_data="tool_funny"),
        InlineKeyboardButton("🎬 دیالوگ و سناریو", callback_data="tool_dialogue")
    )
    markup.add(
        InlineKeyboardButton("🎙 متن پادکست/ویدیو", callback_data="tool_podcast")
    )
    markup.add(
        InlineKeyboardButton("💪 پیام انگیزشی روزانه", callback_data="tool_motivation"),
        InlineKeyboardButton("🧩 معما و بازی فکری", callback_data="tool_puzzle")
    )
    markup.add(
        InlineKeyboardButton("👤 بیو شبکه اجتماعی", callback_data="tool_bio"),
        InlineKeyboardButton("💌 کارت دعوت و مراسم", callback_data="tool_invite")
    )
    markup.add(
        InlineKeyboardButton("💔 خداحافظی و دل‌نوشته", callback_data="tool_farewell"),
        InlineKeyboardButton("🚀 شعار تبلیغاتی", callback_data="tool_slogan")
    )
    markup.add(
        InlineKeyboardButton("🏆 پیام چالش و مسابقه", callback_data="tool_challenge"),
        InlineKeyboardButton("📱 معرفی اپ/استارتاپ", callback_data="tool_appintro")
    )
    markup.add(
        InlineKeyboardButton("🤝 پشتیبانی و پاسخ مشتری", callback_data="tool_support"),
        InlineKeyboardButton("📖 راهنمای محصول/آموزش", callback_data="tool_guide")
    )
    markup.add(
        InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_main_menu")
    )
    return markup

def start(message: Message, bot: TeleBot) -> None:
    bot.send_message(message.chat.id, "سلام! ربات آماده است.")

def gemini_stream_handler(message: Message, bot: TeleBot) -> None:
    bot.send_message(message.chat.id, "پاسخ تست جمینی (sync)")

def gemini_pro_stream_handler(message: Message, bot: TeleBot) -> None:
    bot.send_message(message.chat.id, "پاسخ تست جمینی پرو (sync)")

def clear(message: Message, bot: TeleBot) -> None:
    bot.send_message(message.chat.id, "تاریخچه پاک شد (sync)")

def switch(message: Message, bot: TeleBot) -> None:
    bot.send_message(message.chat.id, "مدل تغییر کرد (sync)")

def gemini_private_handler(message: Message, bot: TeleBot) -> None:
    bot.send_message(message.chat.id, "پاسخ تست خصوصی (sync)")

def gemini_photo_handler(message: Message, bot: TeleBot) -> None:
    bot.send_message(message.chat.id, "عکس دریافت شد (sync)")

def gemini_edit_handler(message: Message, bot: TeleBot) -> None:
    bot.send_message(message.chat.id, "ویرایش عکس (sync)")

def draw_handler(message: Message, bot: TeleBot) -> None:
    bot.send_message(message.chat.id, "طراحی تصویر (sync)")

def handle_assistant_callback(call: types.CallbackQuery, bot: TeleBot) -> None:
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "دستیار انتخاب شد (sync)")

def handle_content_text(message: Message, bot: TeleBot) -> None:
    bot.send_message(message.chat.id, "پاسخ تولید محتوا (sync)")

def handle_content_callback(call: types.CallbackQuery, bot: TeleBot) -> None:
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "دسته‌بندی محتوا انتخاب شد (sync)")

def handle_special_tools_callback(call: types.CallbackQuery, bot: TeleBot) -> None:
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "ابزار ویژه انتخاب شد (sync)")

async def check_rate_limit(message: Message, bot: TeleBot) -> bool:
    """
    بررسی محدودیت تعداد پیام در دقیقه برای هر کاربر
    """
    user_id = message.from_user.id
    now = time.time()
    times = user_message_times.get(user_id, [])
    # فقط پیام‌های ۶۰ ثانیه اخیر را نگه می‌داریم
    times = [t for t in times if now - t < 60]
    if len(times) >= 4:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💎 ارتقا به نامحدود", url="https://zarinp.al/707658"))
        await bot.reply_to(message, "🚫 شما در هر دقیقه فقط مجاز به ارسال ۴ پیام هستید.\nبرای استفاده نامحدود، اشتراک تهیه کنید.", reply_markup=markup)
        return False
    times.append(now)
    user_message_times[user_id] = times
    return True

async def check_user_membership(message: Message, bot: TeleBot) -> bool:
    """
    بررسی عضویت کاربر در کانال
    """
    if not await check_membership(bot, message.from_user.id):
        await bot.reply_to(
            message,
            "⚠️ برای استفاده از ربات، ابتدا باید در کانال ما عضو شوید:",
            reply_markup=get_join_channel_markup()
        )
        return False
    return True

async def handle_channel_membership(chat_member: ChatMemberUpdated, bot: TeleBot) -> None:
    """
    هندلر رویداد عضویت در کانال
    """
    if chat_member.chat.id == CHANNEL_ID and chat_member.new_chat_member.status in ['member', 'administrator', 'creator']:
        welcome_text = escape(f"""
👋 سلام {chat_member.new_chat_member.user.first_name} عزیز!

🤖 به ربات هوش مصنوعی فیبوناچی خوش آمدید!

📝 شما می‌تونید:
• سوالات خود رو بپرسید
• از دستور /gemini برای استفاده از مدل پیشرفته استفاده کنید
• از دستور /draw برای طراحی تصاویر استفاده کنید
• از دستور /edit برای ویرایش عکس‌ها استفاده کنید

💡 مثال‌ها:
• `/gemini هوش مصنوعی چیست؟`
• `/draw یک گربه بامزه بکش`
• `عکس من رو به سبک انیمه تغییر بده`

🔄 برای پاک کردن تاریخچه چت از دستور /clear استفاده کنید
🔄 برای تغییر مدل پیش‌فرض از دستور /switch استفاده کنید

❓ اگر سوالی دارید، در کانال ما بپرسید: @fibonacciai

💝 اگر از ربات راضی هستید، می‌تونید از ما حمایت کنید
""")
        try:
            # ارسال پیام خصوصی به کاربر
            await bot.send_message(
                chat_member.new_chat_member.user.id,
                welcome_text,
                parse_mode="MarkdownV2",
                reply_markup=get_support_markup()
            )
        except Exception as e:
            print(f"Error sending welcome message: {e}")
            # اگر نتوانست پیام خصوصی بفرستد، در کانال ارسال می‌کند
            try:
                await bot.send_message(
                    CHANNEL_ID,
                    f"🎉 به {chat_member.new_chat_member.user.first_name} عزیز خوش آمدید!\nبرای استفاده از ربات، به @fibonacciaibot مراجعه کنید.",
                    reply_markup=get_welcome_markup()
                )
            except Exception as e2:
                print(f"Error sending channel message: {e2}")

def is_creator_question(text: str) -> bool:
    text = text.lower().strip()
    keywords = [
        # فارسی
        "سازنده تو کیست",
        "تو توسط چه کسی ساخته شدی",
        "چه شرکتی تو را ساخته",
        "آیا تو ساخت گوگل هستی",
        "آیا تو gemini هستی",
        "آیا تو از مدل gemini استفاده می‌کنی",
        "آیا تو از مدل گوگل استفاده می‌کنی",
        "آیا تو توسط google ساخته شدی",
        "آیا تو توسط google توسعه داده شدی",
        "مدل هوش مصنوعی تو چیست",
        "مدل تو چیست",
        "مدل زبانی تو چیست",
        "مدل پایه تو چیست",
        "آیا تو از مدل‌های گوگل استفاده می‌کنی",
        "آیا تو gemini ai هستی",
        "آیا تو از هوش مصنوعی گوگل استفاده می‌کنی",
        "آیا تو از هوش مصنوعی جمینی استفاده می‌کنی",
        "آیا تو از api گوگل استفاده می‌کنی",
        "آیا تو از api جمینی استفاده می‌کنی",
        "آیا تو از سرویس گوگل استفاده می‌کنی",
        "آیا تو از سرویس جمینی استفاده می‌کنی",
        "آیا تو ربات گوگل هستی",
        "آیا تو ربات جمینی هستی",
        "آیا تو با گوگل کار می‌کنی",
        "آیا تو با جمینی کار می‌کنی",
        "آیا تو به گوگل وصل هستی",
        "آیا تو به جمینی وصل هستی",
        "آیا تو از دیتابیس گوگل استفاده می‌کنی",
        "آیا تو از دیتابیس جمینی استفاده می‌کنی",
        "آیا تو از تکنولوژی گوگل استفاده می‌کنی",
        "آیا تو از تکنولوژی جمینی استفاده می‌کنی",
        "آیا تو از موتور گوگل استفاده می‌کنی",
        "آیا تو از موتور جمینی استفاده می‌کنی",
        "آیا تو از پلتفرم گوگل استفاده می‌کنی",
        "آیا تو از پلتفرم جمینی استفاده می‌کنی",
        "آیا تو از مدل زبانی گوگل استفاده می‌کنی",
        "آیا تو از مدل زبانی جمینی استفاده می‌کنی",
        "آیا تو از مدل زبانی بزرگ گوگل استفاده می‌کنی",
        "آیا تو از مدل زبانی بزرگ جمینی استفاده می‌کنی",
        "آیا تو از llm گوگل استفاده می‌کنی",
        "آیا تو از llm جمینی استفاده می‌کنی",
        "آیا تو llm گوگل هستی",
        "آیا تو llm جمینی هستی",
        "آیا تو gemini llm هستی",
        "آیا تو google llm هستی",
        "آیا تو gemini chatbot هستی",
        "آیا تو google chatbot هستی",
        "آیا تو gemini assistant هستی",
        "آیا تو google assistant هستی",
        "آیا تو gemini api هستی",
        "آیا تو google api هستی",
        "آیا تو gemini engine هستی",
        "آیا تو google engine هستی",
        "آیا تو gemini technology هستی",
        "آیا تو google technology هستی",
        "آیا تو gemini platform هستی",
        "آیا تو google platform هستی",
        "آیا تو gemini service هستی",
        "آیا تو google service هستی",
        "آیا تو gemini developer هستی",
        "آیا تو google developer هستی",
        "آیا تو gemini creator هستی",
        "آیا تو google creator هستی",
        "آیا تو gemini ساخته شدی",
        "آیا تو google ساخته شدی",
        "آیا تو gemini توسعه داده شدی",
        "آیا تو google توسعه داده شدی",
        "آیا تو gemini برنامه‌نویسی شدی",
        "آیا تو google برنامه‌نویسی شدی",
        "آیا تو gemini طراحی شدی",
        "آیا تو google طراحی شدی",
        # انگلیسی
        "who created you",
        "who made you",
        "who is your creator",
        "who developed you",
        "who built you",
        "who designed you",
        "who programmed you",
        "who is your developer",
        "what is your base model",
        "what ai model do you use",
        "what is your technology",
        "what is your engine",
        "do you use google gemini",
        "do you use google ai",
        "is your backend google",
        "is your backend gemini",
        "is your engine gemini",
        "is your engine google",
        "is your technology google",
        "is your technology gemini",
        "is your model google",
        "is your model gemini",
        "are you made by google",
        "are you gemini",
        "are you using gemini model",
        "are you a google bot",
        "are you based on google ai",
        "are you based on gemini ai",
        "are you a gemini bot",
        "are you a gemini assistant",
        "are you a google assistant",
        "are you a gemini chatbot",
        "are you a google chatbot",
        "are you a gemini api",
        "are you a google api",
        "are you a gemini engine",
        "are you a google engine",
        "are you a gemini technology",
        "are you a google technology",
        "are you a gemini platform",
        "are you a google platform",
        "are you a gemini service",
        "are you a google service",
        "are you a gemini developer",
        "are you a google developer",
        "are you a gemini creator",
        "are you a google creator"
    ]
    for k in keywords:
        if k in text:
            return True
    return False

async def handle_channel_membership(chat_member: ChatMemberUpdated, bot: TeleBot) -> None:
    """
    هندلر رویداد عضویت در کانال
    """
    if chat_member.chat.id == CHANNEL_ID and chat_member.new_chat_member.status in ['member', 'administrator', 'creator']:
        welcome_text = escape(f"""
👋 سلام {chat_member.new_chat_member.user.first_name} عزیز!

🤖 به ربات هوش مصنوعی فیبوناچی خوش آمدید!

📝 شما می‌تونید:
• سوالات خود رو بپرسید
• از دستور /gemini برای استفاده از مدل پیشرفته استفاده کنید
• از دستور /draw برای طراحی تصاویر استفاده کنید
• از دستور /edit برای ویرایش عکس‌ها استفاده کنید

💡 مثال‌ها:
• `/gemini هوش مصنوعی چیست؟`
• `/draw یک گربه بامزه بکش`
• `عکس من رو به سبک انیمه تغییر بده`

🔄 برای پاک کردن تاریخچه چت از دستور /clear استفاده کنید
🔄 برای تغییر مدل پیش‌فرض از دستور /switch استفاده کنید

❓ اگر سوالی دارید، در کانال ما بپرسید: @fibonacciai

💝 اگر از ربات راضی هستید، می‌تونید از ما حمایت کنید
""")
        try:
            # ارسال پیام خصوصی به کاربر
            await bot.send_message(
                chat_member.new_chat_member.user.id,
                welcome_text,
                parse_mode="MarkdownV2",
                reply_markup=get_support_markup()
            )
        except Exception as e:
            print(f"Error sending welcome message: {e}")
            # اگر نتوانست پیام خصوصی بفرستد، در کانال ارسال می‌کند
            try:
                await bot.send_message(
                    CHANNEL_ID,
                    f"🎉 به {chat_member.new_chat_member.user.first_name} عزیز خوش آمدید!\nبرای استفاده از ربات، به @fibonacciaibot مراجعه کنید.",
                    reply_markup=get_welcome_markup()
                )
            except Exception as e2:
                print(f"Error sending channel message: {e2}")
