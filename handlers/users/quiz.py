import asyncio
import html
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.types import PollAnswer
from loader import bot, logger
from database import (
    create_quiz_session, save_user_answer, get_session_results, close_session,
    get_questions, get_or_create_user, get_all_subjects
)

router = Router()

# Global quiz state (simple dict for mvp)
active_quizzes: dict = {}

# Fast poll lookup map (poll_id -> chat_id) for O(1) lookup
poll_to_chat: dict = {}

# ==== QUIZ helpers ====
def _parse_quiz_command(text: str) -> tuple[str | None, int | None, int | str | None, int | str | None]:
    text = (text or "").strip()
    if not text.startswith("/quiz"):
        return None, None, None, None
    # Extract subject from command suffix, e.g., /quizeng -> eng
    cmd_and_rest = text.split(maxsplit=1)
    cmd = cmd_and_rest[0]
    rest = cmd_and_rest[1] if len(cmd_and_rest) > 1 else ""
    suffix = cmd[5:].strip().lower()

    subject: str | None = suffix if suffix else None
    num_questions: int | None = None
    seconds_per_question: int | str | None = None
    target_answers: int | str | None = None

    for token in [t for t in rest.split() if t]:
        token_lower = token.lower()
        if token.isdigit():
            if num_questions is None:
                num_questions = int(token)
            elif seconds_per_question is None:
                seconds_per_question = int(token)
            elif target_answers is None and seconds_per_question == "off":
                target_answers = int(token)
        elif token == ".":
            if target_answers is None and seconds_per_question == "off":
                target_answers = "."
        elif token_lower == "off":
            if seconds_per_question is None:
                seconds_per_question = "off"
        else:
            if subject is None:
                subject = token_lower

    return subject, num_questions, seconds_per_question, target_answers

async def _run_quiz_from_text(message: types.Message):
    subject, num_questions, seconds_per_question, target_answers = _parse_quiz_command(message.text or "")
    num_questions = 20 if num_questions is None else max(1, min(100, num_questions))
    
    if seconds_per_question != "off":
        seconds_per_question = 15 if seconds_per_question is None else max(5, min(600, int(seconds_per_question)))
    
    if target_answers is None and seconds_per_question == "off":
        target_answers = 1

    if subject:
        subjects_db = set(await get_all_subjects())
        subjects_defaults = {"english", "russian", "math", "physics"}
        if subject not in subjects_db and subject not in subjects_defaults:
            await message.answer(f"❌ Bunday fan topilmadi: {subject}")
            return

    await start_quiz(
        message, 
        subject, 
        num_questions=num_questions, 
        seconds_per_question=seconds_per_question, 
        target_answers=target_answers
    )

async def start_quiz(message: types.Message, subject: str | None, *, num_questions: int = 20, seconds_per_question: int | str = 15, target_answers: int | str | None = None):
    chat_id = message.chat.id
    if chat_id in active_quizzes and active_quizzes[chat_id]["active"]:
        await message.answer("❌ Test allaqachon boshlangan!")
        return

    questions = await get_questions(subject=subject, limit=num_questions)
    if not questions:
        await message.answer("❌ Bu fan uchun savollar topilmadi.")
        return

    session_id = await create_quiz_session(chat_id)
    active_quizzes[chat_id] = {
        "active": True,
        "session_id": session_id,
        "current_question": 0,
        "questions": questions,
        "poll_ids": {},
        "seconds_per_question": seconds_per_question,
        "target_answers": target_answers,
        "current_answers": 0
    }

    time_text = "Vaqtsiz (off)" if seconds_per_question == "off" else f"⏱ Har biriga {seconds_per_question} soniya"
    info_text = f"🎯 Test boshlandi!\nFan: {subject or 'Barcha fanlar'}\nSavollar soni: {len(questions)}\n{time_text}"
    if seconds_per_question == "off" and target_answers:
        if target_answers == ".":
            info_text += "\nRejim: 1-to'g'ri javobgacha (Pollar yopilmaydi)"
        else:
            info_text += f"\nKutilayotgan javoblar: {target_answers} ta"

    await message.answer(info_text, parse_mode="HTML")
    await send_next_question(chat_id)

async def send_next_question(chat_id: int):
    quiz = active_quizzes.get(chat_id)
    if not quiz or not quiz["active"]:
        return

    i = quiz["current_question"]
    questions = quiz["questions"]
    quiz["current_answers"] = 0

    if i >= len(questions):
        await finish_quiz(chat_id)
        return

    q = questions[i]
    try:
        # Send image if exists
        image = q.get("image_url") or q.get("image")
        if image:
            try:
                await bot.send_photo(chat_id=chat_id, photo=image)
                await asyncio.sleep(0.6)
            except Exception as e:
                logger.warning("Rasm yuborishda xato: %s", e)

        raw_question = q.get("question") or ""
        if raw_question.strip() == "" or raw_question.strip().lower() in ("❓rasmdagi savol", "rasmdagi savol"):
            question_text = "Rasmda nima aks etilgan?"
        else:
            question_text = raw_question

        poll_kwargs = {
            "chat_id": chat_id,
            "question": f"❓ {i + 1}/{len(questions)}: {question_text}",
            "options": q["options"],
            "type": "quiz",
            "correct_option_id": q["correct_option_id"],
            "is_anonymous": False
        }
        if quiz["seconds_per_question"] != "off":
            poll_kwargs["open_period"] = int(quiz["seconds_per_question"])

        poll = await bot.send_poll(**poll_kwargs)
    except Exception as e:
        logger.exception("Poll yuborishda xato (savol #%s): %s", i, e)
        quiz["current_question"] += 1
        await asyncio.sleep(1)
        await send_next_question(chat_id)
        return

    if poll.poll:
        quiz["poll_ids"][poll.poll.id] = {
            "question_num": i, 
            "correct": q["correct_option_id"],
            "question_id": q.get("id"),
            "message_id": poll.message_id,
            "first_correct_given": False
        }
        poll_to_chat[poll.poll.id] = chat_id

    if quiz["seconds_per_question"] != "off":
        await asyncio.sleep(max(int(quiz["seconds_per_question"]) + 2, 5))
        # If question was skipped or poll stopped manually, do not proceed in this sleeper
        if not quiz.get("active", False) or quiz.get("current_question", -1) != i:
            return
        quiz["current_question"] += 1
        await send_next_question(chat_id)

