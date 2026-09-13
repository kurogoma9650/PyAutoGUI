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

## Review-grade Windows validation rules

- Final Windows validation must run from a clean worktree so the tested tree SHA uniquely identifies the code under test.
- Bind one evidence bundle to the tested commit SHA, tested tree SHA, `PhraseCollector.exe` absolute path, and executable SHA-256.
- Preserve raw `doctor`, `list`, `capture`, smoke-run, and Phase 8 evidence-run outputs in that same bundle.
- Record Gate B, Gate C, and Gate I separately; never infer a missing gate from another successful command.
- HR-001 UX / 操作性, HR-002 Musical Readability / 音楽的可読性, and HR-003 Visual Design require explicit Human Review judgments.
- Automation, screenshots, and evidence generation must never set HR-001/002/003 to PASS.
- The PR must remain Draft and unmerged until Gate B/C/I and HR-001/002/003 are all explicitly reviewed against the same tested identity.
- `ELIGIBLE_FOR_READY_REVIEW` is only an eligibility result; scripts must not automatically mark a PR Ready or merge it.
