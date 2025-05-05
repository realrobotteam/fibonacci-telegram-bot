import asyncio
from datetime import datetime, timedelta
import json
import os
from telebot import types
from config import conf
import google.generativeai as genai
from handlers import escape

# تنظیمات Gemini
genai.configure(api_key=conf['GOOGLE_GEMINI_KEY'])
model = genai.GenerativeModel(conf['model_1'])

# ساختار داده‌ها برای ذخیره تنظیمات کاربران
user_writer_settings = {}

# مسیر فایل ذخیره‌سازی
SETTINGS_FILE = 'writer_settings.json'

def load_settings():
    """بارگذاری تنظیمات از فایل"""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_settings():
    """ذخیره تنظیمات در فایل"""
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_writer_settings, f, ensure_ascii=False, indent=4)

def get_writer_menu_markup():
    """منوی اصلی نویسنده خودکار"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ تنظیم موضوع جدید", callback_data="writer_new_topic"),
        types.InlineKeyboardButton("📝 لیست موضوعات", callback_data="writer_list_topics"),
        types.InlineKeyboardButton("⚙️ تنظیمات ارسال", callback_data="writer_settings"),
        types.InlineKeyboardButton("❌ لغو اشتراک", callback_data="writer_unsubscribe")
    )
    return markup

async def generate_daily_content(topic, user_id):
    """تولید محتوای روزانه برای موضوع مشخص"""
    prompt = f"""لطفاً یک محتوای ترند و جذاب برای موضوع زیر تولید کن:
موضوع: {topic}

لطفاً محتوا را با این ساختار تولید کن:
1. عنوان جذاب و گیرا
2. مقدمه کوتاه و جذاب
3. محتوای اصلی (حداقل 3 بخش)
4. نتیجه‌گیری
5. هشتگ‌های مرتبط

محتوای تولید شده باید:
- به‌روز و ترند باشد
- جذاب و خواندنی باشد
- از منابع معتبر استفاده کند
- برای مخاطب عام قابل فهم باشد
"""
    
    try:
        response = await model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"خطا در تولید محتوا: {e}")
        return None

async def send_daily_content(bot):
    """ارسال محتوای روزانه به کاربران"""
    while True:
        try:
            current_time = datetime.now()
            for user_id, settings in user_writer_settings.items():
                if not settings.get('active', False):
                    continue
                
                last_sent = datetime.fromisoformat(settings.get('last_sent', '2000-01-01'))
                if current_time - last_sent >= timedelta(days=1):
                    for topic in settings.get('topics', []):
                        content = await generate_daily_content(topic, user_id)
                        if content:
                            try:
                                await bot.send_message(
                                    user_id,
                                    f"📝 محتوای روزانه برای موضوع: {topic}\n\n{escape(content)}",
                                    parse_mode='HTML'
                                )
                            except Exception as e:
                                print(f"خطا در ارسال پیام به کاربر {user_id}: {e}")
                    
                    # به‌روزرسانی زمان آخرین ارسال
                    settings['last_sent'] = current_time.isoformat()
                    save_settings()
            
            # انتظار برای چک کردن مجدد (هر ساعت)
            await asyncio.sleep(3600)
            
        except Exception as e:
            print(f"خطا در ارسال محتوای روزانه: {e}")
            await asyncio.sleep(300)  # انتظار 5 دقیقه در صورت خطا

async def handle_writer_callback(call: types.CallbackQuery, bot):
    """مدیریت callback های منوی نویسنده خودکار"""
    user_id = call.from_user.id
    
    if call.data == "writer_new_topic":
        await bot.send_message(
            call.message.chat.id,
            "لطفاً موضوع مورد نظر خود را وارد کنید:",
            reply_markup=types.ForceReply()
        )
        # ذخیره وضعیت برای دریافت موضوع
        if user_id not in user_writer_settings:
            user_writer_settings[user_id] = {'topics': [], 'active': True}
        user_writer_settings[user_id]['waiting_for_topic'] = True
        save_settings()
    
    elif call.data == "writer_list_topics":
        if user_id in user_writer_settings and user_writer_settings[user_id]['topics']:
            topics = "\n".join([f"• {topic}" for topic in user_writer_settings[user_id]['topics']])
            await bot.send_message(
                call.message.chat.id,
                f"📝 موضوعات فعال شما:\n\n{topics}",
                reply_markup=get_writer_menu_markup()
            )
        else:
            await bot.send_message(
                call.message.chat.id,
                "شما هنوز هیچ موضوعی تنظیم نکرده‌اید.",
                reply_markup=get_writer_menu_markup()
            )
    
    elif call.data == "writer_settings":
        if user_id in user_writer_settings:
            status = "فعال" if user_writer_settings[user_id]['active'] else "غیرفعال"
            await bot.send_message(
                call.message.chat.id,
                f"⚙️ تنظیمات نویسنده خودکار:\n\n"
                f"وضعیت: {status}\n"
                f"تعداد موضوعات: {len(user_writer_settings[user_id]['topics'])}\n"
                f"آخرین ارسال: {user_writer_settings[user_id].get('last_sent', 'هنوز ارسالی انجام نشده')}",
                reply_markup=get_writer_menu_markup()
            )
        else:
            await bot.send_message(
                call.message.chat.id,
                "شما هنوز تنظیماتی ندارید.",
                reply_markup=get_writer_menu_markup()
            )
    
    elif call.data == "writer_unsubscribe":
        if user_id in user_writer_settings:
            user_writer_settings[user_id]['active'] = False
            save_settings()
            await bot.send_message(
                call.message.chat.id,
                "اشتراک شما غیرفعال شد. برای فعال‌سازی مجدد، از منوی نویسنده خودکار استفاده کنید.",
                reply_markup=get_writer_menu_markup()
            )
        else:
            await bot.send_message(
                call.message.chat.id,
                "شما اشتراک فعالی ندارید.",
                reply_markup=get_writer_menu_markup()
            )

async def handle_writer_message(message: types.Message, bot):
    """مدیریت پیام‌های دریافتی برای نویسنده خودکار"""
    user_id = message.from_user.id
    
    if user_id in user_writer_settings and user_writer_settings[user_id].get('waiting_for_topic'):
        topic = message.text.strip()
        if topic:
            if user_id not in user_writer_settings:
                user_writer_settings[user_id] = {'topics': [], 'active': True}
            
            if topic not in user_writer_settings[user_id]['topics']:
                user_writer_settings[user_id]['topics'].append(topic)
                save_settings()
                await bot.send_message(
                    message.chat.id,
                    f"✅ موضوع '{topic}' با موفقیت اضافه شد.",
                    reply_markup=get_writer_menu_markup()
                )
            else:
                await bot.send_message(
                    message.chat.id,
                    "این موضوع قبلاً اضافه شده است.",
                    reply_markup=get_writer_menu_markup()
                )
        
        user_writer_settings[user_id]['waiting_for_topic'] = False
        save_settings()

# بارگذاری تنظیمات در هنگام شروع
user_writer_settings = load_settings() 