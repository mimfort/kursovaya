import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Subject(str, enum.Enum):
    algebra = "algebra"
    geometry = "geometry"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    grade: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    task_sets: Mapped[list["TaskSet"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    attempts: Mapped[list["AnswerAttempt"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class TaskSet(Base):
    __tablename__ = "task_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    subject: Mapped[Subject] = mapped_column(Enum(Subject))
    total_tasks: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(back_populates="task_sets")
    tasks: Mapped[list["GeneratedTask"]] = relationship(back_populates="task_set", cascade="all, delete-orphan")


class GeneratedTask(Base):
    __tablename__ = "generated_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_set_id: Mapped[int] = mapped_column(ForeignKey("task_sets.id", ondelete="CASCADE"))
    order_index: Mapped[int] = mapped_column(Integer)
    subject: Mapped[Subject] = mapped_column(Enum(Subject))
    topic: Mapped[str] = mapped_column(String(128))
    difficulty: Mapped[str] = mapped_column(String(16), default="normal")
    text: Mapped[str] = mapped_column(Text)
    correct_answer: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    task_set: Mapped[TaskSet] = relationship(back_populates="tasks")
    attempts: Mapped[list["AnswerAttempt"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class AnswerAttempt(Base):
    __tablename__ = "answer_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("generated_tasks.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user_answer: Mapped[str] = mapped_column(String(128))
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    looked_answer: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    task: Mapped[GeneratedTask] = relationship(back_populates="attempts")
    user: Mapped[User] = relationship(back_populates="attempts")
