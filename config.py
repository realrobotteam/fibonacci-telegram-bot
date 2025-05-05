import os
from google.genai import types

# تنظیمات کانال
CHANNEL_USERNAME = "@fibonacciai"  # نام کاربری کانال خود را اینجا قرار دهید
CHANNEL_ID = -1002081035666  # شناسه عددی کانال خود را اینجا قرار دهید

conf = {
    "error_info":           "⚠️⚠️⚠️\nSomething went wrong !\nplease try to change your prompt or contact the admin !",
    "before_generate_info": "🤖Generating🤖",
    "download_pic_notify":  "🤖Loading picture🤖",
    "model_1":              "gemini-2.5-flash-preview-04-17",
    "model_2":              "gemini-2.5-pro-exp-03-25",
    "model_3":              "gemini-2.0-flash-exp",#for draw
    "streaming_update_interval": 0.5,  # Streaming answer update interval (seconds)
    "GOOGLE_GEMINI_KEY": os.environ.get("GOOGLE_GEMINI_KEY", "your-gemini-api-key-here")
}

safety_settings = [
    types.SafetySetting(
        category="HARM_CATEGORY_HARASSMENT",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_HATE_SPEECH",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_DANGEROUS_CONTENT",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_CIVIC_INTEGRITY",
        threshold="BLOCK_NONE",
    )
]

generation_config = types.GenerateContentConfig(
    response_modalities=['Text', 'Image'],
    safety_settings=safety_settings,
)
