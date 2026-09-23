from pathlib import Path

from pdf_merger import resolve_output_path


def test_resolve_output_path_uses_output_directory_for_relative_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = resolve_output_path("merged")

    assert result == Path("output/merged.pdf")
    assert (tmp_path / "output").is_dir()


def test_resolve_output_path_preserves_pdf_extension(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = resolve_output_path("merged.pdf")

    assert result == Path("output/merged.pdf")


def test_resolve_output_path_adds_pdf_extension_when_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = resolve_output_path("report")

    assert result == Path("output/report.pdf")


def test_resolve_output_path_handles_nested_relative_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = resolve_output_path("reports/merged")

    assert result == Path("output/reports/merged.pdf")
    assert (tmp_path / "output" / "reports").is_dir()


def test_resolve_output_path_preserves_absolute_path(tmp_path):
    output_path = tmp_path / "exports" / "merged.pdf"

    result = resolve_output_path(output_path)

    assert result == output_path
    assert output_path.parent.is_dir()


def test_resolve_output_path_adds_pdf_extension_to_absolute_path(tmp_path):
    output_path = tmp_path / "exports" / "merged"

    result = resolve_output_path(output_path)

    assert result == tmp_path / "exports" / "merged.pdf"
    assert (tmp_path / "exports").is_dir()


def test_resolve_output_path_does_not_delete_existing_file(tmp_path):
    output_file = tmp_path / "existing.pdf"
    output_file.write_text("already here")

    result = resolve_output_path(output_file)

    assert result == output_file
    assert output_file.read_text() == "already here"
