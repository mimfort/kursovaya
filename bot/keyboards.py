from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Зарегистрироваться", callback_data="register")],
        ]
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="Новый вариант")],
            [KeyboardButton(text="Продолжить вариант")],
            [KeyboardButton(text="Проверить ответы")],
            [KeyboardButton(text="Статистика")],
        ],
    )


def subject_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Алгебра", callback_data="subject:algebra")],
            [InlineKeyboardButton(text="Геометрия", callback_data="subject:geometry")],
        ]
    )


def difficulty_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Лёгкий", callback_data="difficulty:easy"),
                InlineKeyboardButton(text="Норма", callback_data="difficulty:normal"),
                InlineKeyboardButton(text="Сложный", callback_data="difficulty:hard"),
            ]
        ]
    )


def after_pdf_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Перейти к проверке", callback_data="go_check")],
            [InlineKeyboardButton(text="В главное меню", callback_data="go_menu")],
        ]
    )


def retry_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Решить ещё раз", callback_data="retry"),
                InlineKeyboardButton(text="Узнать ответ", callback_data="show_answer"),
            ]
        ]
    )
