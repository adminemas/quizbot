import asyncio
import logging
from datetime import datetime
from aiogram import types
from loader import bot, dp, logger
from database import init_db, ping_db
from handlers.users import start, quiz, ranking, unknown
from handlers.admin import panel
#test bilmayman nechichi ammo jonga tegdi

# Import web server if needed
# from web_server import run_web_server

async def main():
    # 1. Database init
    await init_db()
    
    # 2. Start Web Server (background)
    try:
        from web_server import run_web_server
        asyncio.create_task(run_web_server())
    except Exception as e:
        logger.error(f"Failed to start web server: {e}")

    # 4. Include Routers
    dp.include_router(start.router)
    dp.include_router(quiz.router)
    dp.include_router(ranking.router)
    from handlers.users import transfer
    dp.include_router(transfer.router)
    dp.include_router(panel.router)
    
    # 5. Catch-all router (MUST BE LAST)
    dp.include_router(unknown.router)


    # 6. Scheduler Setup
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from handlers.users.ranking import send_weekly_rating
    
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(send_weekly_rating, "cron", day_of_week="mon", hour=8, minute=0)
    scheduler.add_job(ping_db, "interval", minutes=5)
    scheduler.start()

    logger.info(f"[{datetime.now()}] Bot ishga tushdi ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
