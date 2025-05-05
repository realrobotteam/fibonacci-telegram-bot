from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_user_reply_markup() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("👍 پسندیدم", callback_data="like"),
        InlineKeyboardButton("👎 نپسندیدم", callback_data="dislike"),
        InlineKeyboardButton("🔄 دوباره تولید کن", callback_data="regenerate"),
        InlineKeyboardButton("✏️ ویرایش", callback_data="edit"),
        InlineKeyboardButton("📋 کپی", callback_data="copy"),
        InlineKeyboardButton("💬 سوال جدید", callback_data="new_question"),
        InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")
    )
    return markup 