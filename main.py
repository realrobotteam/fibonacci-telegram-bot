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
from telebot import TeleBot
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
import json
from datetime import datetime
from database import Database
from new_features.financial_assistant import FinancialAssistant
from new_features.language_learning import LanguageLearning
from new_features.code_assistant import CodeAssistant
from new_features.content_summarizer import ContentSummarizer
from new_features.smart_translator import SmartTranslator
from new_features.content_generator import ContentGenerator
from new_features.sentiment_analyzer import SentimentAnalyzer
from new_features.language_detector import LanguageDetector

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
        func=lambda message: message.chat.type == "private" and (message.from_user.id not in handlers.user_content_state or not handlers.user_content_state[message.from_user.id]['type'].startswith('assistant_')),
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

class Bot:
    def __init__(self):
        # ... existing code ...
        
        # ایجاد نمونه‌های کلاس‌های جدید
        self.financial_assistant = FinancialAssistant(self.bot)
        self.language_learning = LanguageLearning(self.bot)
        self.code_assistant = CodeAssistant(self.bot)
        self.content_summarizer = ContentSummarizer(self.bot)
        self.smart_translator = SmartTranslator(self.bot)
        self.content_generator = ContentGenerator(self.bot)
        self.sentiment_analyzer = SentimentAnalyzer(self.bot)
        self.language_detector = LanguageDetector(self.bot)
        
        # ... existing code ...
        
    async def handle_callback(self, call: types.CallbackQuery):
        """پردازش callback‌ها"""
        if call.data == "financial_assistant":
            await self.financial_assistant.show_menu(call)
        elif call.data == "language_learning":
            await self.language_learning.show_menu(call)
        elif call.data == "code_assistant":
            await self.code_assistant.show_menu(call)
        elif call.data == "content_summarizer":
            await self.content_summarizer.show_menu(call)
        elif call.data == "smart_translator":
            await self.smart_translator.show_menu(call)
        elif call.data == "content_generator":
            await self.content_generator.show_menu(call)
        elif call.data == "sentiment_analyzer":
            await self.sentiment_analyzer.show_menu(call)
        elif call.data == "language_detector":
            await self.language_detector.show_menu(call)
        # ... existing code ...

if __name__ == '__main__':
    asyncio.run(main())
