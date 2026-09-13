from aiogram import Router, types
from aiogram.filters import Command
import asyncpg
from loader import DATABASE_URL, bot, logger, CHANNEL_ID
from database import get_user_rank, get_group_rating, get_top_users, reset_all_coins, get_user_coins_and_rank, get_or_create_user, get_user_group_score_and_rank, get_global_rating_weekly, get_global_rating_monthly
from datetime import datetime

router = Router()

async def send_weekly_rating():
    if CHANNEL_ID is None:
        logger.warning("CHANNEL_ID not set; weekly rating skipped.")
        return

    top_users = await get_top_users(limit=10)
    if not top_users:
        if CHANNEL_ID:
            await bot.send_message(CHANNEL_ID, "❌ Bu vaqtda reyting uchun ma'lumot topilmadi.")
        return

    message = "🏆 <b>Haftalik TOP-10 reyting!</b>\n\n"
    for i, row in enumerate(top_users, start=1):
        uid = row["user_id"]
        username = row["username"]
        coins = row["coins"]
        name = f"@{username}" if username else f"ID:{uid}"
        message += f"{i}. {name} — {coins} 🪙\n"

    message += "\nYangi hafta boshlandi, hammaga omad! 🍀"
    await bot.send_message(CHANNEL_ID, message, parse_mode="HTML")
    await reset_all_coins()
    logger.info(f"[{datetime.now()}] ✅ Haftalik reyting yuborildi va tanga qayta tiklandi.")

@router.message(Command("grouprating"))
async def cmd_grouprating(message: types.Message):
    if message.chat.type == "private":
        await message.answer("❌ Bu komanda faqat guruhlarda ishlaydi!")
        return

    group_users = await get_group_rating(message.chat.id, limit=10)
    if not group_users:
        await message.answer("📈 Bu guruhda hali hech kim test yechmagan.")
        return

    text = "👥 <b>Guruhning TOP-10 reytingi!</b>\n\n"
    for i, row in enumerate(group_users, start=1):
        uid = row["user_id"]
        username = row["username"]
        score = row["group_score"]
        name = f"@{username}" if username else f"ID:{uid}"
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "▫️"
        text += f"{medal} {i}. {name} — {score} ball\n"

    # Userning guruhdagi o'rnini qo'shish
    user_id = message.from_user.id
    user_score, rank = await get_user_group_score_and_rank(message.chat.id, user_id)
    if rank is not None:
        text += f"\n────────────────────\n👤 <b>Siz:</b> {rank}-o'rin ({user_score} ball)"

    await message.answer(text, parse_mode="HTML")

@router.message(Command("rating"))
async def cmd_globalrating(message: types.Message):
    top_users = await get_top_users(limit=10)
    if not top_users:
        await message.answer("📈 Hali reyting shakllanmadi.")
        return

    text = "🌍 <b>Umumiy TOP-10 reyting!</b>\n\n"
    for i, row in enumerate(top_users, start=1):
        uid = row["user_id"]
        username = row["username"]
        coins = row["coins"]
        name = f"@{username}" if username else f"ID:{uid}"
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "▫️"
        text += f"{medal} {i}. {name} — {coins} 🪙\n"

    # Hozirgi foydalanuvchining o'z reytingini pastda ko'rsatish
    user_id = message.from_user.id
    # Foydalanuvchi ma'lumotlarini yangilash/yaratish
    await get_or_create_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name
    )
    user_coins, rank = await get_user_coins_and_rank(user_id)
    if rank is not None:
        text += f"\n────────────────────\n👤 <b>Siz:</b> {rank}-o'rin ({user_coins} 🪙)"

    await message.answer(text, parse_mode="HTML")

@router.message(Command("week"))
async def cmd_week(message: types.Message):
    top_users = await get_global_rating_weekly(limit=10)
    if not top_users:
        await message.answer("📉 Bu hafta hali hech kim test yechmagan.")
        return

    text = "🏆 <b>Haftalik TOP-10 reyting!</b>\n\n"
    for i, row in enumerate(top_users, start=1):
        uid = row["user_id"]
        username = row["username"]
        score = row["total_score"]
        name = f"@{username}" if username else row["first_name"] or f"ID:{uid}"
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "▫️"
        text += f"{medal} {i}. {name} — {score} ball\n"

    await message.answer(text, parse_mode="HTML")

@router.message(Command("month"))
async def cmd_month(message: types.Message):
    top_users = await get_global_rating_monthly(limit=10)
    if not top_users:
        await message.answer("📉 Bu oy hali hech kim test yechmagan.")
        return

    text = "🏆 <b>Oylik TOP-10 reyting!</b>\n\n"
    for i, row in enumerate(top_users, start=1):
        uid = row["user_id"]
        username = row["username"]
        score = row["total_score"]
        name = f"@{username}" if username else row["first_name"] or f"ID:{uid}"
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "▫️"
        text += f"{medal} {i}. {name} — {score} ball\n"

    await message.answer(text, parse_mode="HTML")
