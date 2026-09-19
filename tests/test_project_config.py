from pathlib import Path

import tomllib

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_project_metadata_is_defined():
    pyproject = PROJECT_ROOT / "pyproject.toml"

    with pyproject.open("rb") as file:
        config = tomllib.load(file)

    project = config["project"]

    assert project["name"] == "pdf-merger"
    assert project["version"] == "0.1.0"
    assert project["requires-python"] == ">=3.12"


def test_runtime_dependencies_are_declared():
    pyproject = PROJECT_ROOT / "pyproject.toml"

    with pyproject.open("rb") as file:
        config = tomllib.load(file)

    dependencies = config["project"]["dependencies"]

    assert any(
        dependency.startswith("pypdf")
        for dependency in dependencies
    )

    assert any(
        dependency.startswith("PySide6")
        for dependency in dependencies
    )


def test_console_entry_point_is_defined():
    pyproject = PROJECT_ROOT / "pyproject.toml"

    with pyproject.open("rb") as file:
        config = tomllib.load(file)

    scripts = config["project"]["scripts"]

    assert scripts["pdf-merger"] == "gui.main:main"
