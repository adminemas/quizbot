import os
import logging
import re
from typing import Optional
from dotenv import load_dotenv

# --- ENV yuklash ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Determine DB type
IS_SQLITE = False
if not DATABASE_URL or DATABASE_URL.startswith("sqlite"):
    IS_SQLITE = True
    DB_FILE = "bilimlibot.db"
    if DATABASE_URL and DATABASE_URL.startswith("sqlite:///"):
        DB_FILE = DATABASE_URL.replace("sqlite:///", "")
else:
    DB_FILE = None

import aiosqlite
import sqlite3
import asyncpg

# --- Logging setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db_pool = None

class PostgresConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn

    async def execute(self, query: str, *args):
        return await self.conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        return await self.conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        return await self.conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        return await self.conn.fetchval(query, *args)

    def transaction(self):
        return self.conn.transaction()

class AioSQLiteConnectionWrapper:
    def __init__(self, conn: aiosqlite.Connection):
        self.conn = conn

    def _convert_query(self, query: str) -> str:
        # Convert $1, $2, ... placeholders to ?1, ?2, ...
        q = re.sub(r'\$(\d+)', r'?\1', query)
        
        # PostgreSQL specific ILIKE to SQLite LIKE
        q = re.sub(r'\bILIKE\b', 'LIKE', q, flags=re.IGNORECASE)
        
        # PostgreSQL specific CASTs: id::text to CAST(id AS TEXT)
        q = re.sub(r'(\w+)::text', r'CAST(\1 AS TEXT)', q, flags=re.IGNORECASE)
        
        # NOW() - INTERVAL 'X days' to datetime('now', '-X days')
        q = re.sub(r"NOW\(\)\s*-\s*INTERVAL\s+'(\d+)\s+days'", r"datetime('now', '-\1 days')", q, flags=re.IGNORECASE)
        
        # NOW() to datetime('now')
        q = re.sub(r'\bNOW\(\)', "datetime('now')", q, flags=re.IGNORECASE)
        
        # GREATEST(0, val) to max(0, val)
        q = re.sub(r'\bGREATEST\b', 'max', q, flags=re.IGNORECASE)
        
        return q

    async def execute(self, query: str, *args):
        q = self._convert_query(query)
        cursor = await self.conn.execute(q, args)
        await self.conn.commit()
        return cursor

    async def fetch(self, query: str, *args):
        q = self._convert_query(query)
        async with self.conn.execute(q, args) as cursor:
            return await cursor.fetchall()

    async def fetchrow(self, query: str, *args):
        q = self._convert_query(query)
        async with self.conn.execute(q, args) as cursor:
            return await cursor.fetchone()

    async def fetchval(self, query: str, *args):
        q = self._convert_query(query)
        async with self.conn.execute(q, args) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

    async def transaction(self):
        class SQLiteTransaction:
            def __init__(self, conn):
                self.conn = conn
            async def __aenter__(self):
                await self.conn.execute("BEGIN TRANSACTION")
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                if exc_type:
                    await self.conn.rollback()
                else:
                    await self.conn.commit()
        return SQLiteTransaction(self.conn)

class GetConnectionContext:
    def __init__(self):
        self.sqlite_conn = None
        self.pg_conn_context = None
        self.pg_conn = None

    async def __aenter__(self):
        global db_pool
        if IS_SQLITE:
            self.sqlite_conn = await aiosqlite.connect(DB_FILE)
            self.sqlite_conn.row_factory = aiosqlite.Row
            await self.sqlite_conn.execute("PRAGMA foreign_keys = ON")
            return AioSQLiteConnectionWrapper(self.sqlite_conn)
        else:
            if db_pool is None:
                db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=30)
            self.pg_conn_context = db_pool.acquire()
            self.pg_conn = await self.pg_conn_context.__aenter__()
            return PostgresConnectionWrapper(self.pg_conn)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if IS_SQLITE:
            if self.sqlite_conn:
                await self.sqlite_conn.close()
        else:
            if self.pg_conn_context:
                await self.pg_conn_context.__aexit__(exc_type, exc_val, exc_tb)

async def get_connection():
    return GetConnectionContext()

