import pytest

from vanguard_primekg.question_selection import parse_numbers


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (["1"], {1}),
        (["2,3"], {2, 3}),
        (["4", "5"], {4, 5}),
        (["5, 10"], {5, 10}),
        (["1", "2,3", "4", "5, 10"], {1, 2, 3, 4, 5, 10}),
        (["1 2 3"], {1, 2, 3}),
    ],
)
def test_question_number_forms(values: list[str], expected: set[int]) -> None:
    assert parse_numbers(values) == expected


def test_question_number_forms_reject_non_numbers() -> None:
    with pytest.raises(SystemExit, match="invalid question number"):
        parse_numbers(["1,not-a-question"])
