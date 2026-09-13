# Architecture

The harness separates generic GUI infrastructure from application-specific scenarios.

```text
CLI / Scenario Runner
        |
        v
    RunContext
  /    |     |    \
Win32 UIA  Input  Capture
 |     |      |      |
 +-----+------+------+
            |
      Windows desktop
```

## Input policy

UI Automation is primarily used to locate a control. Physical input is delivered by PyAutoGUI so tests exercise the visible GUI path. For custom-rendered surfaces such as WebView2, scenarios may use client-relative coordinates or optional image matching.

Selector priority:

1. UIA selector
2. Client or normalized-client coordinate
3. Image selector

Application scenarios call only `RunContext`; they do not call PyAutoGUI directly.

## Coordinate spaces

- `SCREEN`: physical desktop coordinates.
- `CLIENT`: pixels relative to the target client area.
- `NORMALIZED_CLIENT`: values in `[0, 1]` relative to the target client area.

Scenarios should prefer `CLIENT` and `NORMALIZED_CLIENT`.

## Outcomes

- `PASS`: scenario completed and assertions passed.
- `FAIL`: the application behavior did not meet an assertion.
- `BLOCKED`: the environment cannot support the requested run.
- `ERROR`: harness implementation/runtime failure.
- `ABORTED`: operator/fail-safe interruption.

Automation results and Human Review results are separate.
