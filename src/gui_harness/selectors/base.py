from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UIASelector:
    name: str | None = None
    control_type: str | None = None
    automation_id: str | None = None


@dataclass(frozen=True)
class ImageSelector:
    template: str
    confidence: float = 0.90
