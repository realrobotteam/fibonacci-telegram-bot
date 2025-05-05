from telebot import TeleBot, types
from telebot.types import Message, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from md2tgmd import escape
import traceback
from config import conf
import gemini
from channel_checker import check_membership, get_join_channel_markup, CHANNEL_ID
import time

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
        InlineKeyboardButton("📝 تولید محتوای متنی", callback_data="show_content_menu")
    )
    return markup

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

async def start(message: Message, bot: TeleBot) -> None:
    if not await check_rate_limit(message, bot):
        return
    if is_creator_question(message.text):
        await bot.reply_to(message, escape("من توسط تیم هوش مصنوعی فیبوناچی ساخته شدم."), parse_mode="MarkdownV2")
        return
    try:
        if not await check_user_membership(message, bot):
            return
        welcome_text = escape(f"""
👋 سلام {message.from_user.first_name} عزیز!

🤖 به ربات هوش مصنوعی فیبوناچی خوش آمدید!

📝 شما می‌تونید:
• سوالات خود رو بپرسید
• از دستور /gemini برای استفاده از مدل پیشرفته استفاده کنید
• از دستور /draw برای طراحی تصاویر استفاده کنید
• از دستور /edit برای ویرایش عکس‌ها استفاده کنید
• از دستیارهای هوشمند ما استفاده کنید

💡 مثال‌ها:
• `/gemini هوش مصنوعی چیست؟`
• `/draw یک گربه بامزه بکش`
• `عکس من رو به سبک انیمه تغییر بده`

🔄 برای پاک کردن تاریخچه چت از دستور /clear استفاده کنید
🔄 برای تغییر مدل پیش‌فرض از دستور /switch استفاده کنید

❓ اگر سوالی دارید، در کانال ما بپرسید: @fibonacciai

💝 اگر از ربات راضی هستید، می‌تونید از ما حمایت کنید
""")
        await bot.reply_to(message, welcome_text, parse_mode="MarkdownV2", reply_markup=get_support_markup())
    except IndexError:
        await bot.reply_to(message, error_info)

async def gemini_stream_handler(message: Message, bot: TeleBot) -> None:
    if not await check_rate_limit(message, bot):
        return
    if is_creator_question(message.text):
        await bot.reply_to(message, escape("من توسط تیم هوش مصنوعی فیبوناچی ساخته شدم."), parse_mode="MarkdownV2")
        return
    if not await check_user_membership(message, bot):
        return
    try:
        m = message.text.strip().split(maxsplit=1)[1].strip()
    except IndexError:
        await bot.reply_to(message, escape("Please add what you want to say after /gemini. \nFor example: `/gemini Who is john lennon?`"), parse_mode="MarkdownV2")
        return
    await gemini.gemini_stream(bot, message, m, model_1)

async def gemini_pro_stream_handler(message: Message, bot: TeleBot) -> None:
    if not await check_rate_limit(message, bot):
        return
    if is_creator_question(message.text):
        await bot.reply_to(message, escape("من توسط تیم هوش مصنوعی فیبوناچی ساخته شدم."), parse_mode="MarkdownV2")
        return
    if not await check_user_membership(message, bot):
        return
    try:
        m = message.text.strip().split(maxsplit=1)[1].strip()
    except IndexError:
        await bot.reply_to(message, escape("Please add what you want to say after /gemini_pro. \nFor example: `/gemini_pro Who is john lennon?`"), parse_mode="MarkdownV2")
        return
    await gemini.gemini_stream(bot, message, m, model_2)

async def clear(message: Message, bot: TeleBot) -> None:
    if not await check_rate_limit(message, bot):
        return
    if not await check_user_membership(message, bot):
        return
    # Check if the chat is already in gemini_chat_dict.
    if (str(message.from_user.id) in gemini_chat_dict):
        del gemini_chat_dict[str(message.from_user.id)]
    if (str(message.from_user.id) in gemini_pro_chat_dict):
        del gemini_pro_chat_dict[str(message.from_user.id)]
    if (str(message.from_user.id) in gemini_draw_dict):
        del gemini_draw_dict[str(message.from_user.id)]
    await bot.reply_to(message, "Your history has been cleared")

async def switch(message: Message, bot: TeleBot) -> None:
    if not await check_rate_limit(message, bot):
        return
    if not await check_user_membership(message, bot):
        return
    if message.chat.type != "private":
        await bot.reply_to( message , "This command is only for private chat !")
        return
    # Check if the chat is already in default_model_dict.
    if str(message.from_user.id) not in default_model_dict:
        default_model_dict[str(message.from_user.id)] = False
        await bot.reply_to( message , "Now you are using "+model_2)
        return
    if default_model_dict[str(message.from_user.id)] == True:
        default_model_dict[str(message.from_user.id)] = False
        await bot.reply_to( message , "Now you are using "+model_2)
    else:
        default_model_dict[str(message.from_user.id)] = True
        await bot.reply_to( message , "Now you are using "+model_1)

