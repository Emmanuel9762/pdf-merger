from argparse import Namespace

import pytest
from pypdf import PdfReader, PdfWriter

from main import run


def create_test_pdf(path, page_count, width):
    writer = PdfWriter()

    for _ in range(page_count):
        writer.add_blank_page(width=width, height=792)

    with open(path, "wb") as file:
        writer.write(file)


def test_run_merges_explicit_files(
    tmp_path,
    mock_pdf_1,
    mock_pdf_2,
):
    output_file = tmp_path / "merged.pdf"

    args = Namespace(
        files=[str(mock_pdf_1), str(mock_pdf_2)],
        input="input",
        output=str(output_file),
        order=None,
    )

    result = run(args)

    assert result == 0
    assert output_file.exists()
    assert len(PdfReader(output_file).pages) == 3


def test_run_discovers_and_orders_input_files(
    tmp_path,
    mock_pdf_1,
    mock_pdf_2,
    mock_pdf_3,
    mock_pdf_4,
):
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    for pdf_file in (
        mock_pdf_1,
        mock_pdf_2,
        mock_pdf_3,
        mock_pdf_4,
    ):
        (input_dir / pdf_file.name).write_bytes(pdf_file.read_bytes())

    output_file = tmp_path / "merged.pdf"

    args = Namespace(
        files=[],
        input=str(input_dir),
        output=str(output_file),
        order=[3, 1, 4, 2],
    )

    result = run(args)

    assert result == 0
    assert output_file.exists()

    reader = PdfReader(output_file)
    assert len(reader.pages) == 10


def test_run_rejects_invalid_order(
    tmp_path,
    mock_pdf_1,
    mock_pdf_2,
):
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    for pdf_file in (mock_pdf_1, mock_pdf_2):
        (input_dir / pdf_file.name).write_bytes(pdf_file.read_bytes())

    output_file = tmp_path / "merged.pdf"

    args = Namespace(
        files=[],
        input=str(input_dir),
        output=str(output_file),
        order=[1, 1],
    )

    result = run(args)

    assert result == 1
    assert not output_file.exists()


def test_run_rejects_missing_input_directory(tmp_path):
    args = Namespace(
        files=[],
        input=str(tmp_path / "missing"),
        output=str(tmp_path / "merged.pdf"),
        order=None,
    )

    result = run(args)

    assert result == 1


def test_run_rejects_empty_input_directory(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    args = Namespace(
        files=[],
        input=str(input_dir),
        output=str(tmp_path / "merged.pdf"),
        order=None,
    )

    result = run(args)

    assert result == 1


def test_run_rejects_existing_output(
    tmp_path,
    mock_pdf_1,
    mock_pdf_2,
):
    output_file = tmp_path / "merged.pdf"
    output_file.write_text("existing output")

    args = Namespace(
        files=[str(mock_pdf_1), str(mock_pdf_2)],
        input="input",
        output=str(output_file),
        order=None,
    )

    result = run(args, input_func=lambda _: "n")

    assert result == 1
    assert output_file.read_text() == "existing output"


@pytest.mark.parametrize("pages, expected_status", [(2, 0), (None, 1)])
def test_run_uses_merge_files_boundary(monkeypatch, tmp_path, mock_pdf_1, pages, expected_status):
    import main as cli

    output = tmp_path / "merged.pdf"
    calls = []

    def fake_merge_files(files, target, error_callback=None):
        calls.append((files, target))
        return pages

    monkeypatch.setattr(cli, "merge_files", fake_merge_files)
    args = Namespace(files=[str(mock_pdf_1)], input="input", output=str(output), order=None)

    assert run(args) == expected_status
    assert calls == [([mock_pdf_1], output)]


def test_run_reports_merge_failure_details(monkeypatch, tmp_path, mock_pdf_1, capsys):
    import main as cli

    output = tmp_path / "merged.pdf"

    def fake_merge_files(files, target, error_callback=None):
        error_callback("Password required", files[0])
        return None

    monkeypatch.setattr(cli, "merge_files", fake_merge_files)
    args = Namespace(files=[str(mock_pdf_1)], input="input", output=str(output), order=None)

    assert run(args) == 1

    captured = capsys.readouterr()
    assert "Merge failed while processing: mock_pdf_1.pdf" in captured.out
    assert "Reason: Password required" in captured.out


@pytest.mark.parametrize("error_type", [EOFError, KeyboardInterrupt])
def test_main_handles_interrupted_input(monkeypatch, capsys, error_type):
    import main as cli

    def interrupt():
        raise error_type()

    monkeypatch.setattr(cli, "parse_args", interrupt)

    assert cli.main() == 130
    assert "Merge cancelled." in capsys.readouterr().out


@pytest.fixture
def mock_pdf_1(tmp_path):
    pdf_file = tmp_path / "mock_pdf_1.pdf"
    create_test_pdf(pdf_file, 1, 612)
    return pdf_file


@pytest.fixture
def mock_pdf_2(tmp_path):
    pdf_file = tmp_path / "mock_pdf_2.pdf"
    create_test_pdf(pdf_file, 2, 612)
    return pdf_file


@pytest.fixture
def mock_pdf_3(tmp_path):
    pdf_file = tmp_path / "mock_pdf_3.pdf"
    create_test_pdf(pdf_file, 3, 612)
    return pdf_file


@pytest.fixture
def mock_pdf_4(tmp_path):
    pdf_file = tmp_path / "mock_pdf_4.pdf"
    create_test_pdf(pdf_file, 4, 612)
    return pdf_file
