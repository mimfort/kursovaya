from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.keyboards import (
    after_pdf_keyboard,
    difficulty_keyboard,
    main_menu_keyboard,
    retry_keyboard,
    subject_keyboard,
)
from bot.states import CheckingAnswers, GenerateTasks
from core.config import load_settings
from db.base import get_session
from db.models import Subject
from db.repository import (
    calc_stats,
    create_task_set,
    get_latest_open_task_set,
    get_task_by_order,
    get_task_set,
    get_user,
    mark_task_set_completed,
    save_attempt,
)
from pdf.generator import build_pdf
from tasks.checker import compare_answers
from tasks.generator import TaskPayload, generate_tasks

router = Router()
settings = load_settings()


@router.message(F.text == "Новый вариант")
async def new_variant(message: Message, state: FSMContext) -> None:
    async with get_session() as session:
        user = await get_user(session, tg_id=message.from_user.id)
    if not user:
        await message.answer("Сначала зарегистрируйтесь через /start.")
        return
    await state.clear()
    await state.set_state(GenerateTasks.subject)
    await message.answer("Выберите предмет:", reply_markup=subject_keyboard())


@router.callback_query(F.data.startswith("subject:"))
async def pick_subject(callback: CallbackQuery, state: FSMContext) -> None:
    subject_value = callback.data.split(":", 1)[1]
    await state.update_data(subject=subject_value)
    await state.set_state(GenerateTasks.difficulty)
    await callback.message.answer("Выберите сложность:", reply_markup=difficulty_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("difficulty:"))
async def pick_difficulty(callback: CallbackQuery, state: FSMContext) -> None:
    diff = callback.data.split(":", 1)[1]
    await state.update_data(difficulty=diff)
    await state.set_state(GenerateTasks.count)
    await callback.message.answer("Сколько задач сгенерировать? (1-15). Пример: 5")
    await callback.answer()


@router.message(GenerateTasks.count)
async def pick_count(message: Message, state: FSMContext) -> None:
    try:
        count = int(message.text.strip())
    except ValueError:
        await message.answer("Введите число, например 5.")
        return
    if count <= 0 or count > 15:
        await message.answer("Количество задач должно быть от 1 до 15.")
        return
    data = await state.get_data()
    subject = Subject(data["subject"])
    difficulty = data.get("difficulty", "normal")
    async with get_session() as session:
        user = await get_user(session, tg_id=message.from_user.id)
        if not user:
            await message.answer("Похоже, регистрация не завершена. Запустите /start.")
            return
        generated = generate_tasks(subject, count, difficulty=difficulty)
        tasks_for_db = [{"topic": t.topic, "text": t.text, "answer": t.answer, "difficulty": t.difficulty} for t in generated]
        task_set, tasks_db = await create_task_set(session, user_id=user.id, subject=subject, tasks=tasks_for_db)
        pdf_path = build_pdf(task_set, tasks_db, user, pdf_dir=settings.pdf_dir, bot_name=settings.bot_name or None)
    await message.answer_document(
        FSInputFile(pdf_path),
        caption=f"Ваш вариант по предмету: {subject.value}. Ответы вводите по порядку.\n"
        "Формат ответа: десятичная дробь или целое (пример: 1.25). Округляйте до тысячных при необходимости.",
        reply_markup=after_pdf_keyboard(),
    )
    await state.update_data(task_set_id=task_set.id, current_order=1, total_tasks=task_set.total_tasks)
    await state.set_state(CheckingAnswers.current_order)


