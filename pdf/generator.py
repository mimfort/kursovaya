from io import BytesIO
from pathlib import Path
from typing import Iterable, Optional

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from db.models import GeneratedTask, TaskSet, User


_FONT_NAME = "CyrillicSans"


def _register_font() -> str:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/Library/Fonts/Times New Roman.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            pdfmetrics.registerFont(TTFont(_FONT_NAME, path))
            return _FONT_NAME
    # fallback to built-in (может не отрендерить кириллицу, но не падаем)
    return "Helvetica"


def build_pdf(task_set: TaskSet, tasks: Iterable[GeneratedTask], user: User, pdf_dir: Path, bot_name: Optional[str] = None) -> Path:
    font_name = _register_font()
    pdf_dir.mkdir(parents=True, exist_ok=True)
    filename = pdf_dir / f"taskset_{task_set.id}.pdf"
    c = canvas.Canvas(str(filename), pagesize=A4)
    width, height = A4

    margin = 20 * mm
    y = height - margin

    # Header without heavy bar
    c.setFillColor(colors.black)
    c.setFont(font_name, 14)
    c.drawString(margin, y, "Индивидуальные задания")
    y -= 16

    c.setFont(font_name, 11)
    c.drawString(margin, y, f"Ученик: {user.full_name} (класс: {user.grade})")
    y -= 12
    c.drawString(margin, y, f"Предмет: {task_set.subject.value}")
    y -= 12
    c.drawString(margin, y, f"Набор № {task_set.id}, задач: {task_set.total_tasks}")
    y -= 16
    c.setFont(font_name, 10)
    c.setFillColor(colors.gray)
    c.drawString(margin, y, "Ответ: десятичная дробь или целое. Округляйте до тысячных при необходимости.")
    y -= 18
    c.setFillColor(colors.black)

    if bot_name:
        qr_stream = BytesIO()
        qr = qrcode.QRCode(border=1, box_size=4)
        qr.add_data(f"https://t.me/{bot_name}")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        img.save(qr_stream, format="PNG")
        qr_stream.seek(0)
        c.drawInlineImage(img, width - margin - 30 * mm, height - 38 * mm, 25 * mm, 25 * mm)

    for task in tasks:
        text = f"{task.order_index}. {task.text}"
        # Wrap manually if line is too long
        wrapped = _wrap_text(text, max_width=width - 2 * margin, font_size=11)
        for line in wrapped:
            if y < margin:
                c.showPage()
                y = height - margin
                c.setFont(font_name, 11)
            c.drawString(margin, y, line)
            y -= 12
        y -= 6

    c.showPage()
    c.save()
    return filename


def _wrap_text(text: str, max_width: float, font_size: int) -> list[str]:
    # Simple word-wrapping based on character count approximation
    avg_char_width = font_size * 0.5
    max_chars = int(max_width / avg_char_width)
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > max_chars:
            lines.append(current.strip())
            current = word
        else:
            current += " " + word
    if current:
        lines.append(current.strip())
    return lines