async def finish_quiz(chat_id: int):
    quiz = active_quizzes.get(chat_id)
    if not quiz:
        return

    session_id = quiz["session_id"]
    results = await get_session_results(session_id)
    active_quizzes[chat_id]["active"] = False

    if not results:
        try:
            await bot.send_message(chat_id, "❌ Test tugadi, hech kim javob bermadi.")
        except Exception:
            pass
        await close_session(session_id)
        active_quizzes.pop(chat_id, None)
        return

    text = "🏆 <b>Natijalar:</b>\n\n"
    for i, (uid, username, fname, score) in enumerate(results, 1):
        if username:
            name = f"@{username}"
        elif fname:
            name = html.escape(fname)
        else:
            name = str(uid)
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "▫️"
        text += f"{medal} {i}. {name} — {score} 🪙tanga\n"

    try:
        await bot.send_message(chat_id, text, parse_mode="HTML")
    except Exception as e:
        logger.exception("Natijani yuborishda xato: %s", e)

    # Clean up active poll lookups to prevent memory leak
    for poll_id in list(quiz.get("poll_ids", {}).keys()):
        poll_to_chat.pop(poll_id, None)

    await close_session(session_id)
    active_quizzes.pop(chat_id, None)

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message):
    chat_id = message.chat.id
    quiz = active_quizzes.get(chat_id)
    if not quiz or not quiz.get("active", False):
        await message.answer("❌ Hech qanday test faol emas.", parse_mode="HTML")
        return

    active_quizzes[chat_id]["active"] = False
    await message.answer("❗ Test bekor qilinyapti... Natijalar hisoblanadi.", parse_mode="HTML")
    await finish_quiz(chat_id)

@router.message(Command("next"))
async def cmd_next(message: types.Message):
    chat_id = message.chat.id
    quiz = active_quizzes.get(chat_id)
    if not quiz or not quiz.get("active", False):
        await message.answer("❌ Hech qanday test faol emas.")
        return
        
    if quiz["seconds_per_question"] != "off":
        await message.answer("❌ /next komandasi faqat vaqtsiz (off) testlar uchun ishlaydi.")
        return
        
    for poll_id, q_info in list(quiz["poll_ids"].items()):
        if q_info["question_num"] == quiz["current_question"]:
            try:
                await bot.stop_poll(chat_id=chat_id, message_id=q_info["message_id"])
            except Exception:
                pass
            
    await message.answer("⏭ Keyingi savolga o'tilmoqda...")
    quiz["current_question"] += 1
    await send_next_question(chat_id)

@router.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer):
    user = poll_answer.user
    if not user:
        return

    poll_id = poll_answer.poll_id
    option = poll_answer.option_ids[0] if poll_answer.option_ids else None

    await get_or_create_user(user.id, user.username, user.first_name, user.last_name)

    chat_id = poll_to_chat.get(poll_id)
    if chat_id:
        quiz = active_quizzes.get(chat_id)
        if quiz and poll_id in quiz["poll_ids"]:
            q_info = quiz["poll_ids"][poll_id]
            is_correct = option == q_info["correct"]
            
            # Record answer and proceed if off-mode
            if option is not None:
                question_id = q_info.get("question_id")
                if quiz.get("target_answers") == ".":
                    if is_correct:
                        if not q_info.get("first_correct_given", False):
                            q_info["first_correct_given"] = True
                            await save_user_answer(quiz["session_id"], user.id, q_info["question_num"], is_correct=True, group_score=1, question_id=question_id)
                            
                            if quiz["current_question"] == q_info["question_num"]:
                                quiz["current_question"] += 1
                                asyncio.create_task(send_next_question(chat_id))
                        else:
                            await save_user_answer(quiz["session_id"], user.id, q_info["question_num"], is_correct=True, group_score=0, question_id=question_id)
                    else:
                        await save_user_answer(quiz["session_id"], user.id, q_info["question_num"], is_correct=False, group_score=0, question_id=question_id)
                else:
                    group_score = 1 if is_correct else 0
                    await save_user_answer(quiz["session_id"], user.id, q_info["question_num"], is_correct=is_correct, group_score=group_score, question_id=question_id)

                    if is_correct:
                        quiz["current_answers"] += 1
                        
                    if quiz["seconds_per_question"] == "off":
                        if quiz["target_answers"] and quiz["current_answers"] >= int(quiz["target_answers"]):
                            if quiz["current_question"] == q_info["question_num"]:
                                quiz["current_question"] += 1
                                try:
                                    await bot.stop_poll(chat_id=chat_id, message_id=q_info["message_id"])
                                except Exception:
                                    pass
                                asyncio.create_task(send_next_question(chat_id))

@router.message(F.text.startswith("/quiz"))
async def handle_quiz_any(message: types.Message):
    await _run_quiz_from_text(message)
