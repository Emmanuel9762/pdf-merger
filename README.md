# PDF Merger

A Python desktop application and CLI tool for merging PDF files.

## Features

- Merge multiple PDF files into a single document
- Discover PDFs from an input directory
- Select PDFs directly from the GUI
- Drag and drop PDF files into the GUI
- Reorder PDFs before merging
- Display PDF page counts and file sizes
- Choose the output filename and location
- Prevent accidental output overwrites
- Run merges in a background worker
- Display merge progress
- Cancel an active merge
- Clean up partial output after cancellation or failure
- Validate merge requests
- CLI support for scripted and terminal-based workflows
- Automated test coverage
- PyInstaller packaging for a standalone Linux executable

## Requirements

- Python 3.12+
- pypdf
- PySide6

Development additionally requires:

- pytest
- PyInstaller

## Installation

Clone the repository and create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```
Install the application dependencies:

```
python3 -m pip install -r requirements.txt
```
For development:

```
python3 -m pip install -r requirements-dev.txt
```
The project can also be installed in editable mode:

```
python3 -m pip install -e .
```

## Running the GUI
From the project directory:

```
python3 -m gui.main
```
Or:

```
python3 gui_launcher.py
```
When installed through `pyproject.toml`, the GUI can also be launched with:

```
pdf-merger
```

## CLI Usage
The CLI can merge PDFs from the default `input` directory:

```
python3 main.py
```
PDF files can also be supplied directly:

```
python3 main.py file1.pdf file2.pdf file3.pdf
```
Specify an input directory:

```
python3 main.py --input input
```
Specify an output file:

```
python3 main.py --output output/merged.pdf
```
Specify the merge order:

```
python3 main.py --order 3 1 4 2
```
Arguments can be combined:

```
python3 main.py --input input --output output/merged.pdf --order 3 1 4 2
```

## Running Tests
Run the complete test suite:

```
python3 -m pytest -q
```
The project currently contains tests covering the merger, PDF metadata handling, GUI behavior, project configuration, and packaging configuration.

## Building the Standalone Executable
PyInstaller is included in the development requirements.

Build the Linux executable with:

```
python3 -m PyInstaller --clean --noconfirm pdf_merger.spec
```
The executable is created at:

```
dist/pdf-merger
```
The generated `build/` and `dist/` directories are ignored by Git.

## Project Structure

```
pdf-merger/
├── gui/
│   ├── app.py
│   ├── main.py
│   └── worker.py
├── pdf_merger/
│   ├── merger.py
│   └── pdf_info.py
├── tests/
│   ├── test_gui.py
│   ├── test_merger.py
│   ├── test_packaging.py
│   ├── test_pdf_info.py
│   └── test_project_config.py
├── input/
├── main.py
├── gui_launcher.py
├── pdf_merger.spec
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

## Architecture
The project separates PDF-processing logic from the GUI layer.

- `pdf_merger/` contains the reusable PDF processing functionality.
- `gui/` contains the PySide6 desktop interface and background worker.
- `main.py` provides the CLI interface.
- `tests/` contains automated regression and configuration tests.
- `pdf_merger.spec` defines the PyInstaller build.
The GUI performs PDF merging in a background thread so the interface remains responsive during processing.

## Platform
The application is developed and tested on Linux.

The PyInstaller configuration currently targets a standalone Linux executable. Cross-platform packaging has not yet been configured.

## Status
The project is currently in active development.
