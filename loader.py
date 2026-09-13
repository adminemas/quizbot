import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [aid.strip() for aid in os.getenv("ADMIN_IDS", "").split(",") if aid.strip()]
CHANNEL_ID = os.getenv("CHANNEL_ID")
raw_webapp = (os.getenv("WEBAPP_URL") or "").strip().strip('"').strip("'")
if raw_webapp:
    if raw_webapp.startswith("http://"):
        raw_webapp = "https://" + raw_webapp[7:]
    elif not raw_webapp.startswith("https://"):
        raw_webapp = "https://" + raw_webapp
    WEBAPP_URL = raw_webapp.rstrip("/")
else:
    WEBAPP_URL = None
DATABASE_URL = os.getenv("DATABASE_URL")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi! .env faylida BOT_TOKEN ni sozlang.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
