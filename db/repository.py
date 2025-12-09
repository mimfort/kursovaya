from collections import defaultdict
from datetime import datetime, timedelta
from typing import Iterable, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AnswerAttempt, GeneratedTask, Subject, TaskSet, User


async def get_user(session: AsyncSession, tg_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, tg_id: int, full_name: str, grade: str) -> User:
    user = User(tg_id=tg_id, full_name=full_name, grade=grade)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def create_task_set(
    session: AsyncSession,
    user_id: int,
    subject: Subject,
    tasks: Iterable[dict],
) -> tuple[TaskSet, list[GeneratedTask]]:
    tasks_list = list(tasks)
    task_set = TaskSet(user_id=user_id, subject=subject, total_tasks=len(tasks_list))
    session.add(task_set)
    await session.flush()

    tasks_to_add: list[GeneratedTask] = []
    for idx, task in enumerate(tasks_list, start=1):
        task_data = {
            "task_set_id": task_set.id,
            "order_index": idx,
            "subject": subject,
            "topic": task["topic"],
            "text": task["text"],
            "correct_answer": str(task["answer"]),
        }
        if "difficulty" in task:
            task_data["difficulty"] = task["difficulty"]
        tasks_to_add.append(GeneratedTask(**task_data))
    session.add_all(tasks_to_add)
    await session.commit()
    await session.refresh(task_set)
    return task_set, tasks_to_add


async def get_task_set(session: AsyncSession, task_set_id: int) -> Optional[TaskSet]:
    result = await session.execute(select(TaskSet).where(TaskSet.id == task_set_id))
    return result.scalar_one_or_none()


async def get_latest_open_task_set(session: AsyncSession, user_id: int) -> Optional[TaskSet]:
    stmt = (
        select(TaskSet)
        .where(TaskSet.user_id == user_id, TaskSet.is_completed.is_(False))
        .order_by(TaskSet.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_task_by_order(session: AsyncSession, task_set_id: int, order_index: int) -> Optional[GeneratedTask]:
    stmt = select(GeneratedTask).where(
        GeneratedTask.task_set_id == task_set_id,
        GeneratedTask.order_index == order_index,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def save_attempt(
    session: AsyncSession,
    task: GeneratedTask,
    user: User,
    user_answer: str,
    is_correct: bool,
    looked_answer: bool = False,
) -> AnswerAttempt:
    attempt = AnswerAttempt(
        task_id=task.id,
        user_id=user.id,
        user_answer=user_answer,
        is_correct=is_correct,
        looked_answer=looked_answer,
    )
    session.add(attempt)
    await session.commit()
    await session.refresh(attempt)
    return attempt


async def mark_task_set_completed(session: AsyncSession, task_set_id: int) -> None:
    await session.execute(update(TaskSet).where(TaskSet.id == task_set_id).values(is_completed=True))
    await session.commit()


async def calc_stats(session: AsyncSession, user_id: int) -> dict:
    stats = {
        "total_attempts": 0,
        "total_correct": 0,
        "by_subject": {},
        "by_topic": {},
        "peeked": 0,
        "last_7d": {},
    }
    attempts_stmt = select(
        func.count(AnswerAttempt.id),
        func.count(func.nullif(AnswerAttempt.is_correct, False)),
        func.count(func.nullif(AnswerAttempt.looked_answer, False)),
    ).where(AnswerAttempt.user_id == user_id)
    total_count, correct_count, peek_count = (await session.execute(attempts_stmt)).one()
    stats["total_attempts"] = int(total_count or 0)
    stats["total_correct"] = int(correct_count or 0)
    stats["peeked"] = int(peek_count or 0)

    by_subject_stmt = (
        select(GeneratedTask.subject, func.count(AnswerAttempt.id), func.count(func.nullif(AnswerAttempt.is_correct, False)))
        .join(GeneratedTask, GeneratedTask.id == AnswerAttempt.task_id)
        .where(AnswerAttempt.user_id == user_id)
        .group_by(GeneratedTask.subject)
    )
    for subject, total, correct in (await session.execute(by_subject_stmt)).all():
        stats["by_subject"][subject.value] = {"total": int(total), "correct": int(correct)}

    by_topic_stmt = (
        select(GeneratedTask.topic, func.count(AnswerAttempt.id), func.count(func.nullif(AnswerAttempt.is_correct, False)))
        .join(GeneratedTask, GeneratedTask.id == AnswerAttempt.task_id)
        .where(AnswerAttempt.user_id == user_id)
        .group_by(GeneratedTask.topic)
    )
    topic_stats = defaultdict(lambda: {"total": 0, "correct": 0})
    for topic, total, correct in (await session.execute(by_topic_stmt)).all():
        topic_stats[topic]["total"] = int(total)
        topic_stats[topic]["correct"] = int(correct)
    stats["by_topic"] = topic_stats

    since = datetime.utcnow() - timedelta(days=7)
    last_stmt = select(
        func.count(AnswerAttempt.id),
        func.count(func.nullif(AnswerAttempt.is_correct, False)),
    ).where(AnswerAttempt.user_id == user_id, AnswerAttempt.created_at >= since)
    last_total, last_correct = (await session.execute(last_stmt)).one()
    stats["last_7d"] = {"total": int(last_total or 0), "correct": int(last_correct or 0)}
    return stats
