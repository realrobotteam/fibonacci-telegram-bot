from functools import wraps
from telebot import TeleBot
from telebot.types import Message, ChatMemberStatus
from config import conf

def check_channel_subscription():
    def decorator(func):
        @wraps(func)
        async def wrapper(message: Message, bot: TeleBot, *args, **kwargs):
            try:
                # چک کردن عضویت کاربر در کانال
                member = await bot.get_chat_member(conf["required_channel"], message.from_user.id)
                
                # لیست وضعیت‌های مجاز برای استفاده از ربات
                allowed_statuses = [
                    ChatMemberStatus.MEMBER,
                    ChatMemberStatus.ADMINISTRATOR,
                    ChatMemberStatus.CREATOR
                ]
                
                # اگر کاربر عضو نباشد یا از کانال خارج شده باشد
                if member.status not in allowed_statuses:
                    channel_link = conf["required_channel"]
                    await bot.reply_to(
                        message,
                        conf["not_subscribed_message"].format(channel_link=channel_link),
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )
                    return None
                
                # اگر کاربر عضو باشد، اجازه استفاده از دستور را دارد
                return await func(message, bot, *args, **kwargs)
                
            except Exception as e:
                print(f"Error checking channel subscription: {e}")
                # در صورت خطای تلگرام، پیام خطای عضویت را نمایش می‌دهیم
                channel_link = conf["required_channel"]
                await bot.reply_to(
                    message,
                    conf["not_subscribed_message"].format(channel_link=channel_link),
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                return None
                
        return wrapper
    return decorator 