# v0.2 Release Readiness Checklist (development)

**Current version:** `0.2.0.dev0` on `v0.2.0-dev`.
**Status:** verification pending. This file is a checklist, not evidence that
any test or build has passed.

## Scope

v0.2 adds Split, Extract, Rotate, Delete, and Reorder alongside Merge, in the
core library, CLI, and six-tab desktop GUI. Merge retains its confirmed
overwrite behavior. The new page operations refuse existing output paths.

## Automated verification (must be run locally or in CI)

```bash
git switch v0.2.0-dev
git pull --ff-only origin v0.2.0-dev
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q
python3 scripts/release_preflight.py
git diff --check
git status --short
```

Record the actual test count and failures. **Do not tag** if any test or
preflight step fails. Do not treat a clean Git diff as a test result.

## Manual GUI smoke (Linux desktop)

```bash
python3 -m gui.main
```

- [ ] App starts and displays **PDF Toolkit** with six operation tabs.
- [ ] Merge preserves selected file order and requires confirmation to overwrite.
- [ ] Split with `1-2, 3` creates expected separate parts.
- [ ] Extract with `3, 1` creates a two-page PDF in that order.
- [ ] Rotate selected page(s) without changing other pages.
- [ ] Delete page 2 from a three-page PDF; resulting file has two pages.
- [ ] Reorder a four-page PDF using `4, 2, 1, 3`.
- [ ] Invalid ranges and incomplete reorder orders show useful errors.
- [ ] Existing output files are preserved for page operations.
- [ ] Cancel a running operation and confirm no partial output remains.
- [ ] Closing the window during an active job is blocked with a neutral warning.
- [ ] File list, status, progress, and controls restore after completion.

Use throwaway PDFs and inspect the **actual resulting pages**, not just
success dialogs.

## CLI smoke

Run the examples in README.md against disposable PDFs and verify exit codes,
page order, output locations, and no-clobber behavior.

## Packaging and release gate

```bash
python3 -m PyInstaller --clean --noconfirm pdf_merger.spec
./dist/pdf-merger
```

- [ ] The packaged Linux executable launches on a desktop.
- [ ] At least Merge and Reorder succeed in the packaged build.
- [ ] Python distribution build and validation succeed in CI.
- [ ] Release notes and `pyproject.toml` versions match the intended tag.
- [ ] A candidate version is selected and verified before tagging.
- [ ] GitHub release assets and SHA-256 checksums are checked after publishing.

The existing `RELEASE.md` intentionally documents **0.1.0**. Do not replace
its heading with v0.2 until the actual release version and verification results
are settled. `scripts/release_preflight.py --tag ...` requires matching
version metadata and release notes.

## Deferred

Page thumbnails and drag-to-reorder page previews, cross-platform installers,
and additional PDF transformation features are **not** part of this v0.2 gate.
