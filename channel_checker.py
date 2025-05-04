from telebot.async_telebot import AsyncTeleBot
from telebot import types

# تنظیمات کانال
CHANNEL_USERNAME = "@fibonacciai"  # نام کاربری کانال خود را اینجا قرار دهید
CHANNEL_ID = -1002081035666  # شناسه عددی کانال خود را اینجا قرار دهید

async def check_membership(bot: AsyncTeleBot, user_id: int) -> bool:
    """
    بررسی عضویت کاربر در کانال
    """
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Error checking membership: {e}")
        return False

def get_join_channel_markup() -> types.InlineKeyboardMarkup:
    """
    ایجاد دکمه عضویت در کانال و دکمه شروع چت
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"))
    markup.add(types.InlineKeyboardButton("🚀 شروع چت", "/start"))
    return markup 
