from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RELEASE_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "release.yml"
CI_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"


def read_release_workflow():
    return RELEASE_WORKFLOW.read_text(encoding="utf-8")


def read_ci_workflow():
    return CI_WORKFLOW.read_text(encoding="utf-8")


def test_release_workflow_runs_only_for_version_tags():
    workflow = read_release_workflow()

    assert 'tags:' in workflow
    assert '- "v*"' in workflow


def test_release_workflow_has_minimum_write_permission():
    workflow = read_release_workflow()

    assert "permissions:" in workflow
    assert "contents: write" in workflow


def test_ci_uses_shared_release_preflight():
    workflow = read_ci_workflow()

    assert "python scripts/release_preflight.py" in workflow


def test_release_workflow_uses_shared_tag_preflight():
    workflow = read_release_workflow()

    assert 'python scripts/release_preflight.py --tag "$GITHUB_REF_NAME"' in workflow
    assert 'with Path("pyproject.toml").open' not in workflow


def test_release_workflow_validates_before_publishing():
    workflow = read_release_workflow()

    preflight = workflow.index("python scripts/release_preflight.py")
    tests = workflow.index("python -m pytest -q")
    build = workflow.index("python -m PyInstaller")
    smoke = workflow.index("timeout 3s ./dist/pdf-merger")
    checksum = workflow.index('sha256sum "$asset"')
    publish = workflow.index("gh release")

    assert preflight < tests < build < smoke < checksum < publish


def test_release_workflow_uses_versioned_linux_assets():
    workflow = read_release_workflow()

    assert 'asset="pdf-merger-linux-x86_64-${version}"' in workflow
    assert 'echo "RELEASE_ASSET=$asset" >> "$GITHUB_ENV"' in workflow
    assert '"dist/$RELEASE_ASSET"' in workflow
    assert '"dist/$RELEASE_ASSET.sha256"' in workflow


def test_release_workflow_supports_safe_reruns():
    workflow = read_release_workflow()

    assert 'gh release view "$GITHUB_REF_NAME"' in workflow
    assert "gh release upload" in workflow
    assert "--clobber" in workflow
    assert "gh release create" in workflow
