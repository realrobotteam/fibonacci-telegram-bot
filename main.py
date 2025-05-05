import argparse
import traceback
import re
import telebot
from telebot import TeleBot, types
import os
from config import conf, generation_config, safety_settings
import handlers
from handlers import (
    start, gemini_stream_handler, gemini_pro_stream_handler, clear, switch,
    gemini_private_handler, gemini_photo_handler, gemini_edit_handler, draw_handler,
    handle_channel_membership, handle_assistant_callback, get_assistants_markup,
    get_content_menu_markup, handle_content_callback, handle_content_text, get_special_tools_markup, handle_special_tools_callback,
    get_user_reply_markup, get_support_markup, user_content_state, model_1
)
from channel_checker import check_membership, get_join_channel_markup, CHANNEL_ID
import gemini

# Init args
parser = argparse.ArgumentParser()
parser.add_argument("tg_token", help="telegram token")
parser.add_argument("GOOGLE_GEMINI_KEY", help="Google Gemini API key")
options = parser.parse_args()
print("Arg parse done.")

# Init bot
bot = TeleBot(options.tg_token)

bot.delete_my_commands()
bot.set_my_commands([
    telebot.types.BotCommand("start", "Start"),
    telebot.types.BotCommand("gemini", f"using {conf['model_1']}"),
    telebot.types.BotCommand("gemini_pro", f"using {conf['model_2']}"),
    telebot.types.BotCommand("draw", "draw picture"),
    telebot.types.BotCommand("edit", "edit photo"),
    telebot.types.BotCommand("clear", "Clear all history"),
    telebot.types.BotCommand("switch","switch default model")
])
print("Bot init done.")

# Register content text handler
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
def callback_handler(call):
    if call.data == 'show_assistants':
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "🤖 لطفاً یکی از دستیارهای هوشمند را انتخاب کنید:",
            reply_markup=get_assistants_markup()
        )
    else:
        handle_assistant_callback(call, bot)

@bot.callback_query_handler(func=lambda call: call.data.startswith('content_') or call.data in ['show_content_menu', 'back_main_menu'])
def content_callback_handler(call):
    handle_content_callback(call, bot)

@bot.callback_query_handler(func=lambda call: call.data.startswith('tool_') or call.data == 'show_special_tools')
def special_tools_callback_handler(call):
    handle_special_tools_callback(call, bot)

@bot.callback_query_handler(func=lambda call: call.data in [
    'like', 'dislike', 'regenerate', 'edit', 'copy', 'new_question', 'main_menu'])
def user_reply_buttons_handler(call):
    if call.data == 'like':
        bot.answer_callback_query(call.id, "خوشحالیم که راضی بودید! 😊", show_alert=True)
    elif call.data == 'dislike':
        bot.answer_callback_query(call.id, "متاسفیم که راضی نبودید. لطفاً بازخورد خود را ارسال کنید.", show_alert=True)
    elif call.data == 'regenerate':
        bot.answer_callback_query(call.id, "در حال تولید مجدد پاسخ...", show_alert=True)
        user_id = call.from_user.id
        if user_id in user_content_state:
            content_type = user_content_state[user_id]['type']
            last_prompt = user_content_state[user_id].get('last_prompt', None)
            if last_prompt:
                bot.send_message(call.message.chat.id, "⏳ در حال تولید مجدد محتوا ...")
                # اگر gemini_stream شما async است باید آن را sync کنید یا از threading استفاده کنید
    elif call.data == 'edit':
        bot.answer_callback_query(call.id, "لطفاً متن جدید خود را ارسال کنید.", show_alert=True)
    elif call.data == 'copy':
        bot.answer_callback_query(call.id, "برای کپی متن، روی پیام کلیک کنید و گزینه کپی را انتخاب کنید.", show_alert=True)
    elif call.data == 'new_question':
        bot.answer_callback_query(call.id, "سوال جدید خود را ارسال کنید.", show_alert=True)
    elif call.data == 'main_menu':
        bot.answer_callback_query(call.id, "بازگشت به منوی اصلی.", show_alert=True)
        bot.send_message(call.message.chat.id, "به منوی اصلی بازگشتید.", reply_markup=get_support_markup())

print("Starting Gemini_Telegram_Bot.")
bot.polling(none_stop=True)
