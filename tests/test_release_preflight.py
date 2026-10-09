from pathlib import Path

import pytest

from scripts.release_preflight import PreflightError, validate_release


def write_release_fixture(tmp_path, version="0.2.0.dev0", release_version="0.1.0"):
    (tmp_path / ".github" / "workflows").mkdir(parents=True)

    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname = "pdf-merger"\nversion = "{version}"\n',
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        f"Status: Version `{version}` is in development.\n",
        encoding="utf-8",
    )
    (tmp_path / "RELEASE.md").write_text(
        f"# PDF Merger {release_version}\n\nRelease notes.\n",
        encoding="utf-8",
    )
    (tmp_path / "pdf_merger.spec").write_text("# spec\n", encoding="utf-8")
    (tmp_path / ".github" / "workflows" / "release.yml").write_text(
        "name: Release\n",
        encoding="utf-8",
    )


def test_development_preflight_allows_previous_release_notes(tmp_path):
    write_release_fixture(tmp_path)

    assert validate_release(tmp_path) == "0.2.0.dev0"


def test_release_preflight_accepts_matching_version_tag(tmp_path):
    write_release_fixture(
        tmp_path,
        version="0.2.0",
        release_version="0.2.0",
    )

    assert validate_release(tmp_path, tag="v0.2.0") == "0.2.0"


def test_release_preflight_rejects_tag_version_mismatch(tmp_path):
    write_release_fixture(
        tmp_path,
        version="0.2.0",
        release_version="0.2.0",
    )

    with pytest.raises(PreflightError, match="does not match project version"):
        validate_release(tmp_path, tag="v0.1.0")


def test_release_preflight_rejects_readme_version_drift(tmp_path):
    write_release_fixture(tmp_path)
    (tmp_path / "README.md").write_text(
        "Status: Version `0.1.0` is ready.\n",
        encoding="utf-8",
    )

    with pytest.raises(PreflightError, match="README.md"):
        validate_release(tmp_path)


def test_tagged_release_rejects_release_heading_drift(tmp_path):
    write_release_fixture(
        tmp_path,
        version="0.2.0",
        release_version="0.1.0",
    )

    with pytest.raises(PreflightError, match="RELEASE.md"):
        validate_release(tmp_path, tag="v0.2.0")


def test_release_preflight_rejects_missing_release_file(tmp_path):
    write_release_fixture(tmp_path)
    (tmp_path / "pdf_merger.spec").unlink()

    with pytest.raises(PreflightError, match="pdf_merger.spec"):
        validate_release(tmp_path)