async def gemini_private_handler(message: Message, bot: TeleBot) -> None:
    if not await check_rate_limit(message, bot):
        return
    if not await check_user_membership(message, bot):
        return
    m = message.text.strip()
    if is_creator_question(m):
        await bot.reply_to(message, escape("من توسط تیم هوش مصنوعی فیبوناچی ساخته شدم."), parse_mode="MarkdownV2")
        return
    if str(message.from_user.id) not in default_model_dict:
        default_model_dict[str(message.from_user.id)] = True
        await gemini.gemini_stream(bot, message, m, model_1)
    else:
        if default_model_dict[str(message.from_user.id)]:
            await gemini.gemini_stream(bot, message, m, model_1)
        else:
            await gemini.gemini_stream(bot, message, m, model_2)

async def gemini_photo_handler(message: Message, bot: TeleBot) -> None:
    if not await check_rate_limit(message, bot):
        return
    if not await check_user_membership(message, bot):
        return
    if message.chat.type != "private":
        s = message.caption or ""
        if not s or not (s.startswith("/gemini")):
            return
        try:
            m = s.strip().split(maxsplit=1)[1].strip() if len(s.strip().split(maxsplit=1)) > 1 else ""
            file_path = await bot.get_file(message.photo[-1].file_id)
            photo_file = await bot.download_file(file_path.file_path)
        except Exception:
            traceback.print_exc()
            await bot.reply_to(message, error_info)
            return
        await gemini.gemini_edit(bot, message, m, photo_file)
    else:
        s = message.caption or ""
        try:
            m = s.strip().split(maxsplit=1)[1].strip() if len(s.strip().split(maxsplit=1)) > 1 else ""
            file_path = await bot.get_file(message.photo[-1].file_id)
            photo_file = await bot.download_file(file_path.file_path)
        except Exception:
            traceback.print_exc()
            await bot.reply_to(message, error_info)
            return
        await gemini.gemini_edit(bot, message, m, photo_file)

async def gemini_edit_handler(message: Message, bot: TeleBot) -> None:
    if not await check_rate_limit(message, bot):
        return
    if not await check_user_membership(message, bot):
        return
    if not message.photo:
        await bot.reply_to(message, "pls send a photo")
        return
    s = message.caption or ""
    try:
        m = s.strip().split(maxsplit=1)[1].strip() if len(s.strip().split(maxsplit=1)) > 1 else ""
        file_path = await bot.get_file(message.photo[-1].file_id)
        photo_file = await bot.download_file(file_path.file_path)
    except Exception as e:
        traceback.print_exc()
        await bot.reply_to(message, e.str())
        return
    await gemini.gemini_edit(bot, message, m, photo_file)

async def draw_handler(message: Message, bot: TeleBot) -> None:
    if not await check_rate_limit(message, bot):
        return
    if not await check_user_membership(message, bot):
        return
    try:
        m = message.text.strip().split(maxsplit=1)[1].strip()
    except IndexError:
        await bot.reply_to(message, escape("Please add what you want to draw after /draw. \nFor example: `/draw draw me a cat.`"), parse_mode="MarkdownV2")
        return
    
    # reply to the message first, then delete the "drawing..." message
    drawing_msg = await bot.reply_to(message, "Drawing...")
    try:
        await gemini.gemini_draw(bot, message, m)
    finally:
        await bot.delete_message(chat_id=message.chat.id, message_id=drawing_msg.message_id)

async def handle_assistant_callback(call: types.CallbackQuery, bot: TeleBot) -> None:
    """
    هندلر کلیک روی دکمه‌های دستیار
    """
    assistant_prompts = {
        "assistant_programmer": """
👨‍💻 من یک برنامه‌نویس حرفه‌ای هستم و می‌تونم در موارد زیر کمکتون کنم:

• نوشتن و دیباگ کردن کد
• طراحی معماری نرم‌افزار
• بهینه‌سازی کد
• آموزش برنامه‌نویسی
• حل مشکلات فنی

برای شروع، سوال برنامه‌نویسی خودتون رو بپرسید.
""",
        "assistant_designer": """
🎨 من یک گرافیست و طراح هستم و می‌تونم در موارد زیر کمکتون کنم:

• طراحی لوگو و برندینگ
• طراحی رابط کاربری
• طراحی گرافیکی
• ویرایش تصاویر
• ایده‌پردازی بصری

برای شروع، پروژه طراحی خودتون رو توضیح بدید.
""",
        "assistant_writer": """
📝 من یک نویسنده و محتوا‌ساز هستم و می‌تونم در موارد زیر کمکتون کنم:

• نوشتن مقاله و محتوا
• ویرایش و بازنویسی متن
• ایده‌پردازی برای محتوا
• نگارش متون تبلیغاتی
• ترجمه و بومی‌سازی

برای شروع، موضوع نوشتن خودتون رو مطرح کنید.
""",
        "assistant_teacher": """
🎓 من یک معلم و مربی هستم و می‌تونم در موارد زیر کمکتون کنم:

• آموزش مفاهیم درسی
• حل مسائل ریاضی و فیزیک
• آموزش زبان انگلیسی
• مشاوره تحصیلی
• تدریس خصوصی

برای شروع، سوال درسی خودتون رو بپرسید.
"""
    }
    
    if call.data in assistant_prompts:
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            call.message.chat.id,
            escape(assistant_prompts[call.data]),
            parse_mode="MarkdownV2"
        )

