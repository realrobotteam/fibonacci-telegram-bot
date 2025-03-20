import argparse
import traceback
import asyncio
import re
import telebot
import os
import sys
import fcntl
from telebot.async_telebot import AsyncTeleBot
import handlers
from config import conf, generation_config, safety_settings
import gemini

# Init args
parser = argparse.ArgumentParser()
parser.add_argument("tg_token", help="telegram token")
parser.add_argument("GOOGLE_GEMINI_KEY", help="Google Gemini API key")
options = parser.parse_args()
print("Arg parse done.")

class SingleInstanceBot:
    def __init__(self, lock_file):
        self.lock_file = lock_file
        self.lock_fd = None

    def __enter__(self):
        try:
            # ایجاد یا باز کردن فایل قفل
            self.lock_fd = open(self.lock_file, 'w')
            
            # تلاش برای قفل کردن فایل
            fcntl.lockf(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            return self
        except IOError:
            if self.lock_fd:
                self.lock_fd.close()
            print("⚠️ یک نمونه دیگر از ربات در حال اجراست!")
            sys.exit(1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_fd:
            # آزاد کردن قفل و بستن فایل
            fcntl.lockf(self.lock_fd, fcntl.LOCK_UN)
            self.lock_fd.close()
            try:
                os.remove(self.lock_file)
            except OSError:
                pass

async def main():
    # مسیر فایل قفل
    lock_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.bot.lock')
    
    with SingleInstanceBot(lock_file):
        print("✅ شروع اجرای ربات...")
        
        # Init bot
        bot = AsyncTeleBot(options.tg_token)
        await bot.delete_my_commands(scope=None, language_code=None)
        await bot.set_my_commands(
            commands=[
                telebot.types.BotCommand("start", "Start"),
                telebot.types.BotCommand("gemini", "using gemini-2.0-flash-exp"),
                telebot.types.BotCommand("gemini_pro", "using gemini-1.5-pro"),
                telebot.types.BotCommand("draw", "draw picture"),
                telebot.types.BotCommand("edit", "edit photo"),
                telebot.types.BotCommand("clear", "Clear all history"),
                telebot.types.BotCommand("switch", "switch default model"),
                telebot.types.BotCommand("personality", "تنظیم شخصیت ربات"),
                telebot.types.BotCommand("reset_personality", "بازنشانی شخصیت به حالت پیش‌فرض")
            ],
        )
        print("✅ مقداردهی اولیه ربات انجام شد.")

        # Init commands
        bot.register_message_handler(handlers.start,                         commands=['start'],         pass_bot=True)
        bot.register_message_handler(handlers.gemini_stream_handler,         commands=['gemini'],        pass_bot=True)
        bot.register_message_handler(handlers.gemini_pro_stream_handler,     commands=['gemini_pro'],    pass_bot=True)
        bot.register_message_handler(handlers.draw_handler,                  commands=['draw'],          pass_bot=True)
        bot.register_message_handler(handlers.gemini_edit_handler,           commands=['edit'],          pass_bot=True)
        bot.register_message_handler(handlers.clear,                         commands=['clear'],         pass_bot=True)
        bot.register_message_handler(handlers.switch,                        commands=['switch'],        pass_bot=True)
        bot.register_message_handler(handlers.gemini_photo_handler,          content_types=["photo"],    pass_bot=True)
        bot.register_message_handler(
            handlers.gemini_private_handler,
            func=lambda message: message.chat.type == "private",
            content_types=['text'],
            pass_bot=True)
            
        # اضافه کردن دستورات مدیریت شخصیت
        bot.register_message_handler(gemini.set_personality,                 commands=['personality'],    pass_bot=True)
        bot.register_message_handler(gemini.reset_personality,               commands=['reset_personality'], pass_bot=True)

        # Start bot
        print("✅ شروع گوش دادن به پیام‌های جدید...")
        try:
            await bot.polling(none_stop=True)
        except Exception as e:
            print(f"❌ خطا در اجرای ربات: {e}")
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 ربات با موفقیت متوقف شد.")
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        traceback.print_exc()
        sys.exit(1)
