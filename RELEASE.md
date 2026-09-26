# PDF Merger 0.1.0rc1

Linux release candidate. This version labels the source package; it is not a
published release or a guarantee that every Linux desktop has been tested.

## Included

- CLI with explicit files or directory discovery, ordering, and overwrite confirmation.
- PySide6 GUI with drag and drop ordering, metadata, progress, and cancellation.
- Shared merge service and output path policy with temporary output cleanup.
- Automated tests and a Linux PyInstaller build in CI.

## Validation before a public release

1. In one Python 3.12+ virtual environment, install `requirements-dev.txt`,
   run `python -m pytest -q`, and build with
   `python -m PyInstaller --clean --noconfirm pdf_merger.spec`.
2. Run `python main.py --help` and merge two known PDFs through the CLI.
3. Launch `dist/pdf-merger` in a real Linux desktop session. Add and reorder
   two PDFs, merge them, then inspect the output page count and order.
4. Confirm overwrite decline leaves the previous file intact. Cancel an
   active merge and check that no partial output remains.
5. Check CI results and the uploaded Linux executable and checksum. Verify
   a downloaded file with `sha256sum -c pdf-merger.sha256` from its directory.

## Limits

- The PyInstaller executable is Linux x86-64; Windows and macOS builds are
  outside this candidate.
- The headless CI launch shows that the packaged process starts and remains
  running. It does not test rendering or every desktop library combination.
- Cancellation is checked between input PDFs. A request during the final
  write may finish before cancellation is observed.
