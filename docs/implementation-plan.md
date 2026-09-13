# Implementation Gates

| Gate | Scope | Completion condition |
|---|---|---|
| A | Repository bootstrap | package installs, CLI imports, CI configured |
| B | Win32/DPI/preflight | target window and Windows session are resolved |
| C | Capture | target client area can be captured |
| D | Input | fixture click/type/drag works |
| E | Selectors | UIA/client/relative resolution works |
| F | Safety | foreground and bounds violations abort input |
| G | Evidence | manifest, actions, screenshots, result are written |
| H | Runner | fixture scenario completes |
| I | PhraseCollector | smoke scenario completes on local machine |
| J | Phase 8 evidence | review scenario collects review evidence |
| K | Architecture review | generic layers contain no PhraseCollector dependency |

CI covers static/unit checks. GUI integration remains an explicit local Windows run because a hosted runner is not equivalent to the interactive review desktop.
