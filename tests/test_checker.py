from tasks.checker import compare_answers


def test_compare_accepts_decimal_and_integer_only():
    correct = "0.5"
    assert compare_answers(correct, "0.5")
    assert compare_answers(correct, "0,5")
    assert not compare_answers(correct, "1/2")  # fractions forbidden
    assert not compare_answers(correct, "50%")  # percents forbidden


def test_compare_negative_and_whitespace():
    assert compare_answers("-1.25", " -1.25 ")
    assert not compare_answers("-1.25", "1.25")
