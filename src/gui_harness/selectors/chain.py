from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class SelectorChain:
    selectors: tuple[Any, ...]

    def __init__(self, selectors: Iterable[Any]) -> None:
        object.__setattr__(self, "selectors", tuple(selectors))
        if not self.selectors:
            raise ValueError("SelectorChain requires at least one selector.")
