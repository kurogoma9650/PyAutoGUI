# Agent Rules

This repository implements a reusable Windows GUI automation harness.

## Architecture rules

- Application scenarios must never import `pyautogui` directly.
- Raw absolute screen coordinates must not be hard-coded in application scenarios.
- Resolve targets in this order: UI Automation, client/normalized-client coordinates, image matching.
- Every input action must pass foreground-window and target-window safety checks.
- `BLOCKED` and `FAIL` are distinct outcomes and must never be conflated.
- Automation success does not imply Human Review success.
- Screenshot capture should target the application client area unless a scenario explicitly requires otherwise.
- Machine-specific paths belong in `.gui-harness.local.toml`, environment variables, or CLI arguments; never commit them.
- `core`, `backends`, `selectors`, and `evidence` must remain application-agnostic.
- PhraseCollector-specific behavior belongs only under `scenarios/phrase_collector` and its profile.
- Do not add OpenAI API or other external AI API dependencies.
- Keep `pyautogui.FAILSAFE = True`.
- Do not silently continue when the interactive desktop, target window, or foreground safety check is unavailable.
