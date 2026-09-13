from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loader import WEBAPP_URL

def get_start_kb():
    kb = InlineKeyboardBuilder()
    web_url = WEBAPP_URL or "https://bilmli-bot-production.up.railway.app"
    
    kb.button(text="📱 Kabinet", web_app=WebAppInfo(url=web_url))
    kb.button(text="📚 Fanlar ro'yxati", callback_data="show_subjects")
    kb.adjust(1)
    return kb.as_markup()
