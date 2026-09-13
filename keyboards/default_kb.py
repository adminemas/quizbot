import re
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loader import WEBAPP_URL

def is_valid_https_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    pattern = r'^https://[a-zA-Z0-9\-\.]+(\.[a-zA-Z0-9\-]+)(:[0-9]+)?(/.*)?$'
    return bool(re.match(pattern, url.strip()))

def get_start_kb(is_private: bool = True):
    kb = InlineKeyboardBuilder()
    web_url = WEBAPP_URL
    
    if web_url and is_valid_https_url(web_url):
        if is_private:
            kb.button(text="📱 Kabinet", web_app=WebAppInfo(url=web_url))
        else:
            kb.button(text="📱 Kabinet", url=web_url)
            
    kb.button(text="📚 Fanlar ro'yxati", callback_data="show_subjects")
    kb.adjust(1)
    return kb.as_markup()
