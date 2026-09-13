from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from loader import ADMIN_IDS, WEBAPP_URL, logger
from states.quiz_states import (
    AddProjectStates, AddQuestionStates, AddQuestionsStates,
    DeleteQuestionStates, DeleteProjectStates, DeleteQuestionsBulkStates, AdminAuth
)
from database import (
    get_all_subjects, add_subject, add_question, get_questions_by_text,
    delete_question_db, delete_subject
)
import asyncpg
from loader import DATABASE_URL

router = Router()

# ==== HIDDEN ADMIN PANEL ====
@router.message(Command("adminpanel"))
async def cmd_admin_hidden(message: types.Message, state: FSMContext):
    # Admin bo'lmasa, javob qaytarmaymiz
    if not (ADMIN_IDS and str(message.from_user.id) in ADMIN_IDS):
        return

    await state.set_state(AdminAuth.waiting_for_password)

@router.message(AdminAuth.waiting_for_password)
async def process_admin_password(message: types.Message, state: FSMContext):
    # Faqat adminlar uchun
    if not (ADMIN_IDS and str(message.from_user.id) in ADMIN_IDS):
        logger.warning(f"Ruxsatsiz urinish: {message.from_user.id} ADMIN_IDS ro'yxatida yo'q.")
        await state.clear()
        return

    import os
    admin_pass = os.getenv("ADMIN_PASSWORD", "Str0ng@Adm1n#2026!")

    if message.text and message.text.strip() == admin_pass:
        kb = InlineKeyboardBuilder()
        web_url = WEBAPP_URL or "https://bilmli-bot-production.up.railway.app"
        admin_url = f"{web_url}/admin"
        kb.button(text="🔧 Admin Panelni Ochish", web_app=WebAppInfo(url=admin_url))
        
        await message.answer("✅ Admin panelga kirish ruxsat etildi.", reply_markup=kb.as_markup())
        logger.info(f"Admin panelga kirildi: {message.from_user.id}")
    else:
        # Noto'g'ri parol bo'lsa, indamaymiz
        logger.warning(f"Noto'g'ri parol kiritildi: {message.from_user.id}")
        pass
    await state.clear()

# ==== ADMIN HANDLERS (Legacy Text Commands Removed) ====
# The user moved all admin functionality to the Web App.
# Only the hidden /adminpanel command remains to access the Web App.

