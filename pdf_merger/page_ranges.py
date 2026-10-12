from __future__ import annotations

PageRange = tuple[int, int]


def parse_page_range(value: str) -> PageRange:
    value = value.strip()
    parts = value.split("-")

    try:
        if len(parts) == 1:
            start = end = int(parts[0])
        elif len(parts) == 2:
            start, end = (int(part.strip()) for part in parts)
        else:
            raise ValueError
    except ValueError as error:
        raise ValueError(
            f"Invalid page range: {value!r}. Use PAGE or START-END."
        ) from error

    if start < 1 or end < start:
        raise ValueError(
            f"Invalid page range: {value!r}. Pages must be positive and ordered."
        )

    return start, end


def parse_page_ranges(value: str) -> tuple[PageRange, ...] | None:
    value = value.strip()

    if not value:
        return None

    return tuple(
        parse_page_range(part)
        for part in value.split(",")
        if part.strip()
    )
