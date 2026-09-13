from aiogram import Router, types
from aiogram import F

router = Router()

@router.message()
async def catch_all_unknown(message: types.Message):
    # Agar boshqa hech qanday handler ushlamasa, shunga tushadi
    pass
