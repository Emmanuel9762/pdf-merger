from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def test_pyinstaller_spec_exists():
    spec_file = PROJECT_ROOT / "pdf_merger.spec"

    assert spec_file.is_file()

def test_pyinstaller_spec_targets_gui_entry_point():
    spec_file = PROJECT_ROOT / "pdf_merger.spec"

    content = spec_file.read_text()

    assert '["gui/main.py"]' in content
    assert 'name="pdf-merger"' in content
    assert "console=False" in content
