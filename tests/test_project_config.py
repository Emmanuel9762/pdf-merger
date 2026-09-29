from pathlib import Path

import tomllib

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_project_config():
    pyproject = PROJECT_ROOT / "pyproject.toml"

    with pyproject.open("rb") as file:
        return tomllib.load(file)


def test_project_metadata_is_defined():
    project = load_project_config()["project"]

    assert project["name"] == "pdf-merger"
    assert project["version"] == "0.1.0rc1"
    assert project["requires-python"] == ">=3.12"


def test_runtime_dependencies_are_declared():
    dependencies = load_project_config()["project"]["dependencies"]

    assert any(
        dependency.startswith("pypdf")
        for dependency in dependencies
    )

    assert any(
        dependency.startswith("PySide6")
        for dependency in dependencies
    )


def test_console_entry_point_is_defined():
    scripts = load_project_config()["project"]["scripts"]

    assert scripts["pdf-merger"] == "gui.main:main"


def test_release_version_is_consistent_across_docs():
    version = load_project_config()["project"]["version"]
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    release_notes = (PROJECT_ROOT / "RELEASE.md").read_text(encoding="utf-8")

    assert f"Version `{version}`" in readme
    assert release_notes.startswith(f"# PDF Merger {version}\n")
