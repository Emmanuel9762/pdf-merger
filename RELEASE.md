# PDF Merger 0.1.0

First public Linux release of PDF Merger. The application is available as a
Python project and as a standalone Linux x86-64 executable produced by the
release workflow.

## Included

- CLI with explicit files or directory discovery, deterministic ordering, and overwrite confirmation.
- PySide6 GUI with drag and drop ordering, metadata, progress, and cancellation.
- Shared merge service and output path policy with atomic publication and temporary output cleanup.
- Protection against duplicate/aliased inputs and output paths that resolve to an input.
- Clear CLI failure reporting and clean interrupted-input handling.
- Automated regression coverage for corrupt input preservation, Unicode/spaced paths, release metadata, and release workflows.
- Linux PyInstaller packaging with versioned release assets and SHA-256 checksums.
- Python wheel/source-distribution validation in CI.

## Release validation

1. Run `python3 scripts/release_preflight.py --tag v0.1.0`.
2. Run `python3 -m pytest -q`.
3. Build Python distributions with `python3 -m build` and validate them with
   `python3 -m twine check dist/*`.
4. Build the standalone executable with
   `python3 -m PyInstaller --clean --noconfirm pdf_merger.spec`.
5. Launch `dist/pdf-merger` on a Linux desktop and perform a final merge smoke test.
6. Confirm the tagged GitHub release contains the versioned executable and matching SHA-256 checksum.

## Platform limits

- The standalone executable targets Linux x86-64; Windows and macOS builds are not included in 0.1.0.
- Headless CI verifies that the packaged process starts and remains running, but it cannot verify visual rendering on every Linux desktop environment.
- Cancellation is cooperative. A request arriving after the final publication boundary cannot undo an already-completed merge.
