from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RELEASE_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "release.yml"


def read_release_workflow():
    return RELEASE_WORKFLOW.read_text(encoding="utf-8")


def test_release_workflow_runs_only_for_version_tags():
    workflow = read_release_workflow()

    assert 'tags:' in workflow
    assert '- "v*"' in workflow


def test_release_workflow_has_minimum_write_permission():
    workflow = read_release_workflow()

    assert "permissions:" in workflow
    assert "contents: write" in workflow


def test_release_workflow_rejects_version_mismatch():
    workflow = read_release_workflow()

    assert 'Path("pyproject.toml")' in workflow
    assert 'GITHUB_REF_NAME#v' in workflow
    assert 'does not match project version' in workflow


def test_release_workflow_validates_before_publishing():
    workflow = read_release_workflow()

    tests = workflow.index("python -m pytest -q")
    build = workflow.index("python -m PyInstaller")
    smoke = workflow.index("timeout 3s ./dist/pdf-merger")
    checksum = workflow.index("sha256sum pdf-merger")
    publish = workflow.index("gh release")

    assert tests < build < smoke < checksum < publish


def test_release_workflow_supports_safe_reruns():
    workflow = read_release_workflow()

    assert 'gh release view "$GITHUB_REF_NAME"' in workflow
    assert "gh release upload" in workflow
    assert "--clobber" in workflow
    assert "gh release create" in workflow