async def handle_content_text(message: Message, bot: TeleBot) -> None:
    user_id = message.from_user.id
    if user_id not in user_content_state:
        return  # اگر کاربر دسته‌ای انتخاب نکرده باشد، کاری انجام نمی‌شود
    content_type = user_content_state[user_id]
    prompt = message.text.strip()
    # پیام راهنما بر اساس دسته انتخابی
    content_prompts = {
        "content_article": f"یک مقاله یا پست وبلاگ با موضوع زیر بنویس:\n{prompt}",
        "content_caption": f"یک کپشن جذاب برای شبکه اجتماعی با موضوع زیر بنویس:\n{prompt}",
        "content_idea": f"برای موضوع زیر چند ایده یا عنوان خلاقانه پیشنهاد بده:\n{prompt}",
        "content_email": f"یک ایمیل یا پیام اداری مناسب با موضوع زیر بنویس:\n{prompt}",
        "content_story": f"یک داستان کوتاه یا متن خلاقانه با موضوع زیر بنویس:\n{prompt}",
        "content_translate": f"این متن را ترجمه کن: {prompt}",
        "content_edit": f"این متن را ویرایش و اصلاح کن:\n{prompt}",
        "content_resume": f"بر اساس اطلاعات زیر یک رزومه یا نامه اداری بنویس:\n{prompt}",
        "content_shop": f"یک متن مناسب برای معرفی محصول یا سایت با موضوع زیر بنویس:\n{prompt}",
        "content_ad": f"یک متن تبلیغاتی یا کمپین با موضوع زیر بنویس:\n{prompt}"
    }
    if content_type in content_prompts:
        await bot.send_message(message.chat.id, "⏳ در حال تولید محتوا ...")
        # ارسال پرامپت به مدل (مثلاً مدل Gemini)
        if str(user_id) not in default_model_dict:
            default_model_dict[str(user_id)] = True
            await gemini.gemini_stream(bot, message, content_prompts[content_type], model_1)
        else:
            if default_model_dict[str(user_id)]:
                await gemini.gemini_stream(bot, message, content_prompts[content_type], model_1)
            else:
                await gemini.gemini_stream(bot, message, content_prompts[content_type], model_2)
        # پاک کردن state پس از تولید محتوا
        del user_content_state[user_id]

# ثبت state هنگام انتخاب دسته‌بندی
async def handle_content_callback(call: types.CallbackQuery, bot: TeleBot) -> None:
    content_guides = {
        "content_article": "📝 موضوع مقاله یا پست وبلاگ خود را وارد کنید:",
        "content_caption": "📱 موضوع یا محصول مورد نظر برای کپشن شبکه اجتماعی را وارد کنید:",
        "content_idea": "💡 موضوع یا زمینه‌ای که نیاز به ایده یا عنوان دارید را بنویسید:",
        "content_email": "📧 موضوع یا متن مورد نیاز برای ایمیل یا پیام اداری را وارد کنید:",
        "content_story": "📖 موضوع یا ژانر داستان/متن خلاقانه را وارد کنید:",
        "content_translate": "🌐 متن مورد نظر برای ترجمه و زبان مقصد را وارد کنید (مثال: ترجمه به انگلیسی):",
        "content_edit": "📝 متن مورد نظر برای ویرایش و اصلاح را ارسال کنید:",
        "content_resume": "📄 اطلاعات یا سوابق خود را برای ساخت رزومه یا نامه اداری وارد کنید:",
        "content_shop": "🛒 توضیحات محصول یا متن مورد نیاز برای سایت/فروشگاه را وارد کنید:",
        "content_ad": "📢 موضوع یا هدف تبلیغاتی/کمپین را وارد کنید:"
    }
    user_id = call.from_user.id
    if call.data == "show_content_menu":
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            call.message.chat.id,
            "لطفاً نوع محتوای متنی مورد نیاز خود را انتخاب کنید:",
            reply_markup=get_content_menu_markup()
        )
    elif call.data in content_guides:
        # اگر state قبلی وجود داشت، پیام قبلی را حذف کن
        if user_id in user_content_state and hasattr(user_content_state[user_id], 'last_message_id'):
            try:
                await bot.delete_message(call.message.chat.id, user_content_state[user_id].last_message_id)
            except Exception:
                pass
        user_content_state[user_id] = call.data
        sent = await bot.send_message(
            call.message.chat.id,
            content_guides[call.data]
        )
        # ذخیره آیدی پیام راهنما برای حذف بعدی
        class StateObj(str):
            pass
        state_obj = StateObj(call.data)
        state_obj.last_message_id = sent.message_id
        user_content_state[user_id] = state_obj
        await bot.answer_callback_query(call.id)
    elif call.data == "back_main_menu":
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            call.message.chat.id,
            "به منوی اصلی بازگشتید.",
            reply_markup=get_support_markup()
        )
