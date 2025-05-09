from telebot import TeleBot, types
from telebot.types import Message, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from md2tgmd import escape
import traceback
from config import conf
import gemini
from channel_checker import check_membership, get_join_channel_markup, CHANNEL_ID
import time
from points_system import PointsSystem
import sqlite3
from datetime import datetime

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
points_system = PointsSystem()

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
        InlineKeyboardButton("📝 تولید محتوای متنی", callback_data="show_content_menu")
    )
    markup.add(
        InlineKeyboardButton("🛠 ابزارهای متنی ویژه", callback_data="show_special_tools"),
        InlineKeyboardButton("💎 امتیازات من", callback_data="show_points")
    )
    markup.add(
        InlineKeyboardButton("🎯 دعوت از دوستان +50 امتیاز", callback_data="show_referral")
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

async def check_points(message: Message, bot: TeleBot) -> bool:
    """
    بررسی امتیازات کاربر
    """
    user_id = message.from_user.id
    print(f"Checking points for user {user_id}")
    
    points = points_system.get_user_points(user_id)
    print(f"User {user_id} has {points} points")
    
    if points < 5:
        print(f"User {user_id} has insufficient points")
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("💎 خرید امتیاز", url="https://zarinp.al/707658"))
        markup.add(InlineKeyboardButton("🎯 دعوت از دوستان +50 امتیاز", callback_data="show_referral"))
        markup.add(InlineKeyboardButton("🔥 پاداش ویژه 1000 امتیازی 🔥", callback_data="show_referral"))
        
        await bot.reply_to(
            message,
            "⚠️ امتیازات شما کافی نیست!\n"
            "برای استفاده از ربات باید حداقل 5 امتیاز داشته باشید.\n"
            "امتیازات شما هر 24 ساعت یکبار به 100 ریست می‌شوند.\n"
            "با دعوت دوستان می‌توانید 50 امتیاز برای هر دعوت دریافت کنید!\n"
            "🔥 سیستم پاداش پلکانی: تا 1000 امتیاز برای هر دعوت! 🔥",
            reply_markup=markup
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
    """
    هندلر دستور /start
    """
    user_id = message.from_user.id
    
    # بررسی و ریست امتیازات روزانه
    points_system._check_daily_reset(user_id)
    
    # بررسی کد رفرال
    if len(message.text.split()) > 1:
        referral_code = message.text.split()[1]
        print(f"User {user_id} entered with referral code: {referral_code}")
        
        # پیدا کردن کاربر دعوت‌کننده با کد رفرال
        conn = sqlite3.connect(points_system.db_path)
        c = conn.cursor()
        c.execute('SELECT user_id FROM users WHERE referral_code = ?', (referral_code,))
        result = c.fetchone()
        conn.close()
        
        if result and result[0] != user_id:
            referrer_id = result[0]
            print(f"Found referrer: {referrer_id} for user {user_id}")
            
            # پاداش دریافت شده (ممکن است به دلیل سیستم پاداش پلکانی متفاوت باشد)
            awarded_points = points_system.add_referral_points(referrer_id, user_id)
            
            if awarded_points:
                if isinstance(awarded_points, bool):  # اگر نوع برگشتی boolean باشد
                    awarded_points = 50  # مقدار پیش‌فرض
                
                # اطلاع‌رسانی به کاربر دعوت شده
                welcome_msg = f"🎉 به ربات هوش مصنوعی فیبوناچی خوش آمدید!\n\n"
                welcome_msg += f"شما با کد دعوت وارد شده‌اید و {awarded_points} امتیاز به دعوت‌کننده اضافه شد!\n\n"
                welcome_msg += "شما نیز می‌توانید با دعوت دوستان خود، امتیاز رایگان کسب کنید."
                
                await bot.send_message(
                    message.chat.id,
                    welcome_msg
                )
                
                # اطلاع‌رسانی به کاربر دعوت‌کننده
                try:
                    notif_msg = f"🎉 کاربر جدیدی با کد دعوت شما وارد ربات شد!\n\n"
                    notif_msg += f"✅ {awarded_points} امتیاز به حساب شما اضافه شد.\n"
                    notif_msg += f"💰 می‌توانید با دعوت بیشتر دوستان، امتیاز بیشتری کسب کنید."
                    
                    await bot.send_message(
                        referrer_id,
                        notif_msg
                    )
                except Exception as e:
                    print(f"Error sending notification to referrer {referrer_id}: {str(e)}")
            else:
                print(f"Failed to add referral points for referrer {referrer_id} and user {user_id}")
        else:
            if not result:
                print(f"No user found with referral code: {referral_code}")
            else:
                print(f"User {user_id} tried to use their own referral code")
    
    if not await check_user_membership(message, bot):
        return
    
    text = escape(f"""
👋 سلام {message.from_user.first_name} عزیز!

🤖 به ربات هوش مصنوعی فیبوناچی خوش آمدید!

📝 شما می‌تونید:
• سوالات خود رو بپرسید
• متن‌ها رو ویرایش کنید
• تصاویر رو تحلیل کنید
• و خیلی کارهای دیگه...

💎 امتیاز فعلی شما: {points_system.get_user_points(user_id)}
هر 24 ساعت، امتیاز شما به 100 ریست می‌شود!

برای شروع، یکی از گزینه‌های زیر رو انتخاب کنید:
""")
    
    await bot.reply_to(
        message,
        text,
        reply_markup=get_support_markup()
    )

async def gemini_stream_handler(message: Message, bot: TeleBot) -> None:
    """
    پردازش پیام‌های متنی و ارسال به Gemini
    """
    if not await check_user_membership(message, bot):
        return
        
    if not await check_rate_limit(message, bot):
        return
        
    if not await check_points(message, bot):
        return
        
    user_id = message.from_user.id
    print(f"Processing message from user {user_id}")
    
    # کسر امتیاز
    if points_system.deduct_points(user_id):
        print(f"Successfully deducted points from user {user_id}")
    else:
        print(f"Failed to deduct points from user {user_id}")
        await bot.reply_to(message, "⚠️ خطا در کسر امتیاز. لطفاً دوباره تلاش کنید.")
        return
    
    # نمایش وضعیت تایپینگ
    await bot.send_chat_action(message.chat.id, "typing")
    
    try:
        # ارسال پیام به Gemini و دریافت پاسخ
        response = await gemini.gemini_stream(bot, message, message.text, model_1)
        
    except Exception as e:
        print(f"Error in gemini_stream_handler: {str(e)}")
        await bot.reply_to(message, "⚠️ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.")

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
    if not await check_points(message, bot):
        return
        
    user_id = message.from_user.id
    print(f"PRIVATE HANDLER - Processing message from user {user_id}")
    
    # کسر امتیاز
    if points_system.deduct_points(user_id):
        print(f"PRIVATE HANDLER - Successfully deducted points from user {user_id}")
    else:
        print(f"PRIVATE HANDLER - Failed to deduct points from user {user_id}")
        await bot.reply_to(message, "⚠️ خطا در کسر امتیاز. لطفاً دوباره تلاش کنید.")
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
    if not await check_points(message, bot):
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
    if not await check_points(message, bot):
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
    if not await check_points(message, bot):
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

# تابع حذف پیام راهنمای قبلی برای هر کاربر
async def delete_last_guide_message(user_id, chat_id, bot):
    if user_id in user_content_state and user_content_state[user_id].get('last_message_id'):
        try:
            await bot.delete_message(chat_id, user_content_state[user_id]['last_message_id'])
        except Exception:
            pass
        # پاک کردن state قبلی
        del user_content_state[user_id]

async def handle_assistant_callback(call: types.CallbackQuery, bot: TeleBot) -> None:
    await delete_last_guide_message(call.from_user.id, call.message.chat.id, bot)
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
""",
        "assistant_translator": """
🌐 من یک مترجم و مدرس زبان هستم:
• ترجمه متون به زبان‌های مختلف
• رفع اشکال گرامری
• آموزش زبان
برای شروع، متن یا سوال زبانی خود را ارسال کنید.
""",
        "assistant_job": """
💼 من مشاور شغلی و رزومه‌نویس هستم:
• ساخت رزومه و نامه اداری
• مشاوره شغلی و مصاحبه
• راهنمایی مسیر شغلی
برای شروع، سوال یا اطلاعات شغلی خود را ارسال کنید.
""",
        "assistant_marketing": """
📢 من دستیار بازاریابی و تبلیغات هستم:
• تولید متن تبلیغاتی و کمپین
• ایده‌پردازی برای برندینگ
• مشاوره مارکتینگ
برای شروع، هدف یا موضوع تبلیغاتی خود را بنویسید.
""",
        "assistant_legal": """
📄 من دستیار حقوقی هستم:
• راهنمایی در نگارش قرارداد
• پاسخ به سوالات حقوقی ساده
برای شروع، سوال یا موضوع حقوقی خود را ارسال کنید.
""",
        "assistant_psychology": """
💬 من دستیار روانشناسی و انگیزشی هستم:
• ارائه جملات انگیزشی
• راهنمایی مدیریت استرس
• مشاوره انگیزشی
برای شروع، موضوع یا سوال خود را ارسال کنید.
""",
        "assistant_travel": """
✈️ من دستیار سفر و گردشگری هستم:
• پیشنهاد مقصد سفر
• برنامه‌ریزی سفر
• راهنمایی گردشگری
برای شروع، مقصد یا سوال سفر خود را بنویسید.
""",
        "assistant_finance": """
💰 من دستیار مالی و حسابداری هستم:
• راهنمایی مدیریت مالی شخصی
• پاسخ به سوالات حسابداری
برای شروع، سوال مالی یا حسابداری خود را ارسال کنید.
""",
        "assistant_health": """
🍏 من دستیار سلامت و تغذیه هستم:
• ارائه نکات تغذیه‌ای و ورزشی
• پاسخ به سوالات سلامت عمومی
برای شروع، سوال یا موضوع سلامت خود را ارسال کنید.
""",
        "assistant_poetry": """
📚 من دستیار شعر و ادبیات هستم:
• سرودن شعر و متن ادبی
• تحلیل و بازنویسی متون ادبی
برای شروع، موضوع یا متن ادبی خود را ارسال کنید.
""",
        "assistant_kids": """
🧸 من دستیار کودک و سرگرمی هستم:
• قصه‌گویی
• معما و بازی فکری
برای شروع، سن کودک و علاقه‌مندی را بنویسید.
""",
        "assistant_news": """
📰 من دستیار اخبار و اطلاعات روز هستم:
• ارائه اخبار و اطلاعات به‌روز (در صورت فعال بودن)
برای شروع، موضوع یا حوزه خبری مورد نظر را بنویسید.
"""
    }
    if call.data in assistant_prompts:
        await bot.answer_callback_query(call.id)
        sent = await bot.send_message(
            call.message.chat.id,
            escape(assistant_prompts[call.data]),
            parse_mode="MarkdownV2"
        )
        user_content_state[call.from_user.id] = {'type': call.data, 'last_message_id': sent.message_id}

async def handle_content_text(message: Message, bot: TeleBot) -> None:
    user_id = message.from_user.id
    if user_id not in user_content_state:
        return  # اگر کاربر دسته‌ای انتخاب نکرده باشد، کاری انجام نمی‌شود
        
    if not await check_points(message, bot):
        return
        
    content_type = user_content_state[user_id]['type']
    prompt = message.text.strip()
    # پیام راهنما بر اساس دسته انتخابی (همه ابزارها و تولید محتوا و دستیارها)
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
        "content_ad": f"یک متن تبلیغاتی یا کمپین با موضوع زیر بنویس:\n{prompt}",
        "tool_speech2text": f"لطفاً این ویس را به متن تبدیل کن (در حال حاضر فقط متن را بنویسید)",
        "tool_congrats": f"🎉 مناسبت (تولد، عید، سالگرد و ...) و نام شخص را وارد کنید:",
        "tool_funny": f"😂 موضوع یا متن جدی را وارد کنید تا به طنز تبدیل شود:",
        "tool_dialogue": f"🎬 موضوع یا ژانر دیالوگ/سناریو را وارد کنید:",
        "tool_podcast": f"🎙 موضوع پادکست یا ویدیو را وارد کنید:",
        "tool_motivation": f"💪 اگر پیام انگیزشی خاصی مدنظر داری بنویس، یا فقط بنویس 'انگیزشی':",
        "tool_puzzle": f"🧩 موضوع یا سن کاربر را بنویس تا معما یا بازی فکری مناسب دریافت کنی:",
        "tool_bio": f"👤 اطلاعات یا علاقه‌مندی خود را برای تولید بیو بنویس:",
        "tool_invite": f"💌 نوع مراسم (تولد، عروسی، همایش و ...) و اطلاعات لازم را وارد کن:",
        "tool_farewell": f"💔 موضوع خداحافظی یا دل‌نوشته را وارد کن:",
        "tool_slogan": f"🚀 موضوع یا برند مورد نظر برای شعار تبلیغاتی را وارد کن:",
        "tool_challenge": f"🏆 موضوع چالش یا مسابقه را وارد کن:",
        "tool_appintro": f"📱 نام و ویژگی‌های اپلیکیشن یا استارتاپ را وارد کن:",
        "tool_support": f"🤝 موضوع یا سوال پشتیبانی مشتری را وارد کن:",
        "tool_guide": f"📖 نام محصول یا موضوع آموزشی را وارد کن تا راهنما تولید شود:"
    }
    # اگر کلید وجود داشت، پرامپت را ارسال کن
    if content_type in content_prompts:
        await bot.send_message(message.chat.id, "⏳ در حال تولید محتوا ...", reply_markup=get_support_markup())
        if str(user_id) not in default_model_dict:
            default_model_dict[str(user_id)] = True
            await gemini.gemini_stream(bot, message, content_prompts[content_type], model_1, reply_markup=get_support_markup())
        else:
            if default_model_dict[str(user_id)]:
                await gemini.gemini_stream(bot, message, content_prompts[content_type], model_1, reply_markup=get_support_markup())
            else:
                await gemini.gemini_stream(bot, message, content_prompts[content_type], model_2, reply_markup=get_support_markup())
        
        # کسر امتیاز بعد از ارسال پیام
        points_system.deduct_points(user_id)
        
        del user_content_state[user_id]
    else:
        # اگر کلید پیدا نشد، state را پاک کن تا کاربر سردرگم نشود
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
        await delete_last_guide_message(user_id, call.message.chat.id, bot)
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            call.message.chat.id,
            "لطفاً نوع محتوای متنی مورد نیاز خود را انتخاب کنید:",
            reply_markup=get_content_menu_markup()
        )
    elif call.data in content_guides:
        await delete_last_guide_message(user_id, call.message.chat.id, bot)
        sent = await bot.send_message(
            call.message.chat.id,
            content_guides[call.data]
        )
        user_content_state[user_id] = {'type': call.data, 'last_message_id': sent.message_id}
        await bot.answer_callback_query(call.id)
    elif call.data == "back_main_menu":
        await delete_last_guide_message(user_id, call.message.chat.id, bot)
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            call.message.chat.id,
            "به منوی اصلی بازگشتید.",
            reply_markup=get_support_markup()
        )

async def handle_special_tools_callback(call: types.CallbackQuery, bot: TeleBot) -> None:
    special_guides = {
        "tool_speech2text": "🎤 ویس خود را ارسال کنید تا به متن تبدیل شود (در حال حاضر فقط متن را بنویسید)",
        "tool_congrats": "🎉 مناسبت (تولد، عید، سالگرد و ...) و نام شخص را وارد کنید:",
        "tool_funny": "😂 موضوع یا متن جدی را وارد کنید تا به طنز تبدیل شود:",
        "tool_dialogue": "🎬 موضوع یا ژانر دیالوگ/سناریو را وارد کنید:",
        "tool_podcast": "🎙 موضوع پادکست یا ویدیو را وارد کنید:",
        "tool_motivation": "💪 اگر پیام انگیزشی خاصی مدنظر داری بنویس، یا فقط بنویس 'انگیزشی':",
        "tool_puzzle": "🧩 موضوع یا سن کاربر را بنویس تا معما یا بازی فکری مناسب دریافت کنی:",
        "tool_bio": "👤 اطلاعات یا علاقه‌مندی خود را برای تولید بیو بنویس:",
        "tool_invite": "💌 نوع مراسم (تولد، عروسی، همایش و ...) و اطلاعات لازم را وارد کن:",
        "tool_farewell": "💔 موضوع خداحافظی یا دل‌نوشته را وارد کن:",
        "tool_slogan": "🚀 موضوع یا برند مورد نظر برای شعار تبلیغاتی را وارد کن:",
        "tool_challenge": "🏆 موضوع چالش یا مسابقه را وارد کن:",
        "tool_appintro": "📱 نام و ویژگی‌های اپلیکیشن یا استارتاپ را وارد کن:",
        "tool_support": "🤝 موضوع یا سوال پشتیبانی مشتری را وارد کن:",
        "tool_guide": "📖 نام محصول یا موضوع آموزشی را وارد کن تا راهنما تولید شود:"
    }
    user_id = call.from_user.id
    if call.data == "show_special_tools":
        await delete_last_guide_message(user_id, call.message.chat.id, bot)
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            call.message.chat.id,
            "لطفاً یکی از ابزارهای متنی ویژه را انتخاب کنید:",
            reply_markup=get_special_tools_markup()
        )
    elif call.data in special_guides:
        await delete_last_guide_message(user_id, call.message.chat.id, bot)
        sent = await bot.send_message(
            call.message.chat.id,
            special_guides[call.data]
        )
        user_content_state[user_id] = {'type': call.data, 'last_message_id': sent.message_id}
        await bot.answer_callback_query(call.id)
    elif call.data == "back_main_menu":
        await delete_last_guide_message(user_id, call.message.chat.id, bot)
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            call.message.chat.id,
            "به منوی اصلی بازگشتید.",
            reply_markup=get_support_markup()
        )

async def handle_callback(call: types.CallbackQuery, bot: TeleBot) -> None:
    """
    هندلر کلیک روی دکمه‌ها
    """
    print(f"CALLBACK HANDLER - Handling callback with data: {call.data}")
    
    if call.data == "show_points":
        await bot.answer_callback_query(call.id)
        
        # به جای ساخت شیء Message، مستقیماً با SQLite کار می‌کنیم
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        # بررسی امتیاز
        conn = sqlite3.connect(points_system.db_path)
        c = conn.cursor()
        
        # بررسی و ریست امتیازات روزانه
        points_system._check_daily_reset(user_id)
        
        c.execute('SELECT points FROM users WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        
        if result:
            points = result[0]
        else:
            points = 100
            # ایجاد کاربر جدید
            c.execute('INSERT INTO users (user_id, points, last_reset_date) VALUES (?, 100, ?)',
                    (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            
        conn.close()
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🎯 دعوت از دوستان +50 امتیاز", callback_data="show_referral"))
        markup.add(InlineKeyboardButton("🔥 پاداش ویژه 1000 امتیازی 🔥", callback_data="show_referral"))
        markup.add(InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_main_menu"))
        
        text = f"💎 امتیاز فعلی شما: {points}\n\n"
        text += "با هر پیام ۵ امتیاز کسر می‌شود.\n"
        text += "امتیازات شما هر 24 ساعت یکبار به ۱۰۰ ریست می‌شوند.\n"
        text += "کافیست هر روز یکبار از ربات بازدید کنید تا امتیاز روزانه خود را دریافت کنید.\n"
        text += "با دعوت دوستان می‌توانید امتیاز بیشتری کسب کنید!"
        
        await bot.send_message(
            chat_id,
            text,
            reply_markup=markup
        )
        
    elif call.data == "show_referral":
        await bot.answer_callback_query(call.id)
        
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        print(f"User {user_id} requested their referral code")
        # بررسی و ریست امتیازات روزانه
        points_system._check_daily_reset(user_id)
        
        try:
            # دریافت آمار دعوت‌های کاربر
            stats = points_system.get_user_referral_stats(user_id)
            referral_code = points_system.get_referral_code(user_id)
            
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(InlineKeyboardButton("📊 رتبه‌بندی دعوت‌کنندگان برتر", callback_data="show_top_referrers"))
            markup.add(InlineKeyboardButton("🔄 لیست دعوت‌های اخیر من", callback_data="show_my_referrals"))
            markup.add(InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_main_menu"))
            
            # ساخت لینک دعوت
            bot_username = (await bot.get_me()).username
            invite_link = f"https://t.me/{bot_username}?start={referral_code}"
            
            text = "🎯 لینک دعوت شما:\n\n"
            text += f"`{invite_link}`\n\n"
            
            # نمایش آمار دعوت
            text += f"📊 تعداد کل دعوت‌های موفق شما: {stats['total']}\n"
            text += f"💰 امتیاز کسب شده از دعوت‌ها: {stats['estimated_points']}\n\n"
            
            # توضیح سیستم پاداش پلکانی
            text += "💎 سیستم پاداش پلکانی:\n"
            text += "• هر دعوت: 50 امتیاز پایه\n"
            text += "• بیش از 5 دعوت: 80 امتیاز (30 امتیاز بونوس)\n"
            text += "• بیش از 10 دعوت: 120 امتیاز (70 امتیاز بونوس)\n"
            text += "• بیش از 15 دعوت: 150 امتیاز (100 امتیاز بونوس)\n"
            text += "• بیش از 20 دعوت: 200 امتیاز (150 امتیاز بونوس)\n"
            text += "• بیش از 30 دعوت: 300 امتیاز (250 امتیاز بونوس)\n"
            text += "• بیش از 40 دعوت: 400 امتیاز (350 امتیاز بونوس)\n"
            text += "• بیش از 50 دعوت: 500 امتیاز (450 امتیاز بونوس)\n"
            text += "• بیش از 60 دعوت: 600 امتیاز (550 امتیاز بونوس)\n"
            text += "• بیش از 80 دعوت: 800 امتیاز (750 امتیاز بونوس)\n"
            text += "• بیش از 100 دعوت: 1000 امتیاز (950 امتیاز بونوس) 🔥\n\n"
            
            text += "برای دعوت دوستان، لینک بالا را به آنها بدهید."
            
            await bot.send_message(
                chat_id,
                text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Error in show_referral for user {user_id}: {str(e)}")
            await bot.send_message(
                chat_id,
                "⚠️ خطایی در تولید کد دعوت رخ داد. لطفاً دوباره تلاش کنید.",
                reply_markup=get_support_markup()
            )
    elif call.data == "back_main_menu":
        await delete_last_guide_message(call.from_user.id, call.message.chat.id, bot)
        await bot.answer_callback_query(call.id)
        
        # بررسی و ریست امتیازات روزانه هنگام بازگشت به منوی اصلی
        points_system._check_daily_reset(call.from_user.id)
        
        await bot.send_message(
            call.message.chat.id,
            "به منوی اصلی بازگشتید.",
            reply_markup=get_support_markup()
        )
    elif call.data == "show_content_menu":
        await handle_content_callback(call, bot)
    elif call.data == "show_special_tools":
        await handle_special_tools_callback(call, bot)
    elif call.data == "show_assistants":
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            call.message.chat.id,
            "🤖 لطفاً یکی از دستیارهای هوشمند را انتخاب کنید:",
            reply_markup=get_assistants_markup()
        )
    elif call.data == "show_top_referrers":
        await bot.answer_callback_query(call.id)
        
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        try:
            # دریافت لیست کاربران برتر
            top_referrers = points_system.get_top_referrers(10)
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 بازگشت به منوی دعوت", callback_data="show_referral"))
            
            text = "🏆 رتبه‌بندی کاربران برتر از نظر دعوت دوستان:\n\n"
            
            if not top_referrers:
                text += "هنوز هیچ کاربری دعوت موفقی نداشته است!\n"
                text += "اولین نفری باشید که دوستان خود را دعوت می‌کند و در صدر این جدول قرار می‌گیرید!"
            else:
                for i, (referrer_id, count) in enumerate(top_referrers):
                    # ستاره برای کاربر فعلی
                    star = "⭐️ " if referrer_id == user_id else ""
                    # مشخص کردن رتبه اول تا سوم با مدال
                    medal = ""
                    if i == 0:
                        medal = "🥇 "
                    elif i == 1:
                        medal = "🥈 "
                    elif i == 2:
                        medal = "🥉 "
                    else:
                        medal = f"{i+1}. "
                    
                    text += f"{medal}{star}کاربر {referrer_id}: {count} دعوت موفق\n"
            
            await bot.send_message(
                chat_id,
                text,
                reply_markup=markup
            )
        
        except Exception as e:
            print(f"Error in show_top_referrers for user {user_id}: {str(e)}")
            await bot.send_message(
                chat_id,
                "⚠️ خطایی در نمایش رتبه‌بندی رخ داد. لطفاً دوباره تلاش کنید.",
                reply_markup=get_support_markup()
            )
            
    elif call.data == "show_my_referrals":
        await bot.answer_callback_query(call.id)
        
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        try:
            # دریافت آمار دعوت‌های کاربر
            stats = points_system.get_user_referral_stats(user_id)
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 بازگشت به منوی دعوت", callback_data="show_referral"))
            
            text = "🔄 لیست دعوت‌های اخیر شما:\n\n"
            
            if not stats['recent']:
                text += "شما هنوز هیچ دعوت موفقی نداشته‌اید!\n"
                text += "دوستان خود را دعوت کنید تا امتیاز بیشتری کسب کنید."
            else:
                for i, (referred_id, date_str) in enumerate(stats['recent']):
                    # تبدیل تاریخ به فرمت خوانا
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                        date_formatted = date_obj.strftime('%Y/%m/%d %H:%M')
                    except:
                        date_formatted = date_str
                    
                    text += f"{i+1}. کاربر {referred_id} - تاریخ: {date_formatted}\n"
            
            await bot.send_message(
                chat_id,
                text,
                reply_markup=markup
            )
        
        except Exception as e:
            print(f"Error in show_my_referrals for user {user_id}: {str(e)}")
            await bot.send_message(
                chat_id,
                "⚠️ خطایی در نمایش دعوت‌های شما رخ داد. لطفاً دوباره تلاش کنید.",
                reply_markup=get_support_markup()
            )
