from __future__ import annotations

from .base import Scenario
from .phrase_collector.phase8_review import PhraseCollectorPhase8ReviewScenario
from .phrase_collector.smoke import PhraseCollectorSmokeScenario

_SCENARIOS: dict[str, type[Scenario]] = {
    PhraseCollectorSmokeScenario.name: PhraseCollectorSmokeScenario,
    PhraseCollectorPhase8ReviewScenario.name: PhraseCollectorPhase8ReviewScenario,
}


def list_scenarios() -> list[str]:
    return sorted(_SCENARIOS)


def create_scenario(name: str) -> Scenario:
    try:
        return _SCENARIOS[name]()
    except KeyError as exc:
        raise KeyError(f"Unknown scenario: {name}") from exc
