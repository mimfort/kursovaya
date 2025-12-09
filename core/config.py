import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Settings:
    bot_token: str
    database_url: str
    pdf_dir: Path
    bot_name: str


def load_settings() -> Settings:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN", "")
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set in environment or .env")
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")
    pdf_dir = Path(os.getenv("PDF_DIR", "./generated_pdfs")).resolve()
    pdf_dir.mkdir(parents=True, exist_ok=True)
    bot_name = os.getenv("BOT_NAME", "").lstrip("@")
    return Settings(bot_token=bot_token, database_url=database_url, pdf_dir=pdf_dir, bot_name=bot_name)
