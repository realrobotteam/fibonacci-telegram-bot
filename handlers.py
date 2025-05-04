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
        InlineKeyboardButton("🤖 دستیارهای هوشمند", callback_data="show_assistants")
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
        await bot.reply_to(message, "🚫 شما در هر دقیقه فقط مجاز به ارسال ۴ پیام هستید.\nبرای استفاده نامحدود، اشتراک تهیه کنید.")
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

async def start(message: Message, bot: TeleBot) -> None:
    if not await check_rate_limit(message, bot):
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
    if str(message.from_user.id) not in default_model_dict:
        default_model_dict[str(message.from_user.id)] = True
        await gemini.gemini_stream(bot,message,m,model_1)
    else:
        if default_model_dict[str(message.from_user.id)]:
            await gemini.gemini_stream(bot,message,m,model_1)
        else:
            await gemini.gemini_stream(bot,message,m,model_2)

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
