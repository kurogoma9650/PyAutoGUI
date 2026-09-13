from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class RunStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"
    ABORTED = "ABORTED"


class CoordinateSpace(StrEnum):
    SCREEN = "screen"
    WINDOW = "window"
    CLIENT = "client"
    NORMALIZED_CLIENT = "normalized_client"


@dataclass(frozen=True)
class Rect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return max(0, self.right - self.left)

    @property
    def height(self) -> int:
        return max(0, self.bottom - self.top)

    @property
    def center(self) -> tuple[int, int]:
        return (self.left + self.width // 2, self.top + self.height // 2)

    def contains(self, x: int, y: int) -> bool:
        return self.left <= x < self.right and self.top <= y < self.bottom


@dataclass(frozen=True)
class ClientPoint:
    x: int
    y: int


@dataclass(frozen=True)
class RelativePoint:
    x: float
    y: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.x < 1.0 and 0.0 <= self.y < 1.0):
            raise ValueError("RelativePoint coordinates must be in [0, 1).")


@dataclass(frozen=True)
class ScreenPoint:
    x: int
    y: int


@dataclass(frozen=True)
class WindowInfo:
    hwnd: int
    pid: int
    process_name: str
    title: str
    window_rect: Rect
    client_rect: Rect
    visible: bool
    minimized: bool
    session_id: int


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: RunStatus
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "status": self.status.value, "detail": self.detail}
