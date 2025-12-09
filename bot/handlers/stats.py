from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards import main_menu_keyboard
from db.base import get_session
from db.repository import calc_stats, get_user

router = Router()


@router.message(F.text == "Статистика")
async def show_stats(message: Message) -> None:
    async with get_session() as session:
        user = await get_user(session, tg_id=message.from_user.id)
        if not user:
            await message.answer("Сначала зарегистрируйтесь через /start.")
            return
        stats = await calc_stats(session, user_id=user.id)
    total = stats["total_attempts"]
    correct = stats["total_correct"]
    lines = [
        f"Всего попыток: {total}",
        f"Правильных: {correct}",
    ]
    if stats["by_subject"]:
        lines.append("По предметам:")
        for subject, data in stats["by_subject"].items():
            subj_title = "Алгебра" if subject == "algebra" else "Геометрия"
            lines.append(f"- {subj_title}: {data['correct']} из {data['total']}")
    if stats["by_topic"]:
        lines.append("Темы:")
        for topic, data in stats["by_topic"].items():
            if data["total"] == 0:
                continue
            success = round((data['correct'] / data['total']) * 100, 1)
            lines.append(f"- {topic}: {success}% ({data['correct']} из {data['total']})")
    if stats["peeked"]:
        lines.append(f"Подсмотр ответов: {stats['peeked']}")
    last = stats.get("last_7d", {})
    if last:
        lines.append(f"За 7 дней: {last.get('correct',0)} из {last.get('total',0)} верных")
    await message.answer("\n".join(lines), reply_markup=main_menu_keyboard())
