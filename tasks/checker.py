import re
from decimal import Decimal, InvalidOperation
from typing import Tuple

NUM_PATTERN = re.compile(r"^-?\d+(?:[.,]\d+)?$")


def _normalize_answer(value: str) -> str:
    return value.replace(",", ".").strip()


def _parse_decimal(value: str) -> Tuple[Decimal, bool]:
    text = _normalize_answer(value)
    if not NUM_PATTERN.match(text):
        return Decimal(0), False
    try:
        return Decimal(text), True
    except InvalidOperation:
        return Decimal(0), False


def compare_answers(correct: str, user_input: str, tol: float = 1e-6) -> bool:
    correct_dec, ok_correct = _parse_decimal(correct)
    user_dec, ok_user = _parse_decimal(user_input)
    if not (ok_correct and ok_user):
        return False
    return abs(correct_dec - user_dec) <= Decimal(str(tol))
