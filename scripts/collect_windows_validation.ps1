[CmdletBinding()]
param(
    [string]$App = "phrase_collector",
    [string]$ExePath = "C:\ArrangeMaster\build\b\src\authoring\Debug\PhraseCollector.exe",
    [string]$ArtifactsRoot = "artifacts\windows_validation"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Convert-ExitCodeToStatus {
    param([int]$ExitCode)
    switch ($ExitCode) {
        0   { return "PASS" }
        3   { return "BLOCKED" }
        4   { return "FAIL" }
        5   { return "ERROR" }
        130 { return "ABORTED" }
        default { return "ERROR" }
    }
}

function Invoke-HarnessCommand {
    param(
        [string]$Name,
        [string[]]$Arguments,
        [string]$OutputFile
    )

    Write-Host "`n=== $Name ==="
    $output = & gui-harness @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    $output | Tee-Object -FilePath $OutputFile | ForEach-Object { Write-Host $_ }

    [pscustomobject]@{
        name        = $Name
        command     = "gui-harness " + ($Arguments -join " ")
        exit_code   = $exitCode
        status      = Convert-ExitCodeToStatus $exitCode
        output_file = $OutputFile
    }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git is not available on PATH."
}
if (-not (Get-Command gui-harness -ErrorAction SilentlyContinue)) {
    throw "gui-harness is not available on PATH. Activate the project virtual environment first."
}

$repoRoot = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or -not $repoRoot) {
    throw "This script must be run from inside the PyAutoGUI repository."
}
Set-Location $repoRoot

$dirty = @(& git status --porcelain)
if ($LASTEXITCODE -ne 0) {
    throw "Failed to read git worktree status."
}
if ($dirty.Count -gt 0) {
    throw "Working tree is dirty. Commit/stash all changes before review-grade validation so the tested tree SHA is authoritative."
}

$commitSha = (& git rev-parse HEAD).Trim()
$treeSha = (& git rev-parse 'HEAD^{tree}').Trim()
$branch = (& git branch --show-current).Trim()
if (-not $commitSha -or -not $treeSha) {
    throw "Failed to resolve tested commit/tree SHA."
}

$resolvedExe = (Resolve-Path -LiteralPath $ExePath).Path
$exeItem = Get-Item -LiteralPath $resolvedExe
$exeHash = Get-FileHash -LiteralPath $resolvedExe -Algorithm SHA256

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$shortTree = $treeSha.Substring(0, [Math]::Min(12, $treeSha.Length))
$bundle = Join-Path $repoRoot (Join-Path $ArtifactsRoot "${stamp}_${shortTree}")
New-Item -ItemType Directory -Path $bundle -Force | Out-Null

$metadata = [ordered]@{
    schema_version     = 1
    collected_at       = (Get-Date).ToString("o")
    tested_commit_sha  = $commitSha
    tested_tree_sha    = $treeSha
    branch             = $branch
    worktree_clean     = $true
    application        = $App
    executable         = [ordered]@{
        path            = $resolvedExe
        sha256          = $exeHash.Hash
        size_bytes      = $exeItem.Length
        last_write_time = $exeItem.LastWriteTime.ToString("o")
        file_version    = $exeItem.VersionInfo.FileVersion
        product_version = $exeItem.VersionInfo.ProductVersion
    }
}
$metadata | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $bundle "identity.json") -Encoding utf8

$doctor = Invoke-HarnessCommand -Name "doctor --app $App" -Arguments @("doctor", "--app", $App) -OutputFile (Join-Path $bundle "doctor.txt")
$listing = Invoke-HarnessCommand -Name "list" -Arguments @("list") -OutputFile (Join-Path $bundle "list.txt")

$capturePath = Join-Path $bundle "manual_capture.png"
$capture = Invoke-HarnessCommand -Name "capture --app $App" -Arguments @("capture", "--app", $App, "--output", $capturePath) -OutputFile (Join-Path $bundle "capture.txt")
if ($capture.exit_code -eq 0 -and -not (Test-Path -LiteralPath $capturePath)) {
    $capture.status = "ERROR"
}

$smokeRoot = Join-Path $bundle "smoke_artifacts"
$smoke = Invoke-HarnessCommand -Name "run phrase_collector.smoke" -Arguments @("run", "phrase_collector.smoke", "--artifacts", $smokeRoot) -OutputFile (Join-Path $bundle "run_smoke.txt")

$phase8Root = Join-Path $bundle "phase8_artifacts"
$phase8 = Invoke-HarnessCommand -Name "run phrase_collector.phase8_review" -Arguments @("run", "phrase_collector.phase8_review", "--artifacts", $phase8Root) -OutputFile (Join-Path $bundle "run_phase8_review.txt")

$postCommitSha = (& git rev-parse HEAD).Trim()
$postTreeSha = (& git rev-parse 'HEAD^{tree}').Trim()
$postDirty = @(& git status --porcelain)
$postExeHash = (Get-FileHash -LiteralPath $resolvedExe -Algorithm SHA256).Hash
$identityIntegrity = if (
    $postCommitSha -eq $commitSha -and
    $postTreeSha -eq $treeSha -and
    $postDirty.Count -eq 0 -and
    $postExeHash -eq $exeHash.Hash
) { "PASS" } else { "ERROR" }