# === DASTLABKI INITSIALIZATSIYA ===
async def init_db():
    """Ma'lumotlar bazasini yaratish va jadvallarni sozlash"""
    async with await get_connection() as conn:
        if IS_SQLITE:
            # --- USERS ---
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    total_score INTEGER DEFAULT 0,
                    coins INTEGER DEFAULT 0
                )
            ''')

            # --- QUIZ_SESSIONS ---
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS quiz_sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # --- USER_ANSWERS ---
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER REFERENCES quiz_sessions(session_id),
                    user_id INTEGER REFERENCES users(user_id),
                    question_number INTEGER,
                    is_correct BOOLEAN,
                    score INTEGER DEFAULT 0,
                    group_score INTEGER DEFAULT 0,
                    question_id INTEGER,
                    UNIQUE(session_id, user_id, question_number)
                )
            ''')
            try:
                await conn.execute("ALTER TABLE user_answers ADD COLUMN question_id INTEGER")
            except Exception:
                pass

            # --- QUESTIONS ---
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    question TEXT NOT NULL,
                    option1 TEXT NOT NULL,
                    option2 TEXT NOT NULL,
                    option3 TEXT NOT NULL,
                    option4 TEXT NOT NULL,
                    correct_option_id INTEGER NOT NULL,
                    image_url TEXT,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # --- CATEGORIES ---
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    emoji TEXT NOT NULL,
                    slug TEXT UNIQUE NOT NULL,
                    sort_order INTEGER DEFAULT 0
                )
            ''')
        else:
            # --- USERS ---
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    total_score INTEGER DEFAULT 0,
                    coins INTEGER DEFAULT 0
                )
            ''')

            # --- QUIZ_SESSIONS ---
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS quiz_sessions (
                    session_id SERIAL PRIMARY KEY,
                    chat_id BIGINT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # --- USER_ANSWERS ---
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_answers (
                    id SERIAL PRIMARY KEY,
                    session_id INTEGER REFERENCES quiz_sessions(session_id),
                    user_id BIGINT REFERENCES users(user_id),
                    question_number INTEGER,
                    is_correct BOOLEAN,
                    score INTEGER DEFAULT 0,
                    group_score INTEGER DEFAULT 0,
                    question_id INTEGER,
                    UNIQUE(session_id, user_id, question_number)
                )
            ''')
            try:
                await conn.execute("ALTER TABLE user_answers ADD COLUMN question_id INTEGER")
            except Exception:
                pass

            # --- QUESTIONS ---
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id SERIAL PRIMARY KEY,
                    subject TEXT NOT NULL,
                    question TEXT NOT NULL,
                    option1 TEXT NOT NULL,
                    option2 TEXT NOT NULL,
                    option3 TEXT NOT NULL,
                    option4 TEXT NOT NULL,
                    correct_option_id INTEGER NOT NULL,
                    image_url TEXT,
                    created_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # --- CATEGORIES ---
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    emoji TEXT NOT NULL,
                    slug TEXT UNIQUE NOT NULL,
                    sort_order INTEGER DEFAULT 0
                )
            ''')

        # --- SEED CATEGORIES (Works for both) ---
        await conn.execute("INSERT INTO categories (name, emoji, slug, sort_order) VALUES ('Maktab Fanlari', '🏫', 'school', 1) ON CONFLICT (slug) DO NOTHING")
        await conn.execute("INSERT INTO categories (name, emoji, slug, sort_order) VALUES ('Ijtimoiy Fanlar', '🌎', 'social', 2) ON CONFLICT (slug) DO NOTHING")
        await conn.execute("INSERT INTO categories (name, emoji, slug, sort_order) VALUES ('Tabiiy Fanlar', '🧪', 'natural', 3) ON CONFLICT (slug) DO NOTHING")
        await conn.execute("INSERT INTO categories (name, emoji, slug, sort_order) VALUES ('IT & Dasturlash', '💻', 'it', 4) ON CONFLICT (slug) DO NOTHING")
        await conn.execute("INSERT INTO categories (name, emoji, slug, sort_order) VALUES ('Tillar', '🌐', 'languages', 5) ON CONFLICT (slug) DO NOTHING")
        await conn.execute("INSERT INTO categories (name, emoji, slug, sort_order) VALUES ('Sport', '🏀', 'sports', 6) ON CONFLICT (slug) DO NOTHING")

        # --- SUBJECTS ---
        if IS_SQLITE:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS subjects (
                    key TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
                    name TEXT,
                    emoji TEXT DEFAULT '📚',
                    is_popular BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
        else:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS subjects (
                    key TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Add columns backwards-compatibly for PostgreSQL
            try:
                await conn.execute("ALTER TABLE subjects ADD COLUMN category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL")
            except Exception:
                pass
            try:
                await conn.execute("ALTER TABLE subjects ADD COLUMN name TEXT")
            except Exception:
                pass
            try:
                await conn.execute("ALTER TABLE subjects ADD COLUMN emoji TEXT DEFAULT '📚'")
            except Exception:
                pass
            try:
                await conn.execute("ALTER TABLE subjects ADD COLUMN is_popular BOOLEAN DEFAULT FALSE")
            except Exception:
                pass
            try:
                await conn.execute("ALTER TABLE subjects ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
            except Exception:
                pass

        # --- SEED DEFAULT SUBJECTS ---
        school_id = await conn.fetchval("SELECT id FROM categories WHERE slug = 'school'")
        social_id = await conn.fetchval("SELECT id FROM categories WHERE slug = 'social'")
        natural_id = await conn.fetchval("SELECT id FROM categories WHERE slug = 'natural'")
        languages_id = await conn.fetchval("SELECT id FROM categories WHERE slug = 'languages'")
        sports_id = await conn.fetchval("SELECT id FROM categories WHERE slug = 'sports'")

        async def seed_subject(key, name, cat_id, emoji, is_pop=False):
            await conn.execute('''
                INSERT INTO subjects (key, name, category_id, emoji, is_popular)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (key) DO UPDATE
                SET name = $2, category_id = $3, emoji = $4, is_popular = $5
            ''', key, name, cat_id, emoji, is_pop)

        await seed_subject('tarix', 'Tarix', social_id, '🏛', True)
        await seed_subject('geo', 'Geografiya', social_id, '🗺', True)
        await seed_subject('fazo', 'Astronomiya', natural_id, '🌠')
        await seed_subject('eng', 'Ingliz tili', languages_id, '🇬🇧', True)
        await seed_subject('spo', 'Sport', sports_id, '🏅')
        await seed_subject('til', 'Tilshunoslik', languages_id, '✍️')
        await seed_subject('tez', 'Tezkor test', school_id, '⚡')
        await seed_subject('math', 'Matematika', school_id, '🧮', True)
        await seed_subject('physics', 'Fizika', natural_id, '⚛️')
        await seed_subject('english', 'English Advanced', languages_id, '🇬🇧')
        await seed_subject('russian', 'Rus tili', languages_id, '🇷🇺')

        # --- WITHDRAWALS ---
        if IS_SQLITE:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS withdrawals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(user_id),
                    amount_coins INTEGER NOT NULL,
                    amount_money INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS withdrawals (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    amount_coins INTEGER NOT NULL,
                    amount_money INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

        # --- SETTINGS ---
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')

        # --- ADMINS ---
        if IS_SQLITE:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    user_id BIGINT PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # Default settings
        await conn.execute("INSERT INTO settings (key, value) VALUES ('coin_rate', '100') ON CONFLICT DO NOTHING")
        await conn.execute("INSERT INTO settings (key, value) VALUES ('min_withdrawal', '1000') ON CONFLICT DO NOTHING")

        # Close any active quiz sessions left open from previous runs
        if IS_SQLITE:
            await conn.execute("UPDATE quiz_sessions SET is_active=0 WHERE is_active=1")
        else:
            await conn.execute("UPDATE quiz_sessions SET is_active=FALSE WHERE is_active=TRUE")

    logger.info("✅ Baza yaratildi va boshlang'ich sozlamalar kiritildi!")

async def ping_db():
    """Yengil keepalive: bazaga ulanish va SELECT 1 bajarish."""
    try:
        async with await get_connection() as conn:
            await conn.execute('SELECT 1')
        logger.debug("DB keepalive OK")
    except Exception as e:
        logger.warning(f"DB keepalive xato: {e}")

# === SUBJECTS FUNKSIYALARI ===
async def add_subject(key: str):
    key = (key or "").strip().lower()
    if not key:
        raise ValueError("Fan nomi bo'sh bo'lmasligi kerak")
    async with await get_connection() as conn:
        await conn.execute('''
            INSERT INTO subjects (key) VALUES ($1)
            ON CONFLICT (key) DO NOTHING
        ''', key)

async def delete_subject(key: str):
    key = (key or "").strip().lower()
    async with await get_connection() as conn:
        await conn.execute('DELETE FROM subjects WHERE key = $1', key)
        await conn.execute('DELETE FROM questions WHERE subject = $1', key)

async def get_all_subjects():
    async with await get_connection() as conn:
        rows = await conn.fetch('SELECT key FROM subjects ORDER BY key ASC')
        return [r['key'] for r in rows]

# === USER FUNKSIYALARI ===
async def get_or_create_user(user_id: int, username=None, first_name=None, last_name=None):
    async with await get_connection() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", user_id)

        if not user:
            await conn.execute(
                "INSERT INTO users (user_id, username, first_name, last_name) VALUES ($1, $2, $3, $4)",
                user_id, username, first_name, last_name
            )
            logger.info(f"🆕 Yangi foydalanuvchi yaratildi: {user_id}")
            user = await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", user_id)
        else:
            if username or first_name:
                await conn.execute("""
                    UPDATE users SET username=$2, first_name=$3, last_name=$4 WHERE user_id=$1
                """, user_id, username, first_name, last_name)

        return user

async def get_user(user_id: int):
    async with await get_connection() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", user_id)
        return row

async def get_user_by_identifier(identifier: str):
    async with await get_connection() as conn:
        if identifier.startswith('@'):
            username = identifier[1:].lower()
            return await conn.fetchrow("SELECT * FROM users WHERE LOWER(username)=$1", username)
        elif identifier.isdigit():
            return await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", int(identifier))
    return None

async def transfer_coins(from_user_id: int, to_user_id: int, amount: int) -> bool:
    async with await get_connection() as conn:
        async with conn.transaction():
            from_coins = await conn.fetchval("SELECT coins FROM users WHERE user_id=$1", from_user_id)
            if from_coins is None or from_coins < amount:
                return False
            await conn.execute("UPDATE users SET coins = coins - $1 WHERE user_id=$2", amount, from_user_id)
            await conn.execute("UPDATE users SET coins = coins + $1 WHERE user_id=$2", amount, to_user_id)
            return True

# === QUIZ SESSION FUNKSIYALARI ===
async def create_quiz_session(chat_id: int):
    async with await get_connection() as conn:
        if IS_SQLITE:
            await conn.execute(
                "INSERT INTO quiz_sessions (chat_id) VALUES ($1)",
                chat_id
            )
            cursor = await conn.execute("SELECT last_insert_rowid()")
            row = await cursor.fetchone()
            session_id = row[0] if row else None
        else:
            session_id = await conn.fetchval(
                "INSERT INTO quiz_sessions (chat_id) VALUES ($1) RETURNING session_id",
                chat_id
            )
        logger.info(f"🟢 Yangi sessiya yaratildi: ID={session_id}")
        return session_id

async def close_session(session_id: int):
    async with await get_connection() as conn:
        if IS_SQLITE:
            await conn.execute("UPDATE quiz_sessions SET is_active=0 WHERE session_id=$1", session_id)
        else:
            await conn.execute("UPDATE quiz_sessions SET is_active=FALSE WHERE session_id=$1", session_id)
        logger.info(f"🔴 Sessiya yopildi: ID={session_id}")

# === ANSWER / SCORE FUNKSIYALARI ===
async def save_user_answer(session_id: int, user_id: int, question_number: int, is_correct: bool, group_score: int = 0, question_id: int = None):
    score = 1 if is_correct else 0
    coin_score = 1 if is_correct else 0
    await get_or_create_user(user_id)
    async with await get_connection() as conn:
        
        # Anti-Cheat: check if they answered this question correctly in ANY other session
        if is_correct and question_id is not None:
            has_answered = await conn.fetchval('''
                SELECT 1 FROM user_answers
                WHERE user_id = $1 AND question_id = $2 AND is_correct = TRUE AND session_id != $3
                LIMIT 1
            ''', user_id, question_id, session_id)
            if has_answered:
                coin_score = 0  # no coins for repeat, but score stays 1 for global rating
                
        existing = await conn.fetchrow('''
            SELECT is_correct, score FROM user_answers
            WHERE session_id=$1 AND user_id=$2 AND question_number=$3
        ''', session_id, user_id, question_number)

        if existing:
            old_is_correct, old_score = existing["is_correct"], existing["score"]
            await conn.execute('''
                UPDATE user_answers
                SET is_correct=$1, score=$2, group_score=$3, question_id=$4
                WHERE session_id=$5 AND user_id=$6 AND question_number=$7
            ''', is_correct, score, group_score, question_id, session_id, user_id, question_number)
            score_diff = score - old_score
            # Assumes old_score also reflected whether they got a coin
            coin_diff = coin_score - old_score 
        else:
            await conn.execute('''
                INSERT INTO user_answers (session_id, user_id, question_number, is_correct, score, group_score, question_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''', session_id, user_id, question_number, is_correct, score, group_score, question_id)
            score_diff = score
            coin_diff = coin_score

        if score_diff != 0 or coin_diff != 0:
            await conn.execute('''
                UPDATE users
                SET total_score = GREATEST(0, total_score + $1), coins = GREATEST(0, coins + $2)
                WHERE user_id = $3
            ''', score_diff, coin_diff, user_id)

async def get_session_results(session_id: int):
    async with await get_connection() as conn:
        rows = await conn.fetch('''
            SELECT u.user_id, u.username, u.first_name, SUM(ua.score) AS total_score
            FROM user_answers ua
            JOIN users u ON ua.user_id = u.user_id
            WHERE ua.session_id=$1
            GROUP BY u.user_id
            ORDER BY total_score DESC
        ''', session_id)
        return rows

async def get_global_rating(limit: int = 10, offset: int = 0):
    async with await get_connection() as conn:
        rows = await conn.fetch('''
            SELECT user_id, username, first_name, total_score
            FROM users ORDER BY total_score DESC LIMIT $1 OFFSET $2
        ''', limit, offset)
        return rows

async def get_global_rating_weekly(limit: int = 10):
    async with await get_connection() as conn:
        rows = await conn.fetch('''
            SELECT u.user_id, u.username, u.first_name, SUM(ua.score) AS total_score
            FROM user_answers ua
            JOIN quiz_sessions qs ON ua.session_id = qs.session_id
            JOIN users u ON ua.user_id = u.user_id
            WHERE qs.created_at > NOW() - INTERVAL '7 days'
            GROUP BY u.user_id, u.username, u.first_name
            ORDER BY total_score DESC
            LIMIT $1
        ''', limit)
        return rows

async def get_global_rating_monthly(limit: int = 10):
    async with await get_connection() as conn:
        rows = await conn.fetch('''
            SELECT u.user_id, u.username, u.first_name, SUM(ua.score) AS total_score
            FROM user_answers ua
            JOIN quiz_sessions qs ON ua.session_id = qs.session_id
            JOIN users u ON ua.user_id = u.user_id
            WHERE qs.created_at > NOW() - INTERVAL '30 days'
            GROUP BY u.user_id, u.username, u.first_name
            ORDER BY total_score DESC
            LIMIT $1
        ''', limit)
        return rows

# === SAVOL QO‘SHISH ===
async def add_question(subject, question, options, correct_option_id, created_by=None, image_url=None):
    if len(options) != 4:
        raise ValueError("❌ 4 ta variant bo'lishi kerak!")

    async with await get_connection() as conn:
        await conn.execute('''
            INSERT INTO questions (
                subject, question, option1, option2, option3, option4,
                correct_option_id, created_by, image_url
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
        ''', subject, question, *options, correct_option_id, created_by, image_url)
        logger.info(f"➕ Yangi savol qo‘shildi: {subject} | {question}")

# === SAVOLLARNI O‘QISH ===
async def get_questions(subject: Optional[str] = None, limit: int = 20):
    async with await get_connection() as conn:
        if subject:
            rows = await conn.fetch('''
                SELECT * FROM questions WHERE subject=$1 ORDER BY RANDOM() LIMIT $2
            ''', subject, limit)
        else:
            rows = await conn.fetch('SELECT * FROM questions ORDER BY RANDOM() LIMIT $1', limit)

        return [
            {
                "id": r["id"],
                "subject": r["subject"],
                "question": r["question"],
                "options": [r["option1"], r["option2"], r["option3"], r["option4"]],
                "correct_option_id": r["correct_option_id"],
                "image_url": r["image_url"]
            } for r in rows
        ]

async def search_questions_db(q: str, subject: Optional[str] = None, limit: int = 50):
    async with await get_connection() as conn:
        q_str = f'%{q}%'
        if subject:
            rows = await conn.fetch('''
                SELECT * FROM questions 
                WHERE subject=$1 AND (question ILIKE $2 OR CAST(id AS TEXT) = $3)
                ORDER BY id DESC LIMIT $4
            ''', subject, q_str, q, limit)
        else:
            rows = await conn.fetch('''
                SELECT * FROM questions 
                WHERE question ILIKE $1 OR CAST(id AS TEXT) = $2
                ORDER BY id DESC LIMIT $3
            ''', q_str, q, limit)
        return rows

async def delete_question_db(qid: int):
    async with await get_connection() as conn:
        await conn.execute('DELETE FROM questions WHERE id=$1', qid)

# === SAVOLLAR SONINI O‘LCHASH ===
async def get_questions_count(subject: Optional[str] = None):
    async with await get_connection() as conn:
        if subject:
            count = await conn.fetchval('SELECT COUNT(*) FROM questions WHERE subject=$1', subject)
        else:
            count = await conn.fetchval('SELECT COUNT(*) FROM questions')
        return count or 0

# === GURUH REYTINGI ===
async def get_group_rating(chat_id: int, limit: int = 10):
    async with await get_connection() as conn:
        rows = await conn.fetch('''
            SELECT u.user_id, u.username, u.first_name, SUM(ua.group_score) AS group_score
            FROM user_answers ua
            JOIN users u ON ua.user_id = u.user_id
            JOIN quiz_sessions qs ON ua.session_id = qs.session_id
            WHERE qs.chat_id=$1
            GROUP BY u.user_id
            ORDER BY group_score DESC
            LIMIT $2
        ''', chat_id, limit)
        return rows

async def get_user_group_score_and_rank(chat_id: int, user_id: int):
    async with await get_connection() as conn:
        row = await conn.fetchrow('''
            SELECT SUM(ua.group_score) AS score
            FROM user_answers ua
            JOIN quiz_sessions qs ON ua.session_id = qs.session_id
            WHERE qs.chat_id=$1 AND ua.user_id=$2
        ''', chat_id, user_id)
        
        user_score = row["score"] if row and row["score"] else 0
        
        if user_score > 0:
            count = await conn.fetchval('''
                SELECT COUNT(*) FROM (
                    SELECT SUM(ua.group_score) AS score
                    FROM user_answers ua
                    JOIN quiz_sessions qs ON ua.session_id = qs.session_id
                    WHERE qs.chat_id=$1
                    GROUP BY ua.user_id
                    HAVING SUM(ua.group_score) > $2
                ) as t
            ''', chat_id, user_score)
            rank = count + 1 if count is not None else 1
        else:
            rank = None
            
        return user_score, rank

# === JAMI FOYDALANUVCHILAR SONI ===
async def get_total_users_count():
    async with await get_connection() as conn:
        count = await conn.fetchval('SELECT COUNT(*) FROM users')
        return count or 0

async def get_active_users_7days():
    async with await get_connection() as conn:
        count = await conn.fetchval("""
            SELECT COUNT(DISTINCT user_id) FROM user_answers
            WHERE session_id IN (
                SELECT session_id FROM quiz_sessions 
                WHERE created_at > NOW() - INTERVAL '7 days'
            )
        """)
        return count or 0

async def get_user_stats(user_id: int):
    async with await get_connection() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", user_id)
        stats = await conn.fetchrow("""
            SELECT 
                SUM(CASE WHEN is_correct = TRUE THEN 1 ELSE 0 END) as correct,
                SUM(CASE WHEN is_correct = FALSE THEN 1 ELSE 0 END) as incorrect,
                COUNT(*) as total
            FROM user_answers WHERE user_id=$1
        """, user_id)
        
        if not stats:
            stats = {"correct": 0, "incorrect": 0, "total": 0}
            
        rank = 0
        if user:
             cnt = await conn.fetchval('SELECT COUNT(*) FROM users WHERE total_score > $1', user['total_score'])
             rank = cnt + 1 if cnt is not None else 1

        return {
            "score": user['total_score'] if user else 0,
            "coins": user['coins'] if user else 0,
            "correct": stats['correct'] or 0,
            "incorrect": stats['incorrect'] or 0,
            "total": stats['total'] or 0,
            "rank": rank,
            "first_name": user['first_name'] if user else "",
            "username": user['username'] if user else ""
        }

# === FANLAR BO'YICHA SAVOL STATISTIKASI ===
async def get_subject_question_counts():
    async with await get_connection() as conn:
        subject_rows = await conn.fetch('SELECT key AS code, key AS name FROM subjects ORDER BY key')
        counts = await conn.fetch('''
            SELECT subject, COUNT(*) as count 
            FROM questions 
            GROUP BY subject
        ''')

        results = {r['subject']: r['count'] for r in counts}
        
        stats = []
        for row in subject_rows:
            code = row['code']
            name = row['name']
            count = results.get(code, 0)
            stats.append({'code': code, 'name': name, 'count': count})
            
        return stats

# === TOP FOYDALANUVCHILAR ===
async def get_top_users(limit=10):
    async with await get_connection() as conn:
        rows = await conn.fetch('SELECT user_id, username, coins FROM users ORDER BY coins DESC LIMIT $1', limit)
        return rows

async def reset_all_coins():
    async with await get_connection() as conn:
        await conn.execute("UPDATE users SET coins=0")

# === SETTINGS & WITHDRAWALS & ADMINS ===
async def get_setting(key: str, default=None):
    async with await get_connection() as conn:
        val = await conn.fetchval('SELECT value FROM settings WHERE key=$1', key)
        return val if val is not None else default

async def set_setting(key: str, value: str):
    async with await get_connection() as conn:
        await conn.execute("""
            INSERT INTO settings (key, value) VALUES ($1, $2)
            ON CONFLICT (key) DO UPDATE SET value = $2
        """, key, str(value))

async def create_withdrawal(user_id: int, amount_coins: int, rate: float, card_number: str, card_name: str):
    money = int(amount_coins * rate)
    async with await get_connection() as conn:
        async with conn.transaction():
            user_coins = await conn.fetchval("SELECT coins FROM users WHERE user_id=$1", user_id)
            if user_coins < amount_coins:
                raise ValueError("Mablag' yetarli emas")
            
            await conn.execute("UPDATE users SET coins = coins - $1 WHERE user_id=$2", amount_coins, user_id)
            
            if IS_SQLITE:
                await conn.execute("""
                    INSERT INTO withdrawals (user_id, amount_coins, amount_money, card_number, card_name, status)
                    VALUES ($1, $2, $3, $4, $5, 'pending')
                """, user_id, amount_coins, money, card_number, card_name)
                row = await conn.fetchrow("SELECT last_insert_rowid() AS id")
                wid = row["id"]
            else:
                wid = await conn.fetchval("""
                    INSERT INTO withdrawals (user_id, amount_coins, amount_money, card_number, card_name, status)
                    VALUES ($1, $2, $3, $4, $5, 'pending') RETURNING id
                """, user_id, amount_coins, money, card_number, card_name)
                
        return wid

async def get_withdrawals():
    async with await get_connection() as conn:
        rows = await conn.fetch("""
            SELECT w.*, u.username, u.first_name 
            FROM withdrawals w
            LEFT JOIN users u ON w.user_id = u.user_id
            ORDER BY w.created_at DESC LIMIT 50
        """)
        return rows

async def get_user_withdrawals(user_id: int):
    async with await get_connection() as conn:
        rows = await conn.fetch("""
            SELECT * FROM withdrawals
            WHERE user_id = $1
            ORDER BY created_at DESC LIMIT 20
        """, user_id)
        return rows

async def update_withdrawal_status(wid: int, status: str):
    async with await get_connection() as conn:
        if status == 'rejected':
            row = await conn.fetchrow("SELECT * FROM withdrawals WHERE id=$1", wid)
            if row and row['status'] == 'pending':
                async with conn.transaction():
                    await conn.execute("UPDATE users SET coins = coins + $1 WHERE user_id=$2", 
                                       row['amount_coins'], row['user_id'])
                    await conn.execute("UPDATE withdrawals SET status='rejected' WHERE id=$1", wid)
        else:
            await conn.execute("UPDATE withdrawals SET status=$1 WHERE id=$2", status, wid)

async def get_admins_db():
    async with await get_connection() as conn:
        rows = await conn.fetch("SELECT user_id FROM admins")
        return [r['user_id'] for r in rows]

async def add_admin_db(user_id: int):
    async with await get_connection() as conn:
        await conn.execute("INSERT INTO admins (user_id) VALUES ($1) ON CONFLICT DO NOTHING", user_id)

async def remove_admin_db(user_id: int):
    async with await get_connection() as conn:
        await conn.execute("DELETE FROM admins WHERE user_id=$1", user_id)

async def get_user_rank(user_id: int):
    async with await get_connection() as conn:
        row = await conn.fetchrow('SELECT total_score FROM users WHERE user_id = $1', user_id)
        if row:
            user_score = row["total_score"]
            count = await conn.fetchval('SELECT COUNT(*) FROM users WHERE total_score > $1', user_score)
            rank = count + 1 if count is not None else 1
        else:
            rank = None
        return rank

async def add_coins_db(user_id: int, amount: int) -> bool:
    async with await get_connection() as conn:
        try:
            await conn.execute("UPDATE users SET coins = GREATEST(0, coins + $1) WHERE user_id=$2", amount, user_id)
            return True
        except Exception as e:
            logger.error(f"Error in add_coins_db: {e}")
            return False

async def get_user_coins_and_rank(user_id: int):
    async with await get_connection() as conn:
        row = await conn.fetchrow('SELECT coins FROM users WHERE user_id = $1', user_id)
        if row:
            user_coins = row["coins"]
            count = await conn.fetchval('SELECT COUNT(*) FROM users WHERE coins > $1', user_coins)
            rank = count + 1 if count is not None else 1
        else:
            user_coins = 0
            rank = None
        return user_coins, rank

async def get_questions_by_text(text: str):
    async with await get_connection() as conn:
        rows = await conn.fetch("SELECT id, subject, question FROM questions WHERE question ILIKE $1", f"%{text}%")
        return rows

# === REDESIGN HELPERS ===
async def get_categories():
    async with await get_connection() as conn:
        rows = await conn.fetch('SELECT * FROM categories ORDER BY sort_order ASC')
        return rows

async def get_subjects_by_category(category_slug: str, limit: int = 6, offset: int = 0):
    async with await get_connection() as conn:
        rows = await conn.fetch('''
            SELECT s.*, c.name as category_name
            FROM subjects s
            JOIN categories c ON s.category_id = c.id
            WHERE c.slug = $1 AND s.is_active = TRUE
            ORDER BY s.key ASC
            LIMIT $2 OFFSET $3
        ''', category_slug, limit, offset)
        return rows

async def get_subjects_by_category_count(category_slug: str) -> int:
    async with await get_connection() as conn:
        count = await conn.fetchval('''
            SELECT COUNT(*)
            FROM subjects s
            JOIN categories c ON s.category_id = c.id
            WHERE c.slug = $1 AND s.is_active = TRUE
        ''', category_slug)
        return count or 0

async def search_subjects_db(query: str, limit: int = 10):
    async with await get_connection() as conn:
        rows = await conn.fetch('''
            SELECT * FROM subjects
            WHERE (key ILIKE $1 OR name ILIKE $1) AND is_active = TRUE
            ORDER BY key ASC LIMIT $2
        ''', f'%{query}%', limit)
        return rows

async def get_popular_subjects(limit: int = 5):
    async with await get_connection() as conn:
        rows = await conn.fetch('''
            SELECT * FROM subjects
            WHERE is_popular = TRUE AND is_active = TRUE
            ORDER BY key ASC LIMIT $1
        ''', limit)
        return rows

async def get_subject(key: str):
    async with await get_connection() as conn:
        row = await conn.fetchrow('''
            SELECT s.*, c.slug as category_slug, c.name as category_name
            FROM subjects s
            LEFT JOIN categories c ON s.category_id = c.id
            WHERE s.key = $1
        ''', key)
        return row
