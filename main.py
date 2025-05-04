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
    start, help_command, gemini_private_handler, gemini_group_handler,
    gemini_private_handler_photo, gemini_group_handler_photo,
    gemini_private_handler_document, gemini_group_handler_document,
    gemini_private_handler_voice, gemini_group_handler_voice,
    gemini_private_handler_video, gemini_group_handler_video,
    gemini_private_handler_audio, gemini_group_handler_audio,
    gemini_private_handler_video_note, gemini_group_handler_video_note,
    gemini_private_handler_sticker, gemini_group_handler_sticker,
    gemini_private_handler_animation, gemini_group_handler_animation,
    gemini_private_handler_location, gemini_group_handler_location,
    gemini_private_handler_contact, gemini_group_handler_contact,
    gemini_private_handler_poll, gemini_group_handler_poll,
    gemini_private_handler_dice, gemini_group_handler_dice,
    gemini_private_handler_venue, gemini_group_handler_venue,
    gemini_private_handler_invoice, gemini_group_handler_invoice,
    gemini_private_handler_successful_payment, gemini_group_handler_successful_payment,
    gemini_private_handler_connected_website, gemini_group_handler_connected_website,
    gemini_private_handler_passport_data, gemini_group_handler_passport_data,
    gemini_private_handler_proximity_alert_triggered, gemini_group_handler_proximity_alert_triggered,
    gemini_private_handler_web_app_data, gemini_group_handler_web_app_data,
    gemini_private_handler_message_auto_delete_timer_changed, gemini_group_handler_message_auto_delete_timer_changed,
    gemini_private_handler_voice_chat_scheduled, gemini_group_handler_voice_chat_scheduled,
    gemini_private_handler_voice_chat_started, gemini_group_handler_voice_chat_started,
    gemini_private_handler_voice_chat_ended, gemini_group_handler_voice_chat_ended,
    gemini_private_handler_voice_chat_participants_invited, gemini_group_handler_voice_chat_participants_invited,
    gemini_private_handler_inline_query, gemini_private_handler_chosen_inline_result,
    gemini_private_handler_callback_query, gemini_private_handler_shipping_query,
    gemini_private_handler_pre_checkout_query, gemini_private_handler_poll_answer,
    gemini_private_handler_my_chat_member, gemini_private_handler_chat_member,
    gemini_private_handler_chat_join_request, gemini_private_handler_thread,
    gemini_private_handler_forum_topic_created, gemini_private_handler_forum_topic_edited,
    gemini_private_handler_forum_topic_closed, gemini_private_handler_forum_topic_reopened,
    gemini_private_handler_forum_topic_deleted, gemini_private_handler_general_forum_topic_hidden,
    gemini_private_handler_general_forum_topic_unhidden, gemini_private_handler_write_access_locked,
    gemini_private_handler_video_chat_scheduled, gemini_private_handler_video_chat_started,
    gemini_private_handler_video_chat_ended, gemini_private_handler_video_chat_participants_invited,
    admin_command, admin_callback_handler
)

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

    # Init commands
    bot.register_message_handler(start,                         commands=['start'],         pass_bot=True)
    bot.register_message_handler(help_command,                    commands=['help'],          pass_bot=True)
    bot.register_message_handler(admin_command,                    commands=['admin'],         pass_bot=True)
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

    # Start bot
    print("Starting Gemini_Telegram_Bot.")
    await bot.polling(none_stop=True)