$integrity = [ordered]@{
    status                 = $identityIntegrity
    initial_commit_sha     = $commitSha
    final_commit_sha       = $postCommitSha
    initial_tree_sha       = $treeSha
    final_tree_sha         = $postTreeSha
    final_worktree_clean   = ($postDirty.Count -eq 0)
    initial_exe_sha256     = $exeHash.Hash
    final_exe_sha256       = $postExeHash
}
$integrity | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $bundle "identity_integrity.json") -Encoding utf8

$gateB = $doctor.status
$gateC = if ($capture.exit_code -eq 0 -and (Test-Path -LiteralPath $capturePath)) { "PASS" } else { $capture.status }
$gateI = $smoke.status

$validation = [ordered]@{
    schema_version = 1
    identity_file  = "identity.json"
    identity_integrity = $identityIntegrity
    commands       = @($doctor, $listing, $capture, $smoke, $phase8)
    gates          = [ordered]@{
        B = [ordered]@{ status = $gateB; basis = "doctor --app $App" }
        C = [ordered]@{ status = $gateC; basis = "capture --app $App + capture file existence" }
        I = [ordered]@{ status = $gateI; basis = "run phrase_collector.smoke" }
    }
    human_review   = [ordered]@{
        "HR-001" = "PENDING"
        "HR-002" = "PENDING"
        "HR-003" = "PENDING"
    }
    phase8_automation = $phase8.status
    note = "Automation and evidence generation never set HR-001/HR-002/HR-003 to PASS."
}
$validation | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $bundle "validation.json") -Encoding utf8

$reviewTemplate = @"
# Human Review

This review is bound to the exact tested identity below. Do not reuse it for another tree or executable.

- Tested commit SHA: `$commitSha`
- Tested tree SHA: `$treeSha`
- PhraseCollector path: `$resolvedExe`
- PhraseCollector SHA-256: `$($exeHash.Hash)`
- Identity integrity: **$identityIntegrity**
- Gate B: **$gateB**
- Gate C: **$gateC**
- Gate I: **$gateI**

## HR-001 UX / 操作性

- Status: **PENDING**
- Reviewer:
- Observations:
- Decision rationale:

## HR-002 Musical Readability / 音楽的可読性

- Status: **PENDING**
- Reviewer:
- Observations:
- Decision rationale:

## HR-003 Visual Design

- Status: **PENDING**
- Reviewer:
- Observations:
- Decision rationale:

Allowed final Human Review statuses: `PASS`, `FAIL`, `BLOCKED`.
Automation PASS, screenshot generation, or Phase 8 evidence collection must not be substituted for Human Review PASS.
Use `scripts/finalize_windows_validation.ps1` to record the structured final judgments in this same evidence bundle.
"@
$reviewTemplate | Set-Content -LiteralPath (Join-Path $bundle "HUMAN_REVIEW.md") -Encoding utf8

$summary = @"
# Windows Validation Summary

## Tested identity

- Commit SHA: `$commitSha`
- Tree SHA: `$treeSha`
- Branch: `$branch`
- Worktree clean: `true`
- Executable: `$resolvedExe`
- Executable SHA-256: `$($exeHash.Hash)`
- Identity integrity after validation: **$identityIntegrity**

## Gates

| Gate | Status | Basis |
|---|---|---|
| B | $gateB | `gui-harness doctor --app $App` |
| C | $gateC | `gui-harness capture --app $App` and capture existence |
| I | $gateI | `gui-harness run phrase_collector.smoke` |

## Human Review

| Test | Status |
|---|---|
| HR-001 UX / 操作性 | PENDING |
| HR-002 Musical Readability | PENDING |
| HR-003 Visual Design | PENDING |

Phase 8 automation status: **$($phase8.status)**. This is evidence collection only and cannot set a Human Review test to PASS.

The PR must remain Draft/unmerged until identity integrity, Gate B/C/I, and HR-001/002/003 have all been explicitly reviewed and the finalization step reports eligibility.
"@
$summary | Set-Content -LiteralPath (Join-Path $bundle "SUMMARY.md") -Encoding utf8

Write-Host "`nValidation bundle: $bundle"
Write-Host "Identity integrity: $identityIntegrity"
Write-Host "Gate B: $gateB"
Write-Host "Gate C: $gateC"
Write-Host "Gate I: $gateI"
Write-Host "Human Review: PENDING (HR-001/HR-002/HR-003)"

if ($identityIntegrity -ne "PASS") { exit 5 }
if (@($gateB, $gateC, $gateI) -contains "ERROR") { exit 5 }
if (@($gateB, $gateC, $gateI) -contains "BLOCKED") { exit 3 }
if (@($gateB, $gateC, $gateI) -contains "FAIL") { exit 4 }
if (@($gateB, $gateC, $gateI) -contains "ABORTED") { exit 130 }
exit 0
