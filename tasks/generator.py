from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from random import choice, randint
from typing import List

from db.models import Subject


@dataclass
class TaskPayload:
    topic: str
    text: str
    answer: str
    difficulty: str = "normal"


def _finite_decimal_fraction(min_int: int = 1, max_int: int = 30, pow2: int = 3, pow5: int = 2) -> Fraction:
    """Generate fraction with denominator 2^a * 5^b to guarantee finite decimal."""
    numerator = randint(min_int, max_int)
    pow2_val = randint(0, pow2)
    pow5_val = randint(0, pow5)
    denominator = (2**pow2_val) * (5**pow5_val)
    denominator = max(1, denominator)
    return Fraction(numerator, denominator)


def _fraction_to_decimal_str(value: Fraction, places: int = 3) -> str:
    q = value.limit_denominator()
    dec = (Decimal(q.numerator) / Decimal(q.denominator)).quantize(Decimal("1." + "0" * places), rounding=ROUND_HALF_UP)
    text = format(dec, f"f").rstrip("0").rstrip(".")
    return text if text else "0"


def _decimal_operations_task() -> TaskPayload:
    a = _finite_decimal_fraction()
    b = _finite_decimal_fraction()
    op = choice(["+", "-", "*", "/"])
    if op == "+":
        result = a + b
    elif op == "-":
        result = a - b
    elif op == "*":
        result = a * b
    else:
        b = b if b != 0 else Fraction(1, 2)
        result = a / b
    text = f"Найдите значение выражения: { _fraction_to_decimal_str(a) } {op} { _fraction_to_decimal_str(b) }"
    return TaskPayload(topic="decimal_arithmetics", text=text, answer=_fraction_to_decimal_str(result), difficulty="easy")


def _linear_equation_task() -> TaskPayload:
    a = choice([1, 2, 4, 5, 10, 20, 25, 50])
    b = randint(-100, 100)
    while a == 0:
        a = randint(1, 10)
    root = Fraction(-b, a)
    text = f"Найдите корень уравнения: {a}x + {b} = 0"
    return TaskPayload(topic="linear_equation", text=text, answer=_fraction_to_decimal_str(root), difficulty="easy")


def _quadratic_task() -> TaskPayload:
    # Build equation from chosen roots to control the answer
    r1 = _finite_decimal_fraction(-10, 10)
    r2 = _finite_decimal_fraction(-10, 10)
    while r1 == r2:
        r2 = _finite_decimal_fraction(-10, 10)
    a = 1
    b = -(r1 + r2)
    c = r1 * r2
    text = (
        "Найдите корни уравнения: "
        f"{a}x^2 + ({_fraction_to_decimal_str(b)})x + {_fraction_to_decimal_str(c)} = 0. "
        "В ответе напишите меньший из корней."
    )
    answer = min(r1, r2)
    return TaskPayload(topic="quadratic_equation", text=text, answer=_fraction_to_decimal_str(answer), difficulty="normal")


def _ax2_equals_bx_task() -> TaskPayload:
    a = choice([1, 2, 4, 5, 10])
    b = choice([2, 4, 5, 8, 10, 20])
    root_big = max(Fraction(0), Fraction(b, a))
    text = f"Найдите корни уравнения: {a}x^2 = {b}x. В ответ запишите больший из корней."
    return TaskPayload(topic="ax2_eq_bx", text=text, answer=_fraction_to_decimal_str(root_big), difficulty="easy")


def _probability_task() -> TaskPayload:
    variant = choice(["cups", "flashlights", "taxi", "tickets"])
    total = choice([4, 5, 8, 10, 16, 20, 25, 40, 50, 80, 100])
    if variant == "cups":
        red = randint(1, total - 1)
        prob = Fraction(red, total)
        text = (
            f"У бабушки {total} чашек: {red} с красными цветами, остальные с синими. "
            "Бабушка наливает чай в случайно выбранную чашку. Найдите вероятность, что это будет чашка с красными цветами."
        )
    elif variant == "flashlights":
        bad = randint(1, total - 1)
        prob = Fraction(total - bad, total)
        text = (
            f"В среднем из {total} фонариков, поступивших в продажу, {bad} неисправных. "
            "Найдите вероятность, что выбранный наудачу фонарик окажется исправен."
        )
    elif variant == "taxi":
        yellow = randint(1, total - 1)
        black = randint(1, total - yellow - 1)
        green = total - yellow - black
        prob = Fraction(yellow, total)
        text = (
            f"В фирме такси в данный момент свободно {total} машин: {black} черных, {yellow} желтых и {green} зеленых. "
            "По вызову выехала одна из машин, случайно оказавшаяся ближе всего к заказчику. "
            "Найдите вероятность, что к нему приедет желтое такси."
        )
    else:  # tickets
        unlearned = randint(1, total - 1)
        prob = Fraction(total - unlearned, total)
        text = (
            f"На экзамене {total} билетов, Иван не выучил {unlearned} из них. "
            "Найдите вероятность, что ему попадется выученный билет."
        )
    return TaskPayload(topic="probability", text=text, answer=_fraction_to_decimal_str(prob), difficulty="normal")


