from pathlib import Path

from gui.worker import ReorderWorker
from pdf_merger import OperationResult, OperationState


def test_reorder_worker_forwards_success_and_progress(monkeypatch):
    import gui.worker as worker_module

    source = Path("input/source.pdf")
    output = Path("output/reordered.pdf")
    worker = ReorderWorker(source, output, [3, 1, 2])

    progress_events = []
    finished_events = []

    worker.progress.connect(
        lambda current, total, path: progress_events.append(
            (current, total, path)
        )
    )
    worker.finished.connect(lambda result: finished_events.append(result))

    def fake_reorder_pages(
        pdf_file,
        target,
        order,
        progress_callback=None,
        cancel_callback=None,
    ):
        assert pdf_file == source
        assert target == output
        assert order == [3, 1, 2]
        assert cancel_callback() is False
        progress_callback(1, 3, source)
        progress_callback(2, 3, source)
        progress_callback(3, 3, source)
        return OperationResult(
            state=OperationState.SUCCESS,
            outputs=(output,),
            pages_processed=3,
        )

    monkeypatch.setattr(worker_module, "reorder_pages", fake_reorder_pages)
    worker.run()

    assert progress_events == [
        (1, 3, source),
        (2, 3, source),
        (3, 3, source),
    ]
    assert len(finished_events) == 1


def test_reorder_worker_emits_cancelled(monkeypatch):
    import gui.worker as worker_module

    worker = ReorderWorker(
        Path("input/source.pdf"),
        Path("output/reordered.pdf"),
        [2, 1],
    )
    events = []

    worker.finished.connect(lambda *_: events.append("finished"))
    worker.failed.connect(lambda *_: events.append("failed"))
    worker.cancelled.connect(lambda: events.append("cancelled"))

    def fake_reorder_pages(*args, cancel_callback=None, **kwargs):
        worker.cancel()
        assert cancel_callback() is True
        return OperationResult(state=OperationState.CANCELLED)

    monkeypatch.setattr(worker_module, "reorder_pages", fake_reorder_pages)
    worker.run()

    assert events == ["cancelled"]


def test_reorder_worker_emits_failure(monkeypatch):
    import gui.worker as worker_module

    source = Path("input/source.pdf")
    worker = ReorderWorker(
        source,
        Path("output/reordered.pdf"),
        [1, 1],
    )
    failures = []
    worker.failed.connect(lambda *args: failures.append(args))

    monkeypatch.setattr(
        worker_module,
        "reorder_pages",
        lambda *args, **kwargs: OperationResult(
            state=OperationState.FAILED,
            error="invalid permutation",
            current_file=source,
        ),
    )

    worker.run()

    assert failures == [("invalid permutation", source)]
