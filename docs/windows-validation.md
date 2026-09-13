# Windows Validation Contract

Windows interactive validation is review-grade only when the evidence is bound to one exact repository tree and one exact PhraseCollector executable.

## Required identity

Every validation bundle must include:

- tested commit SHA
- tested tree SHA (`git rev-parse HEAD^{tree}`)
- clean worktree assertion
- `PhraseCollector.exe` absolute path
- `PhraseCollector.exe` SHA-256
- executable size and version metadata when available

A dirty worktree is rejected by the collector because the tested tree SHA would not fully identify the code being exercised.

The collector re-checks the repository commit/tree, worktree cleanliness, and executable SHA-256 after all validation commands finish. `identity_integrity.json` must be `PASS`; any mid-run change invalidates review eligibility even if individual GUI gates passed.

## Required command evidence

The following command outputs are captured into the same bundle:

- `gui-harness doctor --app phrase_collector`
- `gui-harness list`
- `gui-harness capture --app phrase_collector`
- `gui-harness run phrase_collector.smoke`
- `gui-harness run phrase_collector.phase8_review`

The collector also stores the generated screenshot/scenario artifacts.

## Gate mapping

- **Gate B**: Win32 / DPI / preflight. Basis: `doctor --app phrase_collector`.
- **Gate C**: MSS client capture. Basis: `capture --app phrase_collector` plus actual output-file existence.
- **Gate I**: PhraseCollector smoke scenario. Basis: `run phrase_collector.smoke`.

`BLOCKED`, `FAIL`, `ERROR`, and `ABORTED` remain distinct from `PASS`.

## Human Review boundary

Automation is not allowed to set any of these to PASS:

- HR-001 UX / 操作性
- HR-002 Musical Readability / 音楽的可読性
- HR-003 Visual Design

The collection script always initializes them as `PENDING`. A reviewer must enter explicit `PASS`, `FAIL`, or `BLOCKED` judgments using the finalization script.

## Workflow

```powershell
.\scripts\collect_windows_validation.ps1 `
  -ExePath "C:\ArrangeMaster\build\b\src\authoring\Debug\PhraseCollector.exe"
```

The script prints the created validation bundle path. Inspect its screenshots, command logs, `SUMMARY.md`, `identity_integrity.json`, and `HUMAN_REVIEW.md`, then record the Human Review judgments:

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

Finalization writes `human_review.json`, `final_review.json`, and `FINAL_REVIEW.md` into the same bundle.

`ELIGIBLE_FOR_READY_REVIEW` is emitted only when identity integrity, Gate B/C/I, and HR-001/002/003 are all PASS. It does not automatically alter the GitHub pull request. The PR must remain Draft and unmerged until the exact tested identity and evidence bundle have been reviewed.
