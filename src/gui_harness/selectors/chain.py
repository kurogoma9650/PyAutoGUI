from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SelectorChain:
    selectors: tuple[Any, ...]

    def __init__(self, selectors: Iterable[Any]) -> None:
        object.__setattr__(self, "selectors", tuple(selectors))
        if not self.selectors:
            raise ValueError("SelectorChain requires at least one selector.")
