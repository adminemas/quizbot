from aiohttp import web
import aiohttp_cors
import os
import json
import logging
import asyncio
from pathlib import Path

# Import DB functions
from database import (
    get_user_stats, get_global_rating, get_global_rating_weekly, get_global_rating_monthly,
    get_setting, set_setting, create_withdrawal, get_withdrawals, update_withdrawal_status,
    get_total_users_count, get_questions_count, get_active_users_7days,
    add_subject, delete_subject, get_all_subjects,
    add_question, search_questions_db, delete_question_db,
    get_admins_db, add_admin_db, remove_admin_db
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- AUTH HELPERS ---
async def get_user_id(request):
    # For Mini App, ideally we validate initData. 
    # For now we rely on X-User-ID header which the frontend sends.
    # In production, VALIDATE initData!
    uid = request.headers.get('X-User-ID')
    if not uid:
        return None
    try:
        return int(uid)
    except:
        return None

async def is_admin(request):
    uid = await get_user_id(request)
    if not uid:
        return False
    
    # Check .env admins
    env_admins = os.getenv("ADMIN_IDS", "").split(",")
    if str(uid) in [x.strip() for x in env_admins if x.strip()]:
        return True
        
    # Check DB admins
    db_admins = await get_admins_db()
    if uid in db_admins:
        return True
        
    return False

# --- USER HANDLERS ---
async def handle_user_stats(request):
    uid = await get_user_id(request)
    if not uid:
        return web.json_response({"error": "Unauthorized"}, status=401)
    
    stats = await get_user_stats(uid)
    # stats includes score, coins, rank, etc.
    return web.json_response({
        "user": {
            "id": uid, 
            "name": stats.get('first_name') or stats.get('username') or f"User {uid}",
            "coins": stats['coins'],
            "score": stats['score']
        },
        "stats": {
            "total": stats['total'],
            "correct": stats['correct'],
            "incorrect": stats['incorrect']
        },
        "rank": stats['rank']
    })

async def handle_rankings(request):
    period = request.query.get('period', 'all')
    limit = 20
    
    if period == 'week':
        rows = await get_global_rating_weekly(limit)
    elif period == 'month':
        rows = await get_global_rating_monthly(limit)
    else:
        rows = await get_global_rating(limit)
        
    # Format
    data = []
    for r in rows:
        data.append({
            "user_id": r['user_id'],
            "name": r['username'] or r['first_name'] or f"ID:{r['user_id']}",
            "score": r['total_score']
        })
    return web.json_response(data)

async def handle_exchange_info(request):
    rate = await get_setting('coin_rate', '100')
    return web.json_response({"rate": float(rate)})

async def handle_exchange_request(request):
    uid = await get_user_id(request)
    if not uid:
        return web.json_response({"error": "Unauthorized"}, status=401)
        
    try:
        data = await request.json()
        amount = int(data.get('amount', 0))
        card_number = data.get('card_number', '').strip()
        card_name = data.get('card_name', '').strip()
    except:
        return web.json_response({"error": "Invalid JSON"}, status=400)
        
    if amount <= 0:
        logger.warning(f"Exchange 400: Invalid amount {amount} for user {uid}")
        return web.json_response({"error": "Invalid amount"}, status=400)

    clean_card = card_number.replace(" ", "")
    if len(clean_card) != 16 or not clean_card.isdigit():
        logger.warning(f"Exchange 400: Invalid card number '{card_number}' (clean: '{clean_card}') for user {uid}")
        return web.json_response({"error": "Karta raqami xato (16 ta raqam bo'lishi kerak)"}, status=400)

    if not card_name:
        logger.warning(f"Exchange 400: Missing card name for user {uid}")
        return web.json_response({"error": "Kartadagi ism-familiya kiritilmagan"}, status=400)
        
    rate = float(await get_setting('coin_rate', '100'))
    min_wd = float(await get_setting('min_withdrawal', '1000'))
    
    if amount < min_wd:
        logger.warning(f"Exchange 400: Amount {amount} less than min {min_wd} for user {uid}")
        return web.json_response({"error": f"Minimal summa: {min_wd}"}, status=400)
        
    try:
        wid = await create_withdrawal(uid, amount, rate, card_number, card_name)
        
        # Adminlarga Telegram orqali xabar yuborish
        from loader import bot, ADMIN_IDS
        from database import get_admins_db, get_user
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        
        # Foydalanuvchi ma'lumotlarini olish
        user = await get_user(uid)
        username = user['username'] if user else None
        first_name = user['first_name'] if user else ""
        user_mention = f"@{username}" if username else f"<a href='tg://user?id={uid}'>{first_name or uid}</a>"
        
        money_to_pay = int(amount * rate)
        
        admin_msg = (
            f"💰 <b>Coin yechish arizasi!</b>\n\n"
            f"👤 <b>Foydalanuvchi:</b> {user_mention} (ID: <code>{uid}</code>)\n"
            f"🪙 <b>Tanga:</b> {amount} ➡️ <b>{money_to_pay:,} so'm</b>\n"
            f"💳 <b>Karta raqami:</b> <code>{card_number}</code>\n"
            f"👤 <b>Karta egasi:</b> {card_name}\n"
        )
        
        kb = InlineKeyboardBuilder()
        kb.button(text="Tasdiqlash ✅", callback_data=f"wd_approve_{wid}")
        kb.button(text="Rad etish ❌", callback_data=f"wd_reject_{wid}")
        kb.adjust(2)
        
        db_admins = await get_admins_db()
        all_admins = set([int(aid) for aid in ADMIN_IDS if aid.strip()] + db_admins)
        
        for admin_id in all_admins:
            try:
                await bot.send_message(admin_id, admin_msg, parse_mode="HTML", reply_markup=kb.as_markup())
            except Exception as e:
                logger.warning(f"Admin {admin_id} ga ariza yuborishda xatolik: {e}")
                
        return web.json_response({"success": True})
    except ValueError as e:
        logger.warning(f"Exchange ValueError: {e} for user {uid}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Exchange error: {e}")
        return web.json_response({"error": "Internal error"}, status=500)

async def handle_user_withdrawals(request):
    uid = await get_user_id(request)
    if not uid:
        return web.json_response({"error": "Unauthorized"}, status=401)
        
    try:
        from database import get_user_withdrawals
        rows = await get_user_withdrawals(uid)
        
        data = []
        for r in rows:
            data.append({
                "id": r["id"],
                "amount_coins": r["amount_coins"],
                "amount_money": r["amount_money"],
                "status": r["status"],
                "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], 'isoformat') else str(r["created_at"])
            })
            
        return web.json_response(data)
    except Exception as e:
        logger.error(f"Get user withdrawals error: {e}")
        return web.json_response({"error": "Internal error"}, status=500)

# --- ADMIN HANDLERS ---
async def admin_check_middleware(request, handler):
    if not await is_admin(request):
        return web.json_response({"error": "Forbidden"}, status=403)
    return await handler(request)

async def handle_admin_stats(request):
    if not await is_admin(request): return web.json_response({"error": "Forbidden"}, status=403)
    
    total_q = await get_questions_count()
    total_u = await get_total_users_count()
    active_u = await get_active_users_7days()
    
    return web.json_response({
        "total_questions": total_q,
        "total_users": total_u,
        "active_users": active_u,
        "inactive_users": total_u - active_u
    })

async def handle_admin_subjects(request):
    if not await is_admin(request): return web.json_response({"error": "Forbidden"}, status=403)
    
    if request.method == 'GET':
        subs = await get_all_subjects()
        return web.json_response([{"id": s, "name": s} for s in subs])
        
    elif request.method == 'POST':
        data = await request.json()
        name = data.get('name')
        if name:
            await add_subject(name)
            return web.json_response({"success": True})
            
    elif request.method == 'DELETE':
        name = request.query.get('id') or request.query.get('name')
        if name and name != 'undefined':
            await delete_subject(name)
            return web.json_response({"success": True})
            
    return web.json_response({"error": "Bad Request"}, status=400)

async def handle_admin_add_question(request):
    if not await is_admin(request): return web.json_response({"error": "Forbidden"}, status=403)
    
    try:
        data = await request.json()
        # subject, question, options (list), correct_option (int)
        await add_question(
            data['subject'], 
            data['question'], 
            data['options'], 
            int(data['correct_option']),
            created_by=await get_user_id(request)
        )
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Add question error: {e}")
        return web.json_response({"error": str(e)}, status=400)

async def handle_admin_bulk_txt(request):
    if not await is_admin(request): return web.json_response({"error": "Forbidden"}, status=403)
    
    data = await request.json()
    subject = data.get('subject')
    text = data.get('text', '')
    
    created_by = await get_user_id(request)
    
    lines = [ln.strip() for ln in text.replace('\r','').split('\n') if ln.strip()]
    success = 0
    errors = 0
    
    for line in lines:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3:
            errors += 1
            continue
        q_text = parts[0]
        options = [o.strip() for o in parts[1].split(",")]
        try:
            correct = int(parts[2]) - 1
        except:
            errors += 1
            continue
            
        if len(options) != 4 or not (0 <= correct <= 3):
            errors += 1
            continue
            
        try:
            await add_question(subject, q_text, options, correct, created_by)
            success += 1
        except:
            errors += 1
            
    return web.json_response({"added": success, "errors": errors})

async def handle_admin_bulk_pairs(request):
    if not await is_admin(request): return web.json_response({"error": "Forbidden"}, status=403)
    # Not fully implemented yet as per HTML comments, but skeleton here
    return web.json_response({"added": 0, "errors": 0})

async def handle_admin_search(request):
    if not await is_admin(request): return web.json_response({"error": "Forbidden"}, status=403)
    
    q = request.query.get('q', '')
    subj = request.query.get('subject')
    
    rows = await search_questions_db(q, subj if subj else None)
    
    res = []
    for r in rows:
        res.append({
            "id": r['id'],
            "subject": r['subject'],
            "question": r['question'],
            "options": [r['option1'], r['option2'], r['option3'], r['option4']],
            "correct_option_id": r['correct_option_id']
        })
    return web.json_response(res)

async def handle_admin_delete_question(request):
    if not await is_admin(request): return web.json_response({"error": "Forbidden"}, status=403)
    
    qid = request.query.get('id')
    if qid:
        await delete_question_db(int(qid))
        return web.json_response({"success": True})
    return web.json_response({"error": "Missing ID"}, status=400)

async def handle_admin_helpers(request):
    if not await is_admin(request): return web.json_response({"error": "Forbidden"}, status=403)
    
    if request.method == 'GET':
        admins = await get_admins_db()
        return web.json_response(admins)
    elif request.method == 'POST':
        data = await request.json()
        uid = data.get('user_id')
        if uid:
            await add_admin_db(int(uid))
            return web.json_response({"success": True})
    elif request.method == 'DELETE':
        uid = request.query.get('user_id')
        if uid:
            await remove_admin_db(int(uid))
            return web.json_response({"success": True})
            
    return web.json_response({"error": "Bad Request"}, status=400)

async def handle_admin_rate(request):
    if not await is_admin(request): return web.json_response({"error": "Forbidden"}, status=403)
    
    if request.method == 'GET':
        rate = await get_setting('coin_rate', '100')
        min_wd = await get_setting('min_withdrawal', '1000')
        return web.json_response({"rate": float(rate), "min_withdrawal": int(min_wd)})
        
    elif request.method == 'POST':
        data = await request.json()
        rate = data.get('rate')
        if rate:
            await set_setting('coin_rate', rate)
            return web.json_response({"success": True})
            
    return web.json_response({"error": "Bad Request"}, status=400)

async def handle_admin_settings(request):
    if not await is_admin(request): return web.json_response({"error": "Forbidden"}, status=403)
    
    data = await request.json()
    key = data.get('key')
    val = data.get('value')
    if key and val is not None:
        await set_setting(key, val)
        return web.json_response({"success": True})
    return web.json_response({"error": "Bad Request"}, status=400)

async def handle_admin_withdrawals(request):
    if not await is_admin(request): return web.json_response({"error": "Forbidden"}, status=403)
    
    if request.method == 'GET':
        rows = await get_withdrawals()
        data = []
        for r in rows:
            data.append({
                "id": r['id'],
                "user_id": r['user_id'],
                "username": r['username'],
                "amount_coins": r['amount_coins'],
                "amount_money": r['amount_money'],
                "created_at": str(r['created_at']),
                "status": r['status'],
                "card_number": r.get('card_number'),
                "card_name": r.get('card_name')
            })
        return web.json_response(data)
        
    return web.json_response({"error": "Bad Request"}, status=400)

async def handle_admin_withdrawals_update(request):
    if not await is_admin(request): return web.json_response({"error": "Forbidden"}, status=403)
    
    data = await request.json()
    wid = data.get('id')
    status = data.get('status')
    if wid and status:
        await update_withdrawal_status(int(wid), status)
        return web.json_response({"success": True})
    return web.json_response({"error": "Missing params"}, status=400)


# --- HTML SERVING ---
# Next.js static build output (frontend/out/) is used when available.
# Fallback: old web/index.html and web/admin.html (kept for reference).

FRONTEND_OUT = Path('./frontend/out')

async def serve_public_file(request):
    filename = request.match_info.get('filename')
    target_path = FRONTEND_OUT / filename
    if target_path.exists() and target_path.is_file():
        return web.FileResponse(str(target_path))
    return web.HTTPNotFound()

async def serve_index(request):
    next_file = FRONTEND_OUT / 'index.html'
    if next_file.exists():
        return web.FileResponse(str(next_file))
    return web.FileResponse('./web/index.html')

async def serve_admin(request):
    next_file = FRONTEND_OUT / 'admin.html'
    if next_file.exists():
        return web.FileResponse(str(next_file))
    return web.FileResponse('./web/admin.html')

# --- APP FACTORY ---
def setup_web_server():
    app = web.Application()

    # Serve Next.js static assets (_next/static, images, etc.)
    if (FRONTEND_OUT / '_next').exists():
        app.router.add_static('/_next', str(FRONTEND_OUT / '_next'), name='nextjs_static')

    # Serve any public static files from frontend/out
    if FRONTEND_OUT.exists():
        app.router.add_static('/static', str(FRONTEND_OUT), name='frontend_static', append_version=False)

    # HTML routes
    app.router.add_get('/', serve_index)
    app.router.add_get('/admin', serve_admin)
    app.router.add_get(r'/{filename:[a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+}', serve_public_file)
    
    # API Routes
    # User
    app.router.add_get('/api/user/stats', handle_user_stats)
    app.router.add_get('/api/user/withdrawals', handle_user_withdrawals)
    app.router.add_get('/api/rankings', handle_rankings)
    app.router.add_get('/api/exchange/info', handle_exchange_info)
    app.router.add_post('/api/exchange/request', handle_exchange_request)
    
    # Admin
    app.router.add_get('/api/admin/stats', handle_admin_stats)
    
    app.router.add_get('/api/admin/subjects', handle_admin_subjects)
    app.router.add_post('/api/admin/subjects', handle_admin_subjects)
    app.router.add_delete('/api/admin/subjects', handle_admin_subjects)
    
    app.router.add_post('/api/admin/questions/add', handle_admin_add_question)
    app.router.add_post('/api/admin/questions/bulk_txt', handle_admin_bulk_txt)
    app.router.add_post('/api/admin/questions/bulk_pairs', handle_admin_bulk_pairs)
    app.router.add_get('/api/admin/questions/search', handle_admin_search)
    app.router.add_delete('/api/admin/questions/delete', handle_admin_delete_question)
    
    app.router.add_get('/api/admin/helpers', handle_admin_helpers)
    app.router.add_post('/api/admin/helpers', handle_admin_helpers)
    app.router.add_delete('/api/admin/helpers', handle_admin_helpers)
    
    app.router.add_get('/api/admin/rate', handle_admin_rate)
    app.router.add_post('/api/admin/rate', handle_admin_rate)
    
    app.router.add_post('/api/admin/settings', handle_admin_settings)
    
    app.router.add_get('/api/admin/withdrawals', handle_admin_withdrawals)
    app.router.add_post('/api/admin/withdrawals', handle_admin_withdrawals_update)
    
    # CORS setup
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*",
        )
    })
    
    for route in list(app.router.routes()):
        cors.add(route)
        
    return app

async def run_web_server():
    app = setup_web_server()
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    logger.info(f"🌍 Web server running on port {port}")
    await site.start()
    
    # Keep running
    # In main.py we will asyncio.create_task this, so it runs in background
    while True:
        await asyncio.sleep(3600)
