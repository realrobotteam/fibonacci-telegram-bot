from google.genai import types
conf = {
    "error_info":           "⚠️⚠️⚠️\nSomething went wrong !\nplease try to change your prompt or contact the admin !",
    "before_generate_info": "🤖Generating🤖",
    "download_pic_notify":  "🤖Loading picture🤖",
    "model_1":              "gemini-2.0-flash-exp",
    "model_2":              "gemini-1.5-pro-latest",
    "streaming_update_interval": 0.5,  # Streaming answer update interval (seconds)
    "required_channel": "@your_channel",  # آیدی کانال شما
    "not_subscribed_message": "⚠️ کاربر گرامی\n\n🔰 برای استفاده از خدمات ربات، باید عضو کانال ما باشید:\n\n📣 {channel_link}\n\n✅ پس از عضویت در کانال، مجدداً دستور خود را ارسال کنید."
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