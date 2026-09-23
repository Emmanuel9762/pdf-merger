from pathlib import Path


def resolve_output_path(output_path, output_dir="output"):
    """Normalize an output path to a PDF file under the chosen output directory."""
    path = Path(output_path)

    if not path.is_absolute():
        path = Path(output_dir) / path

    if path.suffix.lower() != ".pdf":
        path = path.with_suffix(".pdf")

    path.parent.mkdir(parents=True, exist_ok=True)

    return path
