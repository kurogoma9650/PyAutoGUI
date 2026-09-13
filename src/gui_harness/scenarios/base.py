from __future__ import annotations

from abc import ABC, abstractmethod

from ..core.context import RunContext


class Scenario(ABC):
    name: str
    application: str

    def setup(self, ctx: RunContext) -> None:
        pass

    @abstractmethod
    def run(self, ctx: RunContext) -> None:
        raise NotImplementedError

    def cleanup(self, ctx: RunContext) -> None:
        pass
