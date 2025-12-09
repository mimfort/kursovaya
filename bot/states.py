from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    full_name = State()
    grade = State()


class GenerateTasks(StatesGroup):
    subject = State()
    difficulty = State()
    count = State()


class CheckingAnswers(StatesGroup):
    task_set_id = State()
    current_order = State()
