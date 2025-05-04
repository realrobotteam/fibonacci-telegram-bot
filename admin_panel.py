from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
from datetime import datetime

# لیست ادمین‌ها
ADMIN_IDS = [1066860490]  # شناسه عددی ادمین‌ها را اینجا قرار دهید

# مسیر فایل‌های ذخیره‌سازی
STATS_FILE = "stats.json"
USERS_FILE = "users.json"

def is_admin(user_id: int) -> bool:
    """بررسی ادمین بودن کاربر"""
    return user_id in ADMIN_IDS

def load_stats() -> dict:
    """بارگذاری آمار از فایل"""
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "total_users": 0,
        "active_users": 0,
        "total_messages": 0,
        "start_date": datetime.now().strftime("%Y-%m-%d")
    }

def save_stats(stats: dict):
    """ذخیره آمار در فایل"""
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=4)

def load_users() -> dict:
    """بارگذاری لیست کاربران از فایل"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users: dict):
    """ذخیره لیست کاربران در فایل"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def get_admin_markup() -> InlineKeyboardMarkup:
    """ایجاد دکمه‌های پنل ادمین"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 آمار کلی", callback_data="admin_stats"),
        InlineKeyboardButton("👥 لیست کاربران", callback_data="admin_users")
    )
    markup.add(
        InlineKeyboardButton("📨 ارسال پیام به همه", callback_data="admin_broadcast"),
        InlineKeyboardButton("🔍 جستجوی کاربر", callback_data="admin_search")
    )
    return markup

async def admin_panel(message: Message, bot: TeleBot) -> None:
    """نمایش پنل ادمین"""
    if not is_admin(message.from_user.id):
        await bot.reply_to(message, "⚠️ شما دسترسی به پنل ادمین ندارید!")
        return

    welcome_text = """
🔰 پنل مدیریت ربات

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:

📊 آمار کلی: مشاهده آمار کلی ربات
👥 لیست کاربران: مشاهده لیست کاربران
📨 ارسال پیام به همه: ارسال پیام به تمام کاربران
🔍 جستجوی کاربر: جستجو در بین کاربران
"""
    await bot.reply_to(message, welcome_text, reply_markup=get_admin_markup())

async def handle_admin_callback(call, bot: TeleBot) -> None:
    """پردازش کلیک روی دکمه‌های پنل ادمین"""
    if not is_admin(call.from_user.id):
        await bot.answer_callback_query(call.id, "⚠️ شما دسترسی به پنل ادمین ندارید!")
        return

    if call.data == "admin_stats":
        stats = load_stats()
        stats_text = f"""
📊 آمار کلی ربات:

👥 تعداد کل کاربران: {stats['total_users']}
✅ کاربران فعال: {stats['active_users']}
💬 تعداد کل پیام‌ها: {stats['total_messages']}
📅 تاریخ شروع: {stats['start_date']}
"""
        await bot.edit_message_text(
            stats_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_admin_markup()
        )

    elif call.data == "admin_users":
        users = load_users()
        users_text = f"""
👥 لیست کاربران:

تعداد کل: {len(users)}
"""
        for user_id, user_data in list(users.items())[:10]:  # نمایش 10 کاربر اول
            users_text += f"\n👤 {user_data.get('username', 'بدون نام کاربری')} (ID: {user_id})"
        
        if len(users) > 10:
            users_text += f"\n\n... و {len(users) - 10} کاربر دیگر"

        await bot.edit_message_text(
            users_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_admin_markup()
        )

    elif call.data == "admin_broadcast":
        await bot.edit_message_text(
            "📨 لطفاً پیام خود را برای ارسال به همه کاربران ارسال کنید:",
            call.message.chat.id,
            call.message.message_id
        )
        # ذخیره وضعیت برای دریافت پیام بعدی
        # این بخش نیاز به پیاده‌سازی state management دارد

    elif call.data == "admin_search":
        await bot.edit_message_text(
            "🔍 لطفاً نام کاربری یا شناسه کاربر را وارد کنید:",
            call.message.chat.id,
            call.message.message_id
        )
        # ذخیره وضعیت برای دریافت پیام بعدی
        # این بخش نیاز به پیاده‌سازی state management دارد

async def broadcast_message(message: Message, bot: TeleBot) -> None:
    """ارسال پیام به همه کاربران"""
    if not is_admin(message.from_user.id):
        return

    users = load_users()
    success = 0
    failed = 0

    await bot.reply_to(message, "🔄 در حال ارسال پیام به کاربران...")

    for user_id in users:
        try:
            await bot.send_message(user_id, message.text)
            success += 1
        except Exception as e:
            print(f"Error sending message to {user_id}: {e}")
            failed += 1

    await bot.reply_to(
        message,
        f"""
✅ ارسال پیام به اتمام رسید:

✅ موفق: {success}
❌ ناموفق: {failed}
"""
    ) 
