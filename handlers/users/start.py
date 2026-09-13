from aiogram import Router, types, F
from aiogram.filters import Command
from loader import ADMIN_IDS, logger
from keyboards.default_kb import get_start_kb
from database import get_connection

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "👋 <b>Assalomu alaykum! BilimliBot ga xush kelibsiz!</b>\n\n"
        "Bu bot orqali siz turli qiziqarli savollarga javob berib tangalar ishlashingiz va ularni haqiqiy pulga almashtirib olishingiz mumkin! 💰\n\n"
        "📚 Fanlar:\n\n"
        "/quiztarix – 🏛 Tarix\n"
        "/quizgeo – 🗺 Geografiya\n"
        "/quizfazo – 🌠 Astronomiya\n"
        "/quizeng - ingliz tili \n"
        "/quizspo – 🏅 Sport\n"
        "/quiztop - eng sara testlar\n"
        "/quizqiziqarli – 🔍 Qiziqarli testlar\n"
        "/quiz – 🎯 Aralash testlar\n"
        "/quiztil - tilshunoslik\n"
        "/quiztez - tezkor \n\n"
        "Fanlardan birini tanlash uchun ustiga bosing 👆"
    )
    is_private = (message.chat.type == "private")
    try:
        await message.answer(text, reply_markup=get_start_kb(is_private=is_private), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in cmd_start answer: {e}")
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        fallback_kb = InlineKeyboardBuilder()
        fallback_kb.button(text="📚 Fanlar ro'yxati", callback_data="show_subjects")
        await message.answer(text, reply_markup=fallback_kb.as_markup(), parse_mode="HTML")

@router.message(Command("royhat"))
async def cmd_royhat(message: types.Message):
    async with await get_connection() as conn:
        rows = await conn.fetch('''
            SELECT s.key, s.name, s.emoji, c.name as category_name
            FROM subjects s
            LEFT JOIN categories c ON s.category_id = c.id
            WHERE s.is_active = TRUE
            AND EXISTS (SELECT 1 FROM questions q WHERE q.subject = s.key)
            ORDER BY c.sort_order ASC, s.name ASC
        ''')
        
    if not rows:
        await message.answer("😔 Hozircha fanlar mavjud emas.")
        return

    categories_dict = {}
    for r in rows:
        cat_name = r['category_name'] or "Boshqa yo'nalishlar"
        if cat_name not in categories_dict:
            categories_dict[cat_name] = []
        categories_dict[cat_name].append(r)

    text = "📚 <b>Mavjud barcha fanlar ro'yxati:</b>\n\n"
    for cat_name, subs in categories_dict.items():
        text += f"🔹 <b>{cat_name}:</b>\n"
        for s in subs:
            emoji = s['emoji'] or "📚"
            name = s['name'] or s['key'].capitalize()
            cmd = f"/quiz{s['key']}"
            text += f"  {emoji} {name} — {cmd}\n"
        text += "\n"
    
    text += "Fanlardan birini tanlash va testni boshlash uchun tegishli buyruq ustiga bosing 👆"
    await message.answer(text, parse_mode="HTML")

@router.callback_query(F.data == "show_subjects")
async def show_subjects_list(call: types.CallbackQuery):
    async with await get_connection() as conn:
        rows = await conn.fetch('''
            SELECT s.key, s.name, s.emoji, c.name as category_name
            FROM subjects s
            LEFT JOIN categories c ON s.category_id = c.id
            WHERE s.is_active = TRUE
            AND EXISTS (SELECT 1 FROM questions q WHERE q.subject = s.key)
            ORDER BY c.sort_order ASC, s.name ASC
        ''')
        
    if not rows:
        await call.message.answer("😔 Hozircha fanlar mavjud emas.")
        await call.answer()
        return

    categories_dict = {}
    for r in rows:
        cat_name = r['category_name'] or "Boshqa yo'nalishlar"
        if cat_name not in categories_dict:
            categories_dict[cat_name] = []
        categories_dict[cat_name].append(r)

    text = "📚 <b>Mavjud barcha fanlar ro'yxati:</b>\n\n"
    for cat_name, subs in categories_dict.items():
        text += f"🔹 <b>{cat_name}:</b>\n"
        for s in subs:
            emoji = s['emoji'] or "📚"
            name = s['name'] or s['key'].capitalize()
            cmd = f"/quiz{s['key']}"
            text += f"  {emoji} {name} — {cmd}\n"
        text += "\n"
    
    text += "Fanlardan birini tanlash va testni boshlash uchun tegishli buyruq ustiga bosing 👆"
    await call.message.answer(text, parse_mode="HTML")
    await call.answer()
