from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import get_user_by_identifier, transfer_coins, get_or_create_user
from loader import bot

router = Router()

async def process_send(message: types.Message, target_identifier: str, amount_str: str):
    try:
        amount = int(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Tanga miqdori musbat butun son bo'lishi kerak!")
        return

    sender_id = message.from_user.id
    await get_or_create_user(sender_id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)

    target_user = await get_user_by_identifier(target_identifier)
    if not target_user:
        await message.answer(f"❌ Foydalanuvchi topilmadi ({target_identifier}). U botdan kamida bir marta foydalangan bo'lishi kerak.")
        return

    target_id = target_user["user_id"]
    if sender_id == target_id:
        await message.answer("❌ O'zingizga tanga yubora olmaysiz!")
        return

    success = await transfer_coins(sender_id, target_id, amount)
    if success:
        target_name = target_user["username"] or target_user["first_name"] or str(target_id)
        await message.answer(f"✅ <b>{amount}</b> tanga muvaffaqiyatli <b>{target_name}</b> ga yuborildi!", parse_mode="HTML")
        
        try:
            sender_name = message.from_user.username or message.from_user.first_name
            await bot.send_message(target_id, f"💸 <b>{sender_name}</b> sizga <b>{amount}</b> tanga yubordi!", parse_mode="HTML")
        except Exception:
            pass
    else:
        await message.answer("❌ Hisobingizda yetarli tanga mavjud emas yoki xatolik yuz berdi.")

@router.message(Command("send"))
async def cmd_send(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) != 3:
        await message.answer("⚠️ Noto'g'ri format.\nFoydalanish: `/send <@username yoki ID> <miqdor>`\nMisol: `/send @uzbdo 10`")
        return
    await process_send(message, args[1], args[2])

@router.message(F.text.lower().startswith("send "))
async def reply_send(message: types.Message):
    # Faqat guruhlarda ishlashi mumkin, yuboruvchi kimgadir reply qilgan bo'lishi kerak
    if message.chat.type == "private" or not message.reply_to_message:
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        return
        
    amount_str = parts[1]
    target_id = str(message.reply_to_message.from_user.id)
    
    # Check if target is bot
    if message.reply_to_message.from_user.is_bot:
        await message.answer("❌ Botga tanga yuborib bo'lmaydi.")
        return
        
    # Ensure target exists in DB
    await get_or_create_user(
        message.reply_to_message.from_user.id,
        message.reply_to_message.from_user.username,
        message.reply_to_message.from_user.first_name,
        message.reply_to_message.from_user.last_name
    )
        
    await process_send(message, target_id, amount_str)

@router.message(F.text.lower().startswith("put "))
async def cmd_put(message: types.Message):
    if message.chat.type == "private":
        return
        
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        return
        
    try:
        amount = int(parts[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        return

    requester_id = message.from_user.id
    
    await get_or_create_user(requester_id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="Yuborish 💸", callback_data=f"put_send_{requester_id}_{amount}")
    
    await message.answer(
        f"🎯 <b>Foydalanuvchi {amount} tanga yig'moqda!</b>\n"
        f"Uni qo'llab-quvvatlash uchun quyidagi tugmani bosing va o'z hissangizni qo'shing.",
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data.startswith("put_send_"))
async def process_put_send(call: types.CallbackQuery):
    _, _, requester_id_str, amount_str = call.data.split("_")
    requester_id = int(requester_id_str)
    amount = int(amount_str)
    
    sender_id = call.from_user.id
    
    if sender_id == requester_id:
        await call.answer("❌ O'zingiz so'ragan tangani o'zingiz yubora olmaysiz!", show_alert=True)
        return
        
    kb = InlineKeyboardBuilder()
    kb.button(text="Ha", callback_data=f"confirm_send_{requester_id}_{amount}")
    kb.button(text="Yo'q", callback_data="cancel_send")
    
    await call.message.edit_text(
        f"Rostan ham {amount} tanga yuborishni tasdiqlaysizmi?",
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data == "cancel_send")
async def process_cancel_send(call: types.CallbackQuery):
    await call.message.edit_text("❌ Yuborish bekor qilindi.")
    await call.answer()

@router.callback_query(F.data.startswith("confirm_send_"))
async def process_confirm_send(call: types.CallbackQuery):
    _, _, target_id_str, amount_str = call.data.split("_")
    target_id = int(target_id_str)
    amount = int(amount_str)
    sender_id = call.from_user.id
    
    await get_or_create_user(sender_id, call.from_user.username, call.from_user.first_name, call.from_user.last_name)
    
    success = await transfer_coins(sender_id, target_id, amount)
    
    if success:
        await call.message.edit_text(f"✅ Muvaffaqiyatli yuborildi! ({amount} tanga)")
        try:
            sender_name = call.from_user.username or call.from_user.first_name
            await bot.send_message(target_id, f"💸 <b>{sender_name}</b> guruhdagi so'rovingizga binoan sizga <b>{amount}</b> tanga yubordi!", parse_mode="HTML")
        except Exception:
            pass
    else:
        await call.answer("❌ Hisobingizda yetarli tanga mavjud emas!", show_alert=True)
        await call.message.edit_text("❌ Tanga yetarli bo'lmagani uchun jarayon bekor qilindi.")
