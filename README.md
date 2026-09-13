# GUI Automation Harness

Reusable Windows GUI automation for local desktop applications.

The harness combines:

- **Win32 / pywinauto** for window discovery and UI Automation.
- **PyAutoGUI** for physical mouse and keyboard input.
- **MSS + Pillow** for screenshots and visual-stability waits.
- **Evidence recording** for screenshots, JSONL action logs, manifests, and result summaries.
- **Scenario adapters** for application-specific workflows such as PhraseCollector.

It does not require the OpenAI API. It is intended to be driven locally by a human or by Codex through shell commands.

## Requirements

- Windows 10 or Windows 11
- Python 3.11+
- An interactive, visible desktop session

## Install

```powershell
git clone git@github.com:kurogoma9650/PyAutoGUI.git
cd PyAutoGUI
git switch feature/gui-harness-v1
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
```

Optional image matching:

```powershell
pip install -e ".[dev,vision]"
```

## Local configuration

Create `.gui-harness.local.toml` in the repository root:

```toml
[applications.phrase_collector]
executable = "C:\\ArrangeMaster\\build\\b\\src\\authoring\\Debug\\PhraseCollector.exe"
working_directory = "C:\\ArrangeMaster\\build\\b\\src\\authoring\\Debug"
```

The file is intentionally ignored by Git.

## CLI

```powershell
gui-harness doctor
gui-harness doctor --app phrase_collector
gui-harness list
gui-harness capture --app phrase_collector
gui-harness launch --app phrase_collector
gui-harness run phrase_collector.smoke
gui-harness run phrase_collector.phase8_review
```

Machine-readable output is available with `--json` where applicable.

## Review-grade Windows validation

For Gate B/C/I and Human Review, use the validation scripts instead of collecting unrelated command outputs manually. The collector refuses a dirty worktree and binds the evidence to the exact tested tree SHA and `PhraseCollector.exe` SHA-256. It re-checks the commit/tree, clean worktree, and executable hash after the run; any identity drift invalidates review eligibility.

```powershell
.\scripts\collect_windows_validation.ps1 `
  -ExePath "C:\ArrangeMaster\build\b\src\authoring\Debug\PhraseCollector.exe"
```

It records `doctor`, `list`, `capture`, smoke-run, Phase 8 evidence-run, Gate B/C/I status, tested commit/tree SHA, executable identity, and post-run identity integrity in one bundle under `artifacts\windows_validation`.

After visually and interactively reviewing the exact captured build, record the Human Review decisions:

```powershell
.\scripts\finalize_windows_validation.ps1 `
  -Bundle "artifacts\windows_validation\<bundle>" `
  -Reviewer "<reviewer>" `
  -HR001 PASS `
  -HR002 PASS `
  -HR003 PASS `
  -HR001Note "<observations>" `
  -HR002Note "<observations>" `
  -HR003Note "<observations>"
```

Only identity integrity, Gate B/C/I, and HR-001/002/003 all PASS yields `ELIGIBLE_FOR_READY_REVIEW`. The scripts never change the GitHub PR state or merge it. See `docs/windows-validation.md` for the evidence contract.

## Safety

The harness refuses input when the expected target is not the foreground application. PyAutoGUI's fail-safe remains enabled: moving the mouse to the upper-left corner aborts PyAutoGUI operations.

`PASS` means an automation scenario completed its assertions. It never means that UX, musical readability, or visual design has passed Human Review.
