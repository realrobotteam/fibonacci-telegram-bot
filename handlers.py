from telebot import TeleBot
from telebot.types import Message
from md2tgmd import escape
import traceback
from config import conf
import gemini
from decorators import check_channel_subscription

error_info              =       conf["error_info"]
before_generate_info    =       conf["before_generate_info"]
download_pic_notify     =       conf["download_pic_notify"]
model_1                 =       conf["model_1"]
model_2                 =       conf["model_2"]

gemini_chat_dict        = gemini.gemini_chat_dict
gemini_pro_chat_dict    = gemini.gemini_pro_chat_dict
default_model_dict      = gemini.default_model_dict
gemini_draw_dict        = gemini.gemini_draw_dict

@check_channel_subscription()
async def start(message: Message, bot: TeleBot) -> None:
    try:
        await bot.reply_to(message , escape("Welcome, you can ask me questions now. \nFor example: `Who is john lennon?`"), parse_mode="MarkdownV2")
    except IndexError:
        await bot.reply_to(message, error_info)

@check_channel_subscription()
async def gemini_stream_handler(message: Message, bot: TeleBot) -> None:
    try:
        m = message.text.strip().split(maxsplit=1)[1].strip()
    except IndexError:
        await bot.reply_to(message, escape("Please add what you want to say after /gemini. \nFor example: `/gemini Who is john lennon?`"), parse_mode="MarkdownV2")
        return
    await gemini.gemini_stream(bot, message, m, model_1)

@check_channel_subscription()
async def gemini_pro_stream_handler(message: Message, bot: TeleBot) -> None:
    try:
        m = message.text.strip().split(maxsplit=1)[1].strip()
    except IndexError:
        await bot.reply_to(message, escape("Please add what you want to say after /gemini_pro. \nFor example: `/gemini_pro Who is john lennon?`"), parse_mode="MarkdownV2")
        return
    await gemini.gemini_stream(bot, message, m, model_2)

@check_channel_subscription()
async def clear(message: Message, bot: TeleBot) -> None:
    # Check if the chat is already in gemini_chat_dict.
    if (str(message.from_user.id) in gemini_chat_dict):
        del gemini_chat_dict[str(message.from_user.id)]
    if (str(message.from_user.id) in gemini_pro_chat_dict):
        del gemini_pro_chat_dict[str(message.from_user.id)]
    if (str(message.from_user.id) in gemini_draw_dict):
        del gemini_draw_dict[str(message.from_user.id)]
    await bot.reply_to(message, "Your history has been cleared")

@check_channel_subscription()
async def switch(message: Message, bot: TeleBot) -> None:
    if str(message.from_user.id) not in default_model_dict:
        default_model_dict[str(message.from_user.id)] = model_1
    elif default_model_dict[str(message.from_user.id)] == model_1:
        default_model_dict[str(message.from_user.id)] = model_2
    else:
        default_model_dict[str(message.from_user.id)] = model_1
    await bot.reply_to(message, f"Default model switched to {default_model_dict[str(message.from_user.id)]}")

@check_channel_subscription()
async def gemini_private_handler(message: Message, bot: TeleBot) -> None:
    if str(message.from_user.id) not in default_model_dict:
        default_model_dict[str(message.from_user.id)] = model_1
    await gemini.gemini_stream(bot, message, message.text, default_model_dict[str(message.from_user.id)])

@check_channel_subscription()
async def gemini_photo_handler(message: Message, bot: TeleBot) -> None:
    try:
        await bot.reply_to(message, download_pic_notify)
        file_info = await bot.get_file(message.photo[-1].file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        await gemini.gemini_vision(bot, message, downloaded_file)
    except Exception as e:
        print(traceback.format_exc())
        await bot.reply_to(message, error_info)

@check_channel_subscription()
async def gemini_edit_handler(message: Message, bot: TeleBot) -> None:
    if str(message.from_user.id) not in gemini_draw_dict:
        await bot.reply_to(message, "Please send me a picture first.")
        return
    try:
        m = message.text.strip().split(maxsplit=1)[1].strip()
    except IndexError:
        await bot.reply_to(message, escape("Please add what you want to say after /edit. \nFor example: `/edit make it more colorful`"), parse_mode="MarkdownV2")
        return
    await gemini.gemini_vision_edit(bot, message, m)

@check_channel_subscription()
async def draw_handler(message: Message, bot: TeleBot) -> None:
    try:
        m = message.text.strip().split(maxsplit=1)[1].strip()
    except IndexError:
        await bot.reply_to(message, escape("Please add what you want to say after /draw. \nFor example: `/draw A cat sitting on a chair`"), parse_mode="MarkdownV2")
        return
    await gemini.gemini_draw(bot, message, m)
