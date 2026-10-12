import pytest

from pdf_merger import parse_page_range, parse_page_ranges


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1", (1, 1)),
        ("2-5", (2, 5)),
        (" 7-9 ", (7, 9)),
    ],
)
def test_parse_page_range(value, expected):
    assert parse_page_range(value) == expected


def test_parse_page_ranges_accepts_comma_separated_values():
    assert parse_page_ranges("1-3, 5, 7-9") == (
        (1, 3),
        (5, 5),
        (7, 9),
    )


def test_parse_page_ranges_blank_means_default_split():
    assert parse_page_ranges("") is None
    assert parse_page_ranges("   ") is None


@pytest.mark.parametrize("value", ["0", "3-2", "1-2-3", "x", "1-x"])
def test_parse_page_ranges_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        parse_page_ranges(value)
