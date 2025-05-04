from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

# لیست ادمین‌ها
ADMIN_IDS = [
    -1066860490,  # شناسه عددی ادمین
    # شناسه‌های ادمین‌های دیگر را اینجا اضافه کنید
]

# مسیر فایل ذخیره‌سازی اطلاعات کاربران
USERS_DB_FILE = "users_db.json"

def is_admin(user_id: int) -> bool:
    """بررسی ادمین بودن کاربر"""
    return user_id in ADMIN_IDS

def get_admin_markup() -> InlineKeyboardMarkup:
    """ایجاد دکمه‌های پنل ادمین"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("👥 لیست کاربران", callback_data="admin_list_users"),
        InlineKeyboardButton("📊 آمار کلی", callback_data="admin_stats")
    )
    markup.add(
        InlineKeyboardButton("📨 ارسال پیام به همه", callback_data="admin_broadcast"),
        InlineKeyboardButton("🔍 جستجوی کاربر", callback_data="admin_search_user")
    )
    return markup

def save_user(user_id: int, username: str = None, first_name: str = None):
    """ذخیره اطلاعات کاربر در دیتابیس"""
    users = load_users()
    if str(user_id) not in users:
        users[str(user_id)] = {
            "username": username,
            "first_name": first_name,
            "join_date": None
        }
        save_users(users)

def load_users() -> dict:
    """بارگذاری اطلاعات کاربران از دیتابیس"""
    if os.path.exists(USERS_DB_FILE):
        with open(USERS_DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users: dict):
    """ذخیره اطلاعات کاربران در دیتابیس"""
    with open(USERS_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

async def handle_admin_command(message: Message, bot: TeleBot):
    """مدیریت دستورات ادمین"""
    if not is_admin(message.from_user.id):
        await bot.reply_to(message, "⚠️ شما دسترسی به این بخش را ندارید.")
        return

    await bot.reply_to(
        message,
        "🔐 پنل مدیریت\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_admin_markup()
    )

async def handle_admin_callback(call, bot: TeleBot):
    """مدیریت کلیک روی دکمه‌های پنل ادمین"""
    if not is_admin(call.from_user.id):
        await bot.answer_callback_query(call.id, "⚠️ شما دسترسی به این بخش را ندارید.")
        return

    if call.data == "admin_list_users":
        users = load_users()
        text = "👥 لیست کاربران:\n\n"
        for user_id, user_data in users.items():
            text += f"🆔 ID: {user_id}\n"
            if user_data.get("username"):
                text += f"👤 Username: @{user_data['username']}\n"
            if user_data.get("first_name"):
                text += f"📝 Name: {user_data['first_name']}\n"
            text += "➖➖➖➖➖➖➖➖➖➖\n"
        
        # تقسیم پیام به بخش‌های کوچکتر اگر خیلی طولانی باشد
        if len(text) > 4000:
            parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for part in parts:
                await bot.send_message(call.message.chat.id, part)
        else:
            await bot.send_message(call.message.chat.id, text)

    elif call.data == "admin_stats":
        users = load_users()
        total_users = len(users)
        text = f"""
📊 آمار کلی ربات:

👥 تعداد کل کاربران: {total_users}
"""
        await bot.send_message(call.message.chat.id, text)

    elif call.data == "admin_broadcast":
        await bot.send_message(
            call.message.chat.id,
            "📨 لطفاً پیام خود را برای ارسال به همه کاربران ارسال کنید:"
        )
        # این وضعیت را در یک متغیر ذخیره کنید تا در هندلر پیام‌های بعدی بررسی شود

    elif call.data == "admin_search_user":
        await bot.send_message(
            call.message.chat.id,
            "🔍 لطفاً شناسه یا نام کاربری کاربر مورد نظر را ارسال کنید:"
        )
        # این وضعیت را در یک متغیر ذخیره کنید تا در هندلر پیام‌های بعدی بررسی شود

async def broadcast_message(message: Message, bot: TeleBot):
    """ارسال پیام به همه کاربران"""
    if not is_admin(message.from_user.id):
        return

    users = load_users()
    sent = 0
    failed = 0
    
    await bot.reply_to(message, "🔄 در حال ارسال پیام به کاربران...")
    
    for user_id in users.keys():
        try:
            await bot.send_message(user_id, message.text)
            sent += 1
        except Exception as e:
            print(f"Error sending message to {user_id}: {e}")
            failed += 1
    
    await bot.reply_to(
        message,
        f"""
✅ ارسال پیام به اتمام رسید:

✅ ارسال موفق: {sent}
❌ ارسال ناموفق: {failed}
"""
    ) 