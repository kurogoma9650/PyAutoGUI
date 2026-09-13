from __future__ import annotations

from pathlib import Path


def test_collector_binds_review_identity() -> None:
    text = Path("scripts/collect_windows_validation.ps1").read_text(encoding="utf-8")
    required = [
        "tested_commit_sha",
        "tested_tree_sha",
        "Get-FileHash",
        "identity_integrity",
        "initial_exe_sha256",
        "final_exe_sha256",
        "final_worktree_clean",
        "doctor",
        "list",
        "capture",
        "phrase_collector.smoke",
        "phrase_collector.phase8_review",
        '"HR-001" = "PENDING"',
        '"HR-002" = "PENDING"',
        '"HR-003" = "PENDING"',
    ]
    for token in required:
        assert token in text


def test_finalizer_requires_integrity_and_never_changes_pr_state() -> None:
    text = Path("scripts/finalize_windows_validation.ps1").read_text(encoding="utf-8")
    assert "identity_integrity.json" in text
    assert "IDENTITY_INTEGRITY_ERROR" in text
    assert "ELIGIBLE_FOR_READY_REVIEW" in text
    assert "mark ready" not in text.lower()
    assert "gh pr ready" not in text.lower()
    assert "gh pr merge" not in text.lower()
