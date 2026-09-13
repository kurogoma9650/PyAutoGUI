from __future__ import annotations

from ..base import Scenario


class PhraseCollectorPhase8ReviewScenario(Scenario):
    """Collects review evidence; it does not make Human Review judgments."""

    name = "phrase_collector.phase8_review"
    application = "phrase_collector"

    def run(self, ctx) -> None:
        ctx.focus_window()
        ctx.capture("startup")
        ctx.wait.visual_stable(timeout=4.0)
        ctx.capture("workspace_stable")
        ctx.recorder.action(
            "human_review_boundary",
            "PASS",
            note=(
                "Automation evidence collected. HR-001/HR-002/HR-003 remain Human Review "
                "judgments and are not marked PASS by this scenario."
            ),
        )
