# 🎯 BilimliBot - Telegram Test Bot

Telegram orqali test yechish uchun ishlatiladigan bot. PostgreSQL ma'lumotlar bazasidan foydalanadi.

## 📋 Imtiyozlar

- 📚 Ko'p fanlardan testlar (Matematika, Fizika, Ingliz tili, Rus tili va boshqalar)
- 🏆 Umumiy va guruh reytinglari
- 🪙 Tanga tizimi (har bir to'g'ri javob = 1 tanga)
- 🔄 Haftalik reyting va tanga qayta tiklanadigan tizim
- 👨‍💼 Admin panel (savol/fan qo'shish/o'chirish)
- 🎨 Poll orqali interaktiv test javoblari

## 🚀 O'rnatish

### 1. Repositoryni klonlash

```bash
git clone <repository-url>
cd bilimlibot
```

### 2. Virtual environment yaratish

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Kerakli paketlarni o'rnatish

```bash
pip install -r requirements.txt
```

### 4. Environment sozlamalari

`.env.example` faylini `.env` ga nusxalang va qatorlarni to'ldiring:

```bash
cp .env.example .env
```

`.env` faylini oching va quyidagilarni to'ldiring:

```env
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
CHANNEL_ID=your_channel_id_here
DATABASE_URL=postgresql://user:password@localhost:5432/bilimlibot
```

**BOT_TOKEN:** [@BotFather](https://t.me/botfather) dan olingan bot tokeningiz

**ADMIN_IDS:** Admin bo'lishi kerak bo'lgan foydalanuvchilar ID raqamlari (vergul bilan ajratilgan)

**CHANNEL_ID:** Haftalik reyting yuboriladigan kanal ID raqami

**DATABASE_URL:** PostgreSQL ma'lumotlar bazasi ulanishi

## 🗄️ Ma'lumotlar bazasi

Bot PostgreSQL ishlatadi. Database avtomatik yaratiladi dastur ishga tushganda.

### Railway da sozlash

1. Railway akkauntida yangi PostgreSQL ma'lumotlar bazasi yarating
2. `DATABASE_URL` ni nusxalang
3. `.env` faylida `DATABASE_URL` ni o'rnating

```env
DATABASE_URL=postgresql://postgres:password@host.railway.app:port/railway
```

### Lokal test qilish

PostgreSQL lokalni o'rnating va yangi database yarating:

```sql
CREATE DATABASE bilimlibot;
```

Keyin `.env` faylida local database URL ni ko'rsating:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/bilimlibot
```

## ▶️ Botni ishga tushirish

### Lokal kompyuterdan

```bash
python main.py
```

### Railway da deploy qilish

1. [Railway.app](https://railway.app) da akkaunt yarating
2. "New Project" ni tanlang va GitHub repositorynizi ulang
3. PostgreSQL ma'lumotlar bazasini qo'shing:
   - "New" → "Database" → "Add PostgreSQL"
   - PostgreSQL ni tanlab yarating
4. Bot uchun environment variables sozlang:
   - Settings → Variables → Add Variable
   - Quyidagi o'zgaruvchilarni qo'shing:
     - `BOT_TOKEN`: Telegram bot tokeningiz
     - `ADMIN_IDS`: Admin ID raqamlari (vergul bilan ajratilgan)
     - `CHANNEL_ID`: Kanal ID (ixtiyoriy)
     - `DATABASE_URL`: PostgreSQL connection string (Railway PostgreSQL'dan avtomatik yaratiladi)
5. Deploy qilish:
   - Railway avtomatik `requirements.txt` ni o'qib, paketlarni o'rnatadi
   - Bot `python main.py` buyrug'i bilan ishga tushadi
   - Logs → Deploy Logs da bot ishga tushganini ko'rasiz

**Muhim:** Railway PostgreSQL `DATABASE_URL` ni avtomatik yaratadi va environment variable sifatida qo'shadi.

## 📜 Bot komandalari

### Foydalanuvchilar uchun

- `/start` - Botni boshlash va fanlar ro'yxati
- `/quiz` - Barcha fanlardan aralash (random) testlar
- `/quiz<fan_nomi>` - Maxsus fan bo'yicha test boshlash (masalan: `/quizeng`, `/quiztarix`, `/quizgeo`, `/quiztez`)
- `/rating` - Umumiy TOP-10 reyting
- `/grouprating` - Guruhning TOP-10 reytingi (faqat guruhlarda)
- `/cancel` - Faol testni bekor qilish
- `/next` - Keyingi savolga o'tish (faqat vaqtsiz/off rejimdagi testlar uchun)

### Adminlar uchun

- `/adminpanel` - Boshqaruv veb-paneliga kirish tugmasini olish (faqat tizim adminlari uchun)
- `/addpic` - Rasmli savollarni guruh/bot orqali qo'shish

## 📚 Savol qo'shish usullari

### 1. Veb Admin Panel orqali (Tavsiya etiladi)
`/adminpanel` yordamida kirib:
- Fanlarni boshqarish (qo'shish/o'chirish).
- Savollarni qulay veb interfeys orqali qo'shish/o'chirish.
- Savollarni bulk (ommaviy) formatda matn orqali yuklash.

### 2. Rasmli savollarni bot orqali qo'shish
Rasm yuborilayotgan paytda rasm izohiga (caption) quyidagi formatda yozing:
```
/addpic fan_nomi | savol_matni | var1, var2, var3, var4 | to'g'ri_javob_raqami(1-4)
```

**Misol:**
```
/addpic tarix | Suratdagi shaxs kim? | Amir Temur, Bobur, Al-Xorazmiy, Ibn Sino | 1
```

## 🔄 Haftalik reyting

Har dushanba kuni soat 08:00 da (Toshkent vaqti bilan) kanalga haftalik reyting yuboriladi va foydalanuvchilarning barcha tangalari (coins) qayta tiklanadi.

## 📝 Fayllar

- `main.py` - Asosiy bot va dasturni ishga tushirish fayli
- `database.py` - Ma'lumotlar bazasi bilan ishlash funksiyalari
- `web_server.py` - Admin panel va API uchun veb-server kodlari
- `loader.py` - Bot va o'zgaruvchilarni initsializatsiya qilish
- `custom_subjects.json` - Qo'shimcha mavjud fanlar ro'yxati
- `requirements.txt` - Kerakli Python kutubxonalari ro'yxati

## 🛠️ Texnologiyalar

- **Python 3.10+**
- **aiogram 3.13.1** - Telegram Bot API
- **asyncpg 0.30.0** - PostgreSQL async driver
- **APScheduler 3.10.4** - Vazifalar rejalashtirish
- **PostgreSQL** - Ma'lumotlar bazasi

## 📄 Mualliflik huquqi

Bu loyiha ochiq manba dastur sifatida taqdim etilgan.

## 🤝 Yordam

Muammo bo'lsa, issue oching yoki pull request qiling.