@router.message(F.photo, F.caption.startswith("/addpic"))
async def cmd_addpic(message: types.Message):
    from database import get_admins_db
    db_admins = await get_admins_db()
    is_admin = (ADMIN_IDS and str(message.from_user.id) in ADMIN_IDS) or message.from_user.id in db_admins
    if not is_admin:
        return

    caption = message.caption
    parts = caption.split("/addpic", 1)[1].strip().split("|")
    if len(parts) != 4:
        await message.answer("❌ Noto'g'ri format. To'g'ri format:\n/addpic fan_nomi | savol_matni | var1, var2, var3, var4 | to'g'ri_javob_raqami")
        return

    subject = parts[0].strip().lower()
    question = parts[1].strip()
    options_str = parts[2].strip()
    correct_idx_str = parts[3].strip()

    options = [opt.strip() for opt in options_str.split(",")]
    if len(options) != 4:
        await message.answer("❌ Variantlar aniq 4 ta bo'lishi kerak (vergul bilan ajrating)!")
        return

    if not correct_idx_str.isdigit() or not (1 <= int(correct_idx_str) <= 4):
        await message.answer("❌ To'g'ri javob raqami 1 dan 4 gacha bo'lgan son bo'lishi kerak!")
        return

    correct_option_id = int(correct_idx_str) - 1
    file_id = message.photo[-1].file_id

    await add_subject(subject)

    try:
        await add_question(
            subject=subject,
            question=question,
            options=options,
            correct_option_id=correct_option_id,
            created_by=message.from_user.id,
            image_url=file_id
        )
        await message.answer("✅ Rasmli savol bazaga muvaffaqiyatli qo'shildi!")
    except Exception as e:
        logger.error(f"Rasmli savol qo'shishda xato: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

@router.message(Command("addcoin", "coin"))
async def cmd_addcoin(message: types.Message):
    # Faqat adminlar uchun (env adminlar yoki DB adminlar)
    from database import get_admins_db, add_coins_db, get_user_by_identifier
    
    db_admins = await get_admins_db()
    is_admin = (ADMIN_IDS and str(message.from_user.id) in ADMIN_IDS) or message.from_user.id in db_admins
    if not is_admin:
        return

    # Argumentlarni tekshirish: /addcoin <user_id_yoki_username> <tanga_miqdori> [izoh]
    args = message.text.split(maxsplit=3)
    if len(args) < 3:
        await message.answer("⚠️ Noto'g'ri format.\nFoydalanish: `/coin <user_id yoki @username> <miqdor> [izoh]`\nMisol: `/coin @uzbdo -10 qoidabuzarlik`")
        return

    identifier, amount_str = args[1], args[2]
    comment = args[3] if len(args) > 3 else ""

    # Miqdor tekshiruvi
    try:
        amount = int(amount_str)
    except ValueError:
        await message.answer("❌ Tanga miqdori butun son bo'lishi kerak!")
        return

    # Foydalanuvchini bazadan qidirish
    user = await get_user_by_identifier(identifier)
    if not user:
        await message.answer(f"❌ Foydalanuvchi topilmadi ({identifier}).")
        return

    user_id = user["user_id"]

    # Tangani qo'shish
    success = await add_coins_db(user_id, amount)
    if success:
        updated_user = await get_user_by_identifier(str(user_id))
        new_coins = updated_user["coins"]
        name = updated_user["username"] or updated_user["first_name"] or f"ID:{user_id}"
        
        # Admin xabari
        action_text = "qo'shildi" if amount >= 0 else "ayirildi"
        await message.answer(
            f"✅ <b>{name}</b> (ID: <code>{user_id}</code>) hisobiga <b>{amount}</b> tanga {action_text}.\n"
            f"Hozirgi balansi: <b>{new_coins}</b> tanga 🪙",
            parse_mode="HTML"
        )
        
        # Foydalanuvchini xabardor qilish
        try:
            from loader import bot
            user_msg = f"🎁 Admin hisobingizga {amount} tanga qo'shdi!" if amount >= 0 else f"⚠️ Admin hisobingizdan {abs(amount)} tanga ayirib tashladi."
            if comment:
                user_msg += f"\n📝 Izoh: {comment}"
            user_msg += f"\nHozirgi balansingiz: <b>{new_coins}</b> tanga 🪙"
            
            await bot.send_message(user_id, user_msg, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Foydalanuvchiga xabar yuborishda xatolik (ID: {user_id}): {e}")
    else:
        await message.answer("❌ Tangani yangilashda xatolik yuz berdi.")

@router.callback_query(F.data.startswith("wd_approve_"))
async def process_wd_approve(call: types.CallbackQuery):
    from database import get_admins_db, update_withdrawal_status, get_connection
    from loader import ADMIN_IDS, bot
    
    # Admin tekshiruvi
    db_admins = await get_admins_db()
    is_admin = (ADMIN_IDS and str(call.from_user.id) in ADMIN_IDS) or call.from_user.id in db_admins
    if not is_admin:
        await call.answer("❌ Siz admin emassiz!", show_alert=True)
        return
        
    wid = int(call.data.split("_")[2])
    
    # Ariza holatini tekshirish
    async with await get_connection() as conn:
        wd = await conn.fetchrow("SELECT status, user_id, amount_coins, amount_money FROM withdrawals WHERE id=$1", wid)
        
    if not wd:
        await call.answer("❌ Ariza topilmadi!", show_alert=True)
        return
        
    if wd["status"] != "pending":
        await call.answer(f"⚠️ Ushbu ariza allaqachon ko'rib chiqilgan: {wd['status']}", show_alert=True)
        await call.message.edit_reply_markup(reply_markup=None)
        return
        
    # Bazada statusni yangilash
    await update_withdrawal_status(wid, "approved")
    await call.answer("✅ Ariza tasdiqlandi!", show_alert=True)
    
    # Xabarni yangilash
    new_text = call.message.html_text + f"\n\n✅ <b>Tasdiqlandi!</b> (Admin: @{call.from_user.username or call.from_user.id})"
    await call.message.edit_text(new_text, parse_mode="HTML", reply_markup=None)
    
    # Foydalanuvchini ogohlantirish
    try:
        await bot.send_message(
            wd["user_id"],
            f"🎉 <b>Pul yechish arizangiz tasdiqlandi!</b>\n\n"
            f"🪙 <b>Tanga:</b> {wd['amount_coins']} ➡️ <b>{wd['amount_money']:,} UZS</b>\n"
            f"Tez orada hisobingizga tushadi. Rahmat! 🙏",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Foydalanuvchiga tasdiqlash xabari yuborishda xatolik (ID: {wd['user_id']}): {e}")

@router.callback_query(F.data.startswith("wd_reject_"))
async def process_wd_reject(call: types.CallbackQuery):
    from database import get_admins_db, update_withdrawal_status, get_connection
    from loader import ADMIN_IDS, bot
    
    # Admin tekshiruvi
    db_admins = await get_admins_db()
    is_admin = (ADMIN_IDS and str(call.from_user.id) in ADMIN_IDS) or call.from_user.id in db_admins
    if not is_admin:
        await call.answer("❌ Siz admin emassiz!", show_alert=True)
        return
        
    wid = int(call.data.split("_")[2])
    
    # Ariza holatini tekshirish
    async with await get_connection() as conn:
        wd = await conn.fetchrow("SELECT status, user_id, amount_coins, amount_money FROM withdrawals WHERE id=$1", wid)
        
    if not wd:
        await call.answer("❌ Ariza topilmadi!", show_alert=True)
        return
        
    if wd["status"] != "pending":
        await call.answer(f"⚠️ Ushbu ariza allaqachon ko'rib chiqilgan: {wd['status']}", show_alert=True)
        await call.message.edit_reply_markup(reply_markup=None)
        return
        
    # Bazada statusni yangilash (bu funksiya tangalarni qaytaradi)
    await update_withdrawal_status(wid, "rejected")
    await call.answer("❌ Ariza rad etildi!", show_alert=True)
    
    # Xabarni yangilash
    new_text = call.message.html_text + f"\n\n❌ <b>Rad etildi!</b> (Admin: @{call.from_user.username or call.from_user.id})"
    await call.message.edit_text(new_text, parse_mode="HTML", reply_markup=None)
    
    # Foydalanuvchini ogohlantirish
    try:
        await bot.send_message(
            wd["user_id"],
            f"❌ <b>Pul yechish arizangiz rad etildi.</b>\n\n"
            f"🪙 <b>Tanga:</b> {wd['amount_coins']} tanga hisobingizga qaytarildi.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Foydalanuvchiga rad etish xabari yuborishda xatolik (ID: {wd['user_id']}): {e}")
