from pathlib import Path

from gui.worker import RotateWorker
from pdf_merger import OperationResult, OperationState


def test_rotate_worker_forwards_success_and_progress(monkeypatch):
    import gui.worker as worker_module

    source = Path("input/source.pdf")
    output = Path("output/rotated.pdf")
    worker = RotateWorker(source, output, 90, [(2, 3)])

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

    def fake_rotate_pages(
        pdf_file,
        target,
        degrees,
        ranges=None,
        progress_callback=None,
        cancel_callback=None,
    ):
        assert pdf_file == source
        assert target == output
        assert degrees == 90
        assert ranges == [(2, 3)]
        assert cancel_callback() is False
        progress_callback(1, 3, source)
        progress_callback(2, 3, source)
        progress_callback(3, 3, source)
        return OperationResult(
            state=OperationState.SUCCESS,
            outputs=(output,),
            pages_processed=3,
        )

    monkeypatch.setattr(worker_module, "rotate_pages", fake_rotate_pages)

    worker.run()

    assert progress_events == [
        (1, 3, source),
        (2, 3, source),
        (3, 3, source),
    ]
    assert len(finished_events) == 1
    assert finished_events[0].outputs == (output,)
    assert failed_events == []
    assert cancelled_events == []


def test_rotate_worker_emits_cancelled(monkeypatch):
    import gui.worker as worker_module

    worker = RotateWorker(
        Path("input/source.pdf"),
        Path("output/rotated.pdf"),
        180,
    )
    events = []

    worker.finished.connect(lambda *_: events.append("finished"))
    worker.failed.connect(lambda *_: events.append("failed"))
    worker.cancelled.connect(lambda: events.append("cancelled"))

    def fake_rotate_pages(*args, cancel_callback=None, **kwargs):
        worker.cancel()
        assert cancel_callback() is True
        return OperationResult(state=OperationState.CANCELLED)

    monkeypatch.setattr(worker_module, "rotate_pages", fake_rotate_pages)

    worker.run()

    assert events == ["cancelled"]


def test_rotate_worker_emits_failure(monkeypatch):
    import gui.worker as worker_module

    source = Path("input/source.pdf")
    worker = RotateWorker(
        source,
        Path("output/rotated.pdf"),
        270,
    )
    failures = []

    worker.failed.connect(lambda *args: failures.append(args))

    monkeypatch.setattr(
        worker_module,
        "rotate_pages",
        lambda *args, **kwargs: OperationResult(
            state=OperationState.FAILED,
            error="bad rotation",
            current_file=source,
        ),
    )

    worker.run()

    assert failures == [("bad rotation", source)]
