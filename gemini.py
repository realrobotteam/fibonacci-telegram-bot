import io
import time
import traceback
import sys
from PIL import Image
from telebot.types import Message
from md2tgmd import escape
from telebot import TeleBot
from config import conf, generation_config
from google import genai

gemini_draw_dict = {}
gemini_chat_dict = {}
gemini_pro_chat_dict = {}
default_model_dict = {}
personality_dict = {}  # دیکشنری برای ذخیره شخصیت‌های سفارشی کاربران

model_1                 =       conf["model_1"]
model_2                 =       conf["model_2"]
error_info              =       conf["error_info"]
before_generate_info    =       conf["before_generate_info"]
download_pic_notify     =       conf["download_pic_notify"]
default_personality     =       conf["bot_personality"]

search_tool = {'google_search': {}}

client = genai.Client(api_key=sys.argv[2])

def get_user_personality(user_id: str) -> str:
    """دریافت شخصیت تنظیم شده برای کاربر"""
    return personality_dict.get(str(user_id), default_personality)

async def set_personality(message: Message, bot: TeleBot) -> None:
    """تنظیم شخصیت جدید برای ربات"""
    try:
        # دریافت متن شخصیت از پیام
        personality_text = message.text.strip().split(maxsplit=1)[1].strip()
        
        # ذخیره شخصیت جدید
        personality_dict[str(message.from_user.id)] = personality_text
        
        await bot.reply_to(
            message,
            "✅ شخصیت جدید ربات با موفقیت تنظیم شد!\n\n🤖 از این پس با این شخصیت به پیام‌های شما پاسخ خواهم داد.",
            parse_mode="HTML"
        )
    except IndexError:
        # اگر متن شخصیت ارائه نشده باشد
        await bot.reply_to(
            message,
            conf["personality_help"],
            parse_mode="HTML"
        )

async def reset_personality(message: Message, bot: TeleBot) -> None:
    """بازنشانی شخصیت ربات به حالت پیش‌فرض"""
    if str(message.from_user.id) in personality_dict:
        del personality_dict[str(message.from_user.id)]
    await bot.reply_to(
        message,
        "✅ شخصیت ربات به حالت پیش‌فرض بازنشانی شد.",
        parse_mode="HTML"
    )

async def gemini_stream(bot:TeleBot, message:Message, m:str, model_type:str):
    sent_message = None
    try:
        sent_message = await bot.reply_to(message, "🤖 در حال پردازش...")

        chat = None
        if model_type == model_1:
            chat_dict = gemini_chat_dict
        else:
            chat_dict = gemini_pro_chat_dict

        if str(message.from_user.id) not in chat_dict:
            chat = client.aio.chats.create(model=model_1, config={'tools': [search_tool]})
            chat_dict[str(message.from_user.id)] = chat
        else:
            chat = chat_dict[str(message.from_user.id)]

        # اضافه کردن شخصیت به پیام
        personality = get_user_personality(str(message.from_user.id))
        prompt = f"{personality}\n\nکاربر پرسیده است: {m}"

        response = await chat.send_message_stream(prompt)

        full_response = ""
        last_update = time.time()
        update_interval = conf["streaming_update_interval"]

        async for chunk in response:
            full_response += chunk.text
            
            # به‌روزرسانی پیام هر 0.5 ثانیه
            if time.time() - last_update >= update_interval:
                try:
                    await bot.edit_message_text(
                        escape(full_response),
                        sent_message.chat.id,
                        sent_message.message_id,
                        parse_mode="MarkdownV2"
                    )
                    last_update = time.time()
                except Exception as e:
                    print(f"Error updating message: {e}")

        # به‌روزرسانی نهایی پیام
        try:
            await bot.edit_message_text(
                escape(full_response),
                sent_message.chat.id,
                sent_message.message_id,
                parse_mode="MarkdownV2"
            )
        except Exception as e:
            print(f"Error in final message update: {e}")

    except Exception as e:
        print(traceback.format_exc())
        if sent_message:
            await bot.edit_message_text(
                error_info,
                sent_message.chat.id,
                sent_message.message_id
            )

async def gemini_edit(bot: TeleBot, message: Message, m: str, photo_file: bytes):

    image = Image.open(io.BytesIO(photo_file))
    try:
        response = await client.aio.models.generate_content(
        model=model_1,
        contents=[m, image],
        config=generation_config
    )
    except Exception as e:
        await bot.send_message(message.chat.id, e.str())
    for part in response.candidates[0].content.parts:
        if part.text is not None:
            await bot.send_message(message.chat.id, escape(part.text), parse_mode="MarkdownV2")
        elif part.inline_data is not None:
            photo = part.inline_data.data
            await bot.send_photo(message.chat.id, photo)

async def gemini_draw(bot:TeleBot, message:Message, m:str):
    chat_dict = gemini_draw_dict
    if str(message.from_user.id) not in chat_dict:
        chat = client.aio.chats.create(
            model=model_1,
            config=generation_config,
        )
        chat_dict[str(message.from_user.id)] = chat
    else:
        chat = chat_dict[str(message.from_user.id)]

    response = await chat.send_message(m)
    for part in response.candidates[0].content.parts:
        if part.text is not None:
            text = part.text
            while len(text) > 4000:
                await bot.send_message(message.chat.id, escape(text[:4000]), parse_mode="MarkdownV2")
                text = text[4000:]
            if text:
                await bot.send_message(message.chat.id, escape(text), parse_mode="MarkdownV2")
        elif part.inline_data is not None:
            photo = part.inline_data.data
            await bot.send_photo(message.chat.id, photo)
