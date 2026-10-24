# PDF Toolkit (PDF Merger)

A Python/PySide6 desktop application and CLI for organizing PDF documents. The
repository and installable package retain the `pdf-merger` name for compatibility.

## Features

- **Merge:** combine multiple PDFs in a chosen file order.
- **Split:** create one PDF per page or one per specified page range.
- **Extract:** combine selected pages/ranges into one new PDF, preserving the
  requested order (including repeated pages).
- **Rotate:** rotate all pages or selected pages by 90°, 180°, or 270°.
- **Delete:** remove selected pages, keeping the remaining pages in order.
  Removing every page is rejected.
- **Reorder:** supply a complete one-based page permutation, with every page
  included exactly once.

The GUI provides six operation tabs, drag-and-drop file selection, file metadata,
progress, cancellation, and background workers. Merge supports confirmed
overwrite; the other operations refuse to overwrite existing output files.
Operations use staged output publication and clean up temporary files on
cancellation or failure.

## Requirements

- Python 3.12+
- Linux desktop for the currently supported standalone executable
- Runtime: `pypdf` and `PySide6`
- Development: `pytest`, `PyInstaller`, and other packages in
  `requirements-dev.txt`

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
```

On fish, activate with `source .venv/bin/activate.fish`. For runtime-only
installation, use `requirements.txt` instead.

## Desktop GUI

```bash
python3 -m gui.main
```

Alternative entry points: `python3 gui_launcher.py`, or `pdf-merger` after
installing the project with `python3 -m pip install -e .`.

Add PDFs to the file list. Merge uses the full ordered list; Split, Extract,
Rotate, Delete, and Reorder use the selected PDF. All page numbers are
**one-based**. Use comma-separated ranges in the GUI, e.g. `2-3, 5`. Reorder
requires a complete comma-separated list, e.g. `4, 2, 1, 3` for a four-page
document. Outputs are new PDF files; originals are not modified.

## CLI

Merge is the default command and retains the v0.1 CLI syntax:

```bash
python3 main.py file1.pdf file2.pdf --output output/merged.pdf
python3 main.py --input input --order 2 1 --output output/merged.pdf
```

The v0.2 page operations use subcommands:

```bash
python3 main.py split report.pdf --range 1-3 --range 4-6 --output output/parts
python3 main.py extract report.pdf --range 4-5 --range 2 --output output/extracted.pdf
python3 main.py rotate report.pdf --degrees 90 --range 2-3 --output output/rotated.pdf
python3 main.py delete report.pdf --range 2-3 --range 5 --output output/trimmed.pdf
python3 main.py reorder report.pdf --order 4 2 1 3 --output output/reordered.pdf
```

For Split and Rotate, omit `--range` to operate on every page. For Extract
and Delete, at least one range is required. The `--order` argument to Reorder
must include each source page exactly once. Without `--output`, page
operations create files in the `output/` directory (Split uses a subdirectory).
See the individual command `--help` options for details.

## Verification

```bash
python3 -m pytest -q
python3 scripts/release_preflight.py
git diff --check
```

For a headless GUI smoke test, set `QT_QPA_PLATFORM=offscreen` before running
GUI tests. For a release, follow the manual checks in
[`V02_RELEASE_CHECKLIST.md`](V02_RELEASE_CHECKLIST.md).

## Packaging

The project includes `pdf_merger.spec` for PyInstaller:

```bash
python3 -m PyInstaller --clean --noconfirm pdf_merger.spec
```

The Linux executable is produced at `dist/pdf-merger`. Build it with the same
Python environment used for dependencies and tests. CI includes Linux packaging
checks; an offscreen process check does **not** replace visual desktop testing.
Windows/macOS standalone builds are not yet configured.

## Project layout

- `pdf_merger/`: reusable core services and operation results
- `gui/`: PySide6 interface and operation workers
- `main.py`: CLI
- `tests/`: core, CLI, GUI, and packaging regression tests
- `scripts/release_preflight.py`: release metadata checks
- `pdf_merger.spec`: Linux executable build configuration

## Status

Version `0.2.0.dev0` is the active development version, **not a published
v0.2 release**. The stable 0.1.0 release remains documented in
[`RELEASE.md`](RELEASE.md). The v0.2 feature set is implemented but must pass
the full test suite, GUI smoke checks, and packaging checks before a release
candidate can be declared.
