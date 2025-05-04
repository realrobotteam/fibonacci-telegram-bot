import argparse
import traceback
import asyncio
import re
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.asyncio_storage import StateMemoryStorage
from config import conf, generation_config, safety_settings
from handlers import (
    start,
    help_command,
    gemini_private_handler,
    gemini_group_handler,
    handle_new_member,
    handle_left_member,
    handle_message,
    handle_callback
)
from admin_panel import handle_admin_command

# Init args
parser = argparse.ArgumentParser()
parser.add_argument("tg_token", help="telegram token")
parser.add_argument("GOOGLE_GEMINI_KEY", help="Google Gemini API key")
options = parser.parse_args()
print("Arg parse done.")


async def main():
    # Init bot
    bot = AsyncTeleBot(options.tg_token, state_storage=StateMemoryStorage())
    await bot.delete_my_commands(scope=None, language_code=None)
    await bot.set_my_commands(
    commands=[
        telebot.types.BotCommand("start", "Start"),
        telebot.types.BotCommand("gemini", f"using {conf['model_1']}"),
        telebot.types.BotCommand("gemini_pro", f"using {conf['model_2']}"),
        telebot.types.BotCommand("draw", "draw picture"),
        telebot.types.BotCommand("edit", "edit photo"),
        telebot.types.BotCommand("clear", "Clear all history"),
        telebot.types.BotCommand("switch","switch default model")
    ],
)
    print("Bot init done.")

    # Init commands
    bot.register_message_handler(start, commands=["start"], pass_bot=True)
    bot.register_message_handler(help_command, commands=["help"], pass_bot=True)
    bot.register_message_handler(gemini_private_handler, content_types=["text"], chat_types=["private"], pass_bot=True)
    bot.register_message_handler(gemini_group_handler, content_types=["text"], chat_types=["group", "supergroup"], pass_bot=True)
    bot.register_message_handler(handlers.gemini_stream_handler,         commands=['gemini'],        pass_bot=True)
    bot.register_message_handler(handlers.gemini_pro_stream_handler,     commands=['gemini_pro'],    pass_bot=True)
    bot.register_message_handler(handlers.draw_handler,                  commands=['draw'],          pass_bot=True)
    bot.register_message_handler(handlers.gemini_edit_handler,           commands=['edit'],          pass_bot=True)
    bot.register_message_handler(handlers.clear,                         commands=['clear'],         pass_bot=True)
    bot.register_message_handler(handlers.switch,                        commands=['switch'],        pass_bot=True)
    bot.register_message_handler(handlers.gemini_photo_handler,          content_types=["photo"],    pass_bot=True)
    
    # Register channel membership handler
    bot.register_message_handler(handle_new_member, content_types=["new_chat_members"], pass_bot=True)
    bot.register_message_handler(handle_left_member, content_types=["left_chat_member"], pass_bot=True)
    
    # Register admin commands
    bot.register_message_handler(handle_admin_command, commands=["admin"], pass_bot=True)
    bot.register_message_handler(handle_message, content_types=["text"], pass_bot=True)
    bot.register_callback_query_handler(handle_callback, func=lambda call: True, pass_bot=True)

    # Start bot
    print("Starting Gemini_Telegram_Bot.")
    await bot.polling(none_stop=True)

if __name__ == '__main__':
    asyncio.run(main())
