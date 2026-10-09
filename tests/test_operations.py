from pathlib import Path

from pdf_merger.operations import OperationResult, OperationState


def test_success_result_exposes_outputs_and_page_count():
    outputs = (Path("part-1.pdf"), Path("part-2.pdf"))
    result = OperationResult(
        state=OperationState.SUCCESS,
        outputs=outputs,
        pages_processed=4,
    )

    assert result.succeeded is True
    assert result.cancelled is False
    assert result.failed is False
    assert result.outputs == outputs
    assert result.pages_processed == 4
    assert result.error is None


def test_cancelled_result_is_distinct_from_failure():
    result = OperationResult(
        state=OperationState.CANCELLED,
        pages_processed=2,
    )

    assert result.succeeded is False
    assert result.cancelled is True
    assert result.failed is False
    assert result.error is None


def test_failed_result_carries_error_context():
    source = Path("broken.pdf")
    result = OperationResult(
        state=OperationState.FAILED,
        error="Unable to read PDF",
        current_file=source,
    )

    assert result.failed is True
    assert result.succeeded is False
    assert result.cancelled is False
    assert result.current_file == source
    assert result.error == "Unable to read PDF"
