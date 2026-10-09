import argparse
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PreflightError(RuntimeError):
    pass


def load_project_version(project_root=PROJECT_ROOT):
    pyproject = project_root / "pyproject.toml"

    if not pyproject.is_file():
        raise PreflightError("Missing pyproject.toml.")

    with pyproject.open("rb") as file:
        config = tomllib.load(file)

    try:
        version = config["project"]["version"]
    except KeyError as error:
        raise PreflightError("Project version is not defined in pyproject.toml.") from error

    if not isinstance(version, str) or not version.strip():
        raise PreflightError("Project version must be a non-empty string.")

    return version.strip()


def validate_release(project_root=PROJECT_ROOT, tag=None):
    version = load_project_version(project_root)

    required_files = (
        "README.md",
        "RELEASE.md",
        "pdf_merger.spec",
        ".github/workflows/release.yml",
    )

    missing = [
        relative_path
        for relative_path in required_files
        if not (project_root / relative_path).is_file()
    ]

    if missing:
        raise PreflightError(
            "Missing release files: " + ", ".join(missing)
        )

    readme = (project_root / "README.md").read_text(encoding="utf-8")
    release_notes = (project_root / "RELEASE.md").read_text(encoding="utf-8")

    if f"Version `{version}`" not in readme:
        raise PreflightError(
            f"README.md does not declare Version `{version}`."
        )

    if tag is not None:
        if not tag.startswith("v"):
            raise PreflightError("Release tag must start with 'v'.")

        tag_version = tag[1:]

        if tag_version != version:
            raise PreflightError(
                f"Tag version {tag_version} does not match project version {version}."
            )

        expected_heading = f"# PDF Merger {version}\n"

        if not release_notes.startswith(expected_heading):
            raise PreflightError(
                f"RELEASE.md must start with {expected_heading.strip()!r}."
            )

    return version


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate PDF Merger development or release metadata."
    )
    parser.add_argument(
        "--tag",
        help="Optional Git tag to validate, for example v0.1.0.",
    )
    args = parser.parse_args(argv)

    try:
        version = validate_release(tag=args.tag)
    except PreflightError as error:
        print(f"Release preflight failed: {error}")
        return 1

    print(f"Release preflight passed for {version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
