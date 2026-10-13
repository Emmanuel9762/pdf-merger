from pathlib import Path

from gui.worker import ExtractWorker
from pdf_merger import OperationResult, OperationState


def test_extract_worker_forwards_success_and_progress(monkeypatch):
    import gui.worker as worker_module

    source = Path("input/source.pdf")
    output = Path("output/selected.pdf")
    worker = ExtractWorker(source, output, [(1, 2)])

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

    def fake_extract_pages(
        pdf_file,
        target,
        ranges,
        progress_callback=None,
        cancel_callback=None,
    ):
        assert pdf_file == source
        assert target == output
        assert ranges == [(1, 2)]
        assert cancel_callback() is False
        progress_callback(1, 2, source)
        progress_callback(2, 2, source)
        return OperationResult(
            state=OperationState.SUCCESS,
            outputs=(output,),
            pages_processed=2,
        )

    monkeypatch.setattr(worker_module, "extract_pages", fake_extract_pages)

    worker.run()

    assert progress_events == [
        (1, 2, source),
        (2, 2, source),
    ]
    assert len(finished_events) == 1
    assert finished_events[0].outputs == (output,)
    assert failed_events == []
    assert cancelled_events == []


def test_extract_worker_emits_cancelled(monkeypatch):
    import gui.worker as worker_module

    worker = ExtractWorker(
        Path("input/source.pdf"),
        Path("output/selected.pdf"),
        [(1, 1)],
    )
    events = []

    worker.finished.connect(lambda *_: events.append("finished"))
    worker.failed.connect(lambda *_: events.append("failed"))
    worker.cancelled.connect(lambda: events.append("cancelled"))

    def fake_extract_pages(*args, cancel_callback=None, **kwargs):
        worker.cancel()
        assert cancel_callback() is True
        return OperationResult(state=OperationState.CANCELLED)

    monkeypatch.setattr(worker_module, "extract_pages", fake_extract_pages)

    worker.run()

    assert events == ["cancelled"]


def test_extract_worker_emits_failure(monkeypatch):
    import gui.worker as worker_module

    source = Path("input/source.pdf")
    worker = ExtractWorker(
        source,
        Path("output/selected.pdf"),
        [(1, 1)],
    )
    failures = []

    worker.failed.connect(lambda *args: failures.append(args))

    monkeypatch.setattr(
        worker_module,
        "extract_pages",
        lambda *args, **kwargs: OperationResult(
            state=OperationState.FAILED,
            error="bad range",
            current_file=source,
        ),
    )

    worker.run()

    assert failures == [("bad range", source)]