def register_handlers(bot: AsyncTeleBot):
    """ثبت هندلرهای ربات"""
    # دستورات اصلی
    bot.register_message_handler(start, commands=['start'], pass_bot=True)
    bot.register_message_handler(help_command, commands=['help'], pass_bot=True)
    bot.register_message_handler(admin_command, commands=['admin'], pass_bot=True)
    
    # هندلرهای پیام‌های خصوصی
    bot.register_message_handler(gemini_private_handler, content_types=['text'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_photo, content_types=['photo'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_document, content_types=['document'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_voice, content_types=['voice'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_video, content_types=['video'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_audio, content_types=['audio'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_video_note, content_types=['video_note'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_sticker, content_types=['sticker'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_animation, content_types=['animation'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_location, content_types=['location'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_contact, content_types=['contact'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_poll, content_types=['poll'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_dice, content_types=['dice'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_venue, content_types=['venue'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_invoice, content_types=['invoice'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_successful_payment, content_types=['successful_payment'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_connected_website, content_types=['connected_website'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_passport_data, content_types=['passport_data'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_proximity_alert_triggered, content_types=['proximity_alert_triggered'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_web_app_data, content_types=['web_app_data'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_message_auto_delete_timer_changed, content_types=['message_auto_delete_timer_changed'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_voice_chat_scheduled, content_types=['voice_chat_scheduled'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_voice_chat_started, content_types=['voice_chat_started'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_voice_chat_ended, content_types=['voice_chat_ended'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_voice_chat_participants_invited, content_types=['voice_chat_participants_invited'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_inline_query, content_types=['inline_query'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_chosen_inline_result, content_types=['chosen_inline_result'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_callback_query, content_types=['callback_query'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_shipping_query, content_types=['shipping_query'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_pre_checkout_query, content_types=['pre_checkout_query'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_poll_answer, content_types=['poll_answer'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_my_chat_member, content_types=['my_chat_member'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_chat_member, content_types=['chat_member'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_chat_join_request, content_types=['chat_join_request'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_thread, content_types=['thread'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_forum_topic_created, content_types=['forum_topic_created'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_forum_topic_edited, content_types=['forum_topic_edited'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_forum_topic_closed, content_types=['forum_topic_closed'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_forum_topic_reopened, content_types=['forum_topic_reopened'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_forum_topic_deleted, content_types=['forum_topic_deleted'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_general_forum_topic_hidden, content_types=['general_forum_topic_hidden'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_general_forum_topic_unhidden, content_types=['general_forum_topic_unhidden'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_write_access_locked, content_types=['write_access_locked'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_video_chat_scheduled, content_types=['video_chat_scheduled'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_video_chat_started, content_types=['video_chat_started'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_video_chat_ended, content_types=['video_chat_ended'], chat_types=['private'], pass_bot=True)
    bot.register_message_handler(gemini_private_handler_video_chat_participants_invited, content_types=['video_chat_participants_invited'], chat_types=['private'], pass_bot=True)
    
    # هندلرهای پیام‌های گروهی
    bot.register_message_handler(gemini_group_handler, content_types=['text'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_photo, content_types=['photo'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_document, content_types=['document'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_voice, content_types=['voice'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_video, content_types=['video'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_audio, content_types=['audio'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_video_note, content_types=['video_note'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_sticker, content_types=['sticker'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_animation, content_types=['animation'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_location, content_types=['location'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_contact, content_types=['contact'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_poll, content_types=['poll'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_dice, content_types=['dice'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_venue, content_types=['venue'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_invoice, content_types=['invoice'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_successful_payment, content_types=['successful_payment'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_connected_website, content_types=['connected_website'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_passport_data, content_types=['passport_data'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_proximity_alert_triggered, content_types=['proximity_alert_triggered'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_web_app_data, content_types=['web_app_data'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_message_auto_delete_timer_changed, content_types=['message_auto_delete_timer_changed'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_voice_chat_scheduled, content_types=['voice_chat_scheduled'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_voice_chat_started, content_types=['voice_chat_started'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_voice_chat_ended, content_types=['voice_chat_ended'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_voice_chat_participants_invited, content_types=['voice_chat_participants_invited'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_inline_query, content_types=['inline_query'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_chosen_inline_result, content_types=['chosen_inline_result'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_callback_query, content_types=['callback_query'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_shipping_query, content_types=['shipping_query'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_pre_checkout_query, content_types=['pre_checkout_query'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_poll_answer, content_types=['poll_answer'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_my_chat_member, content_types=['my_chat_member'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_chat_member, content_types=['chat_member'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_chat_join_request, content_types=['chat_join_request'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_thread, content_types=['thread'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_forum_topic_created, content_types=['forum_topic_created'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_forum_topic_edited, content_types=['forum_topic_edited'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_forum_topic_closed, content_types=['forum_topic_closed'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_forum_topic_reopened, content_types=['forum_topic_reopened'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_forum_topic_deleted, content_types=['forum_topic_deleted'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_general_forum_topic_hidden, content_types=['general_forum_topic_hidden'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_general_forum_topic_unhidden, content_types=['general_forum_topic_unhidden'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_write_access_locked, content_types=['write_access_locked'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_video_chat_scheduled, content_types=['video_chat_scheduled'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_video_chat_started, content_types=['video_chat_started'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_video_chat_ended, content_types=['video_chat_ended'], chat_types=['group', 'supergroup'], pass_bot=True)
    bot.register_message_handler(gemini_group_handler_video_chat_participants_invited, content_types=['video_chat_participants_invited'], chat_types=['group', 'supergroup'], pass_bot=True)
    
    # هندلرهای کال‌بک
    bot.register_callback_query_handler(admin_callback_handler, func=lambda call: call.data.startswith('admin_'), pass_bot=True)

if __name__ == '__main__':
    asyncio.run(main())
