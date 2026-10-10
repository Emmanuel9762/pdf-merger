from pathlib import Path

import pytest

from gui.worker import SplitWorker
from pdf_merger import OperationResult, OperationState


def test_split_worker_forwards_success_and_progress(monkeypatch):
    import gui.worker as worker_module

    source = Path("input/source.pdf")
    output_dir = Path("output/source-parts")
    output = output_dir / "source_part-001_page-1.pdf"
    worker = SplitWorker(source, output_dir)

    progress_events = []
    finished_events = []
    failed_events = []
    cancelled_events = []

    worker.progress.connect(
        lambda current, total, path: progress_events.append(
            (current, total, path)
        )
    )
    worker.finished.connect(lambda result: finished_events.append(result))
    worker.failed.connect(lambda *args: failed_events.append(args))
    worker.cancelled.connect(lambda: cancelled_events.append(True))

    def fake_split_pdf(
        pdf_file,
        target_dir,
        ranges=None,
        progress_callback=None,
        cancel_callback=None,
    ):
        assert pdf_file == source
        assert target_dir == output_dir
        assert cancel_callback() is False
        progress_callback(1, 1, output)
        return OperationResult(
            state=OperationState.SUCCESS,
            outputs=(output,),
            pages_processed=1,
        )

    monkeypatch.setattr(worker_module, "split_pdf", fake_split_pdf)

    worker.run()

    assert progress_events == [(1, 1, output)]
    assert len(finished_events) == 1
    assert finished_events[0].succeeded is True
    assert failed_events == []
    assert cancelled_events == []


def test_split_worker_emits_cancelled(monkeypatch):
    import gui.worker as worker_module

    worker = SplitWorker(
        Path("input/source.pdf"),
        Path("output/source-parts"),
    )
    events = []

    worker.finished.connect(lambda *_: events.append("finished"))
    worker.failed.connect(lambda *_: events.append("failed"))
    worker.cancelled.connect(lambda: events.append("cancelled"))

    def fake_split_pdf(*args, cancel_callback=None, **kwargs):
        worker.cancel()
        assert cancel_callback() is True
        return OperationResult(state=OperationState.CANCELLED)

    monkeypatch.setattr(worker_module, "split_pdf", fake_split_pdf)

    worker.run()

    assert events == ["cancelled"]


def test_split_worker_emits_failure(monkeypatch):
    import gui.worker as worker_module

    source = Path("input/source.pdf")
    worker = SplitWorker(source, Path("output/source-parts"))
    failures = []

    worker.failed.connect(lambda *args: failures.append(args))

    monkeypatch.setattr(
        worker_module,
        "split_pdf",
        lambda *args, **kwargs: OperationResult(
            state=OperationState.FAILED,
            error="bad range",
            current_file=source,
        ),
    )

    worker.run()

    assert failures == [("bad range", source)]
