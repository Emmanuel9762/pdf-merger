from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class OperationState(str, Enum):
    SUCCESS = "success"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class OperationResult:
    state: OperationState
    outputs: tuple[Path, ...] = ()
    pages_processed: int = 0
    error: str | None = None
    current_file: Path | None = None

    @property
    def succeeded(self) -> bool:
        return self.state is OperationState.SUCCESS

    @property
    def cancelled(self) -> bool:
        return self.state is OperationState.CANCELLED

    @property
    def failed(self) -> bool:
        return self.state is OperationState.FAILED
