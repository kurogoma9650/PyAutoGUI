from __future__ import annotations

from ..base import Scenario


class PhraseCollectorSmokeScenario(Scenario):
    name = "phrase_collector.smoke"
    application = "phrase_collector"

    def run(self, ctx) -> None:
        ctx.focus_window()
        ctx.wait.visual_stable(timeout=4.0)
        ctx.capture("smoke")