@router.callback_query(F.data == "go_check")
async def go_check(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    task_set_id = data.get("task_set_id")
    if not task_set_id:
        async with get_session() as session:
            user = await get_user(session, tg_id=callback.from_user.id)
            if not user:
                await callback.message.answer("Сначала зарегистрируйтесь через /start.")
                await callback.answer()
                return
            open_set = await get_latest_open_task_set(session, user_id=user.id)
        if not open_set:
            await callback.message.answer("Нет открытых вариантов. Создайте новый.")
            await callback.answer()
            return
        task_set_id = open_set.id
        await state.update_data(task_set_id=task_set_id, current_order=1, total_tasks=open_set.total_tasks)
    await state.set_state(CheckingAnswers.current_order)
    await _send_current_task(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "go_menu")
async def go_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.message(F.text == "Проверить ответы")
async def start_check_flow(message: Message, state: FSMContext) -> None:
    async with get_session() as session:
        user = await get_user(session, tg_id=message.from_user.id)
        if not user:
            await message.answer("Сначала зарегистрируйтесь через /start.")
            return
        open_set = await get_latest_open_task_set(session, user_id=user.id)
    if not open_set:
        await message.answer("У вас нет незавершённых вариантов. Сгенерируйте новый.")
        return
    await state.update_data(task_set_id=open_set.id, current_order=1, total_tasks=open_set.total_tasks)
    await state.set_state(CheckingAnswers.current_order)
    await _send_current_task(message, state)


@router.message(F.text == "Продолжить вариант")
async def continue_variant(message: Message, state: FSMContext) -> None:
    async with get_session() as session:
        user = await get_user(session, tg_id=message.from_user.id)
        if not user:
            await message.answer("Сначала зарегистрируйтесь через /start.")
            return
        open_set = await get_latest_open_task_set(session, user_id=user.id)
    if not open_set:
        await message.answer("Нет незавершённых вариантов. Нажмите «Новый вариант».")
        return
    await state.update_data(task_set_id=open_set.id, current_order=1, total_tasks=open_set.total_tasks)
    await state.set_state(CheckingAnswers.current_order)
    await _send_current_task(message, state)


@router.message(CheckingAnswers.current_order)
async def process_answer(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    task_set_id = data.get("task_set_id")
    current_order = data.get("current_order", 1)
    total_tasks = data.get("total_tasks")
    async with get_session() as session:
        user = await get_user(session, tg_id=message.from_user.id)
        if not user:
            await message.answer("Сначала зарегистрируйтесь через /start.")
            return
        task = await get_task_by_order(session, task_set_id, current_order)
        if not task:
            await message.answer("Не удалось найти задачу. Начните заново через /start.")
            await state.clear()
            return
        if total_tasks is None:
            ts = await get_task_set(session, task_set_id)
            total_tasks = ts.total_tasks if ts else 0
            await state.update_data(total_tasks=total_tasks)
        is_correct = bool(compare_answers(task.correct_answer, message.text))
        await save_attempt(session, task=task, user=user, user_answer=message.text, is_correct=is_correct)
        if is_correct:
            await message.answer("Верно! Двигаемся дальше.")
            next_order = current_order + 1
            await state.update_data(current_order=next_order)
            if next_order > (total_tasks or 0):
                await mark_task_set_completed(session, task.task_set_id)
                await _send_summary(message, session, user_id=user.id, task_set_id=task.task_set_id)
                await state.clear()
                return
            await _send_current_task(message, state)
        else:
            await message.answer("Неверно. Попробуйте ещё раз или узнайте ответ.", reply_markup=retry_keyboard())
            await state.update_data(last_incorrect_task=task.id)


@router.callback_query(F.data == "retry")
async def retry_answer(callback: CallbackQuery, state: FSMContext) -> None:
    await _send_current_task(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "show_answer")
async def show_answer(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    task_set_id = data.get("task_set_id")
    current_order = data.get("current_order", 1)
    total_tasks = data.get("total_tasks")
    async with get_session() as session:
        task = await get_task_by_order(session, task_set_id, current_order)
        user = await get_user(session, tg_id=callback.from_user.id)
        if task and user:
            await save_attempt(session, task=task, user=user, user_answer="(подсмотр)", is_correct=False, looked_answer=True)
        if total_tasks is None:
            ts = await get_task_set(session, task_set_id)
            total_tasks = ts.total_tasks if ts else 0
            await state.update_data(total_tasks=total_tasks)
    if not task:
        await callback.message.answer("Задача не найдена, начните заново.")
        await state.clear()
        await callback.answer()
        return
    await callback.message.answer(f"Правильный ответ: {task.correct_answer}")
    await state.update_data(current_order=current_order + 1)
    async with get_session() as session:
        if current_order >= (total_tasks or 0):
            await mark_task_set_completed(session, task.task_set_id)
            await callback.message.answer("Вариант завершён.", reply_markup=main_menu_keyboard())
            await state.clear()
        else:
            await _send_current_task(callback.message, state)
    await callback.answer()


async def _send_current_task(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    task_set_id = data.get("task_set_id")
    current_order = data.get("current_order", 1)
    async with get_session() as session:
        task = await get_task_by_order(session, task_set_id, current_order)
    if not task:
        await message.answer("Не удалось найти текущую задачу. Начните заново /start.")
        await state.clear()
        return
    await message.answer(
        f"Задача {task.order_index} (уровень {task.difficulty}):\n{task.text}\n"
        "Ответ: десятичная дробь или целое (пример: 1.25). Без обыкновенных дробей."
    )


async def _send_summary(message: Message, session, user_id: int, task_set_id: int) -> None:
    stats = await calc_stats(session, user_id=user_id)
    total = stats["total_attempts"]
    correct = stats["total_correct"]
    await message.answer(
        f"Набор №{task_set_id} завершён.\nПравильных ответов всего: {correct} из {total}.",
        reply_markup=main_menu_keyboard(),
    )
