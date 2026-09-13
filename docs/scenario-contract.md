# Scenario Contract

A scenario subclasses `Scenario` and implements `run(ctx)`.

Optional lifecycle methods are `setup(ctx)` and `cleanup(ctx)`. Cleanup always runs after setup succeeds, including when the run fails or is blocked.

Scenarios must:

- use `RunContext` for input and capture;
- avoid absolute screen-coordinate literals;
- record meaningful checkpoints rather than every frame;
- avoid destructive operations on user production data;
- leave final Human Review judgments to a human/reviewer.

PhraseCollector scenarios live under `gui_harness.scenarios.phrase_collector`.
