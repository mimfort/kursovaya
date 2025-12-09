from fractions import Fraction

from db.models import Subject
from tasks.generator import generate_tasks


def _is_finite_decimal(text: str) -> bool:
    # convert text to Fraction and check denominator prime factors
    frac = Fraction(text)
    denom = frac.denominator
    while denom % 2 == 0:
        denom //= 2
    while denom % 5 == 0:
        denom //= 5
    return denom == 1


def test_generate_algebra_returns_finite_decimal_answers():
    tasks = generate_tasks(Subject.algebra, 10)
    for task in tasks:
        assert _is_finite_decimal(task.answer)


def test_generate_geometry_answers_numeric():
    tasks = generate_tasks(Subject.geometry, 10)
    for task in tasks:
        # answers должны быть приводимы к Fraction
        Fraction(task.answer)
