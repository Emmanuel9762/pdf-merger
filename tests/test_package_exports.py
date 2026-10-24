"""Guard against malformed package exports breaking both entry points."""

import ast
from pathlib import Path

import pdf_merger


def test_package_initializer_is_valid_python():
    initializer = Path(pdf_merger.__file__)
    ast.parse(initializer.read_text(encoding="utf-8"), filename=str(initializer))


def test_all_v02_operations_are_importable():
    for name in (
        "merge_files",
        "split_pdf",
        "extract_pages",
        "rotate_pages",
        "delete_pages",
        "reorder_pages",
    ):
        assert callable(getattr(pdf_merger, name))


def test_all_v02_operations_are_exposed_to_cli():
    from main import (
        build_delete_parser,
        build_extract_parser,
        build_merge_parser,
        build_reorder_parser,
        build_rotate_parser,
        build_split_parser,
    )

    for parser_factory in (
        build_merge_parser,
        build_split_parser,
        build_extract_parser,
        build_rotate_parser,
        build_delete_parser,
        build_reorder_parser,
    ):
        assert parser_factory().prog
