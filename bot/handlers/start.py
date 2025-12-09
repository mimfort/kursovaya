from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards import main_menu_keyboard, start_keyboard
from bot.states import Registration
from db.base import get_session
from db.repository import create_user, get_user

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    async with get_session() as session:
        user = await get_user(session, tg_id=message.from_user.id)
        if user:
            await message.answer(
                f"Привет, {user.full_name}! Что делаем дальше?",
                reply_markup=main_menu_keyboard(),
            )
            return
    await message.answer(
        "Привет! Я бот для генерации и проверки задач. Нажми кнопку, чтобы зарегистрироваться.",
        reply_markup=start_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Я помогу с вариантами по алгебре и геометрии.\n"
        "1) /start — регистрация и главное меню\n"
        "2) «Новый вариант» — выбрать предмет и получить PDF\n"
        "3) «Проверить ответы» или «Продолжить вариант» — ввести ответы по порядку\n"
        "Формат ответов: 1.25 или 1/2 или 1 1/2 или 25%",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "register")
async def start_registration(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Registration.full_name)
    await callback.message.answer("Введите фамилию и имя (например: Иванов Иван):")
    await callback.answer()


@router.message(Registration.full_name)
async def process_full_name(message: Message, state: FSMContext) -> None:
    await state.update_data(full_name=message.text.strip())
    await state.set_state(Registration.grade)
    await message.answer("Введите класс (например: 9Б):")


@router.message(Registration.grade)
async def process_grade(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    full_name = data.get("full_name", "").strip()
    grade = message.text.strip()
    if not full_name:
        await message.answer("Сначала введите фамилию и имя.")
        await state.set_state(Registration.full_name)
        return
    async with get_session() as session:
        existing = await get_user(session, tg_id=message.from_user.id)
        if existing:
            await message.answer("Вы уже зарегистрированы.", reply_markup=main_menu_keyboard())
        else:
            await create_user(session, tg_id=message.from_user.id, full_name=full_name, grade=grade)
            await message.answer("Регистрация завершена! Теперь можно работать с заданиями.", reply_markup=main_menu_keyboard())
    await state.clear()
