import argparse
import traceback
import asyncio
import re
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.asyncio_storage import StateMemoryStorage
from telebot import types
import os
from config import conf, generation_config, safety_settings
import handlers
from handlers import (
    start, gemini_stream_handler, gemini_pro_stream_handler, clear, switch,
    gemini_private_handler, gemini_photo_handler, gemini_edit_handler, draw_handler,
    handle_channel_membership, handle_assistant_callback, get_assistants_markup,
    get_content_menu_markup, handle_content_callback, handle_content_text, get_special_tools_markup, handle_special_tools_callback
)
from channel_checker import check_membership, get_join_channel_markup, CHANNEL_ID

# Init args
parser = argparse.ArgumentParser()
parser.add_argument("tg_token", help="telegram token")
parser.add_argument("GOOGLE_GEMINI_KEY", help="Google Gemini API key")
options = parser.parse_args()
print("Arg parse done.")


async def main():
    # Init bot
    bot = AsyncTeleBot(options.tg_token)
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

    # Register content text handler (در ابتدای ثبت هندلرها)
    bot.register_message_handler(
        handle_content_text,
        func=lambda message: message.from_user.id in handlers.user_content_state,
        content_types=['text'],
        pass_bot=True)

    # Init commands
    bot.register_message_handler(start,                         commands=['start'],         pass_bot=True)
    bot.register_message_handler(gemini_stream_handler,         commands=['gemini'],        pass_bot=True)
    bot.register_message_handler(gemini_pro_stream_handler,     commands=['gemini_pro'],    pass_bot=True)
    bot.register_message_handler(draw_handler,                  commands=['draw'],          pass_bot=True)
    bot.register_message_handler(gemini_edit_handler,           commands=['edit'],          pass_bot=True)
    bot.register_message_handler(clear,                         commands=['clear'],         pass_bot=True)
    bot.register_message_handler(switch,                        commands=['switch'],        pass_bot=True)
    bot.register_message_handler(gemini_photo_handler,          content_types=["photo"],    pass_bot=True)
    bot.register_message_handler(
        gemini_private_handler,
        func=lambda message: message.chat.type == "private",
        content_types=['text'],
        pass_bot=True)
    
    # Register channel membership handler
    bot.register_chat_member_handler(
        handle_channel_membership,
        func=lambda chat_member: True,
        pass_bot=True
    )

    # Register callback handler
    @bot.callback_query_handler(func=lambda call: call.data.startswith('assistant_') or call.data == 'show_assistants')
    async def callback_handler(call: types.CallbackQuery):
        if call.data == 'show_assistants':
            await bot.answer_callback_query(call.id)
            await bot.send_message(
                call.message.chat.id,
                "🤖 لطفاً یکی از دستیارهای هوشمند را انتخاب کنید:",
                reply_markup=get_assistants_markup()
            )
        else:
            await handle_assistant_callback(call, bot)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('content_') or call.data in ['show_content_menu', 'back_main_menu'])
    async def content_callback_handler(call: types.CallbackQuery):
        await handle_content_callback(call, bot)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('tool_') or call.data == 'show_special_tools')
    async def special_tools_callback_handler(call: types.CallbackQuery):
        await handle_special_tools_callback(call, bot)

    # Start bot
    print("Starting Gemini_Telegram_Bot.")
    await bot.polling(none_stop=True)

if __name__ == '__main__':
    asyncio.run(main())