def _proportion_task() -> TaskPayload:
    """Простая пропорция с конечной десятичной дробью."""
    a = randint(2, 12)
    b = randint(2, 12)
    x = randint(2, 12)
    y = Fraction(a * x, b)
    text = f"Решите пропорцию: {a} : {b} = x : {x}. Найдите x."
    return TaskPayload(topic="proportion", text=text, answer=_fraction_to_decimal_str(y), difficulty="normal")


def _triangle_angles_task() -> TaskPayload:
    variant = choice(["two_angles", "right_triangle", "exterior"])
    if variant == "two_angles":
        a = randint(20, 90)
        b = randint(20, 90)
        while a + b >= 179:
            b = randint(20, 90)
        answer = 180 - a - b
        text = f"В треугольнике два угла равны {a}° и {b}°. Найдите третий угол. Ответ дайте в градусах."
    elif variant == "right_triangle":
        a = randint(15, 75)
        answer = 90 - a
        text = f"Один из острых углов прямоугольного треугольника равен {a}°. Найдите третий угол."
    else:
        angle_c = randint(30, 150)
        answer = 180 - angle_c
        text = f"В треугольнике ABC угол C равен {angle_c}°. Найдите внешний угол при вершине C."
    return TaskPayload(topic="triangle_angles", text=text, answer=str(answer), difficulty="easy")


def _triangle_elements_task() -> TaskPayload:
    variant = choice(["median", "mid_segment"])
    if variant == "median":
        ac = randint(4, 20)
        bm = randint(3, ac)
        answer = ac / 2
        text = f"В треугольнике ABC известно, что AC = {ac}, BM — медиана, BM = {bm}. Найдите AM."
    else:
        a = randint(3, 12)
        b = randint(3, 12)
        c = randint(abs(a - b) + 1, a + b - 1)
        answer = c / 2
        text = (
            f"Точки M и N — середины сторон AB и BC треугольника ABC, сторона AB = {a}, BC = {b}, AC = {c}. "
            "Найдите MN."
        )
    return TaskPayload(topic="triangle_elements", text=text, answer=_fraction_to_decimal_str(Fraction(answer)), difficulty="normal")


def _triangle_area_task() -> TaskPayload:
    variant = choice(["side_height", "legs"])
    if variant == "side_height":
        a = randint(3, 20)
        h = randint(2, 15)
        area = Fraction(a * h, 2)
        text = f"Сторона треугольника равна {a}, а высота к этой стороне — {h}. Найдите площадь треугольника."
    else:
        a = randint(3, 15)
        b = randint(3, 15)
        area = Fraction(a * b, 2)
        text = f"Два катета прямоугольного треугольника равны {a} и {b}. Найдите площадь треугольника."
    return TaskPayload(topic="triangle_area", text=text, answer=_fraction_to_decimal_str(area), difficulty="easy")


def _triangle_perimeter_task() -> TaskPayload:
    a = randint(3, 15)
    b = randint(3, 15)
    c = randint(abs(a - b) + 1, a + b - 1)
    perimeter = a + b + c
    text = f"Стороны треугольника равны {a}, {b}, {c}. Найдите периметр."
    return TaskPayload(topic="triangle_perimeter", text=text, answer=str(perimeter), difficulty="easy")


def generate_tasks(subject: Subject, count: int, difficulty: str = "normal") -> List[TaskPayload]:
    generators = []
    if subject == Subject.algebra:
        generators = [
            _decimal_operations_task,
            _linear_equation_task,
            _quadratic_task,
            _ax2_equals_bx_task,
            _probability_task,
            _proportion_task,
        ]
    elif subject == Subject.geometry:
        generators = [
            _triangle_angles_task,
            _triangle_elements_task,
            _triangle_area_task,
            _triangle_perimeter_task,
        ]
    tasks: List[TaskPayload] = []
    for _ in range(count):
        gen = choice(generators)
        task = gen()
        task.difficulty = difficulty
        tasks.append(task)
    return tasks
