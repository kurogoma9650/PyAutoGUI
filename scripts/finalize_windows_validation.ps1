[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Bundle,

    [Parameter(Mandatory = $true)]
    [string]$Reviewer,

    [Parameter(Mandatory = $true)]
    [ValidateSet("PASS", "FAIL", "BLOCKED")]
    [string]$HR001,

    [Parameter(Mandatory = $true)]
    [ValidateSet("PASS", "FAIL", "BLOCKED")]
    [string]$HR002,

    [Parameter(Mandatory = $true)]
    [ValidateSet("PASS", "FAIL", "BLOCKED")]
    [string]$HR003,

    [string]$HR001Note = "",
    [string]$HR002Note = "",
    [string]$HR003Note = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$bundlePath = (Resolve-Path -LiteralPath $Bundle).Path
$identityPath = Join-Path $bundlePath "identity.json"
$validationPath = Join-Path $bundlePath "validation.json"
$integrityPath = Join-Path $bundlePath "identity_integrity.json"

foreach ($requiredPath in @($identityPath, $validationPath, $integrityPath)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Required validation evidence is missing: $requiredPath"
    }
}

$identity = Get-Content -LiteralPath $identityPath -Raw | ConvertFrom-Json
$validation = Get-Content -LiteralPath $validationPath -Raw | ConvertFrom-Json
$integrity = Get-Content -LiteralPath $integrityPath -Raw | ConvertFrom-Json

$identityIntegrity = [string]$integrity.status
$gateB = [string]$validation.gates.B.status
$gateC = [string]$validation.gates.C.status
$gateI = [string]$validation.gates.I.status
$allGatesPass = ($gateB -eq "PASS" -and $gateC -eq "PASS" -and $gateI -eq "PASS")
$allHumanPass = ($HR001 -eq "PASS" -and $HR002 -eq "PASS" -and $HR003 -eq "PASS")
$eligible = ($identityIntegrity -eq "PASS" -and $allGatesPass -and $allHumanPass)

$human = [ordered]@{
    schema_version    = 1
    recorded_at       = (Get-Date).ToString("o")
    reviewer          = $Reviewer
    tested_commit_sha = $identity.tested_commit_sha
    tested_tree_sha   = $identity.tested_tree_sha
    executable        = [ordered]@{
        path   = $identity.executable.path
        sha256 = $identity.executable.sha256
    }
    judgments = [ordered]@{
        "HR-001" = [ordered]@{
            name   = "UX / 操作性"
            status = $HR001
            note   = $HR001Note
        }
        "HR-002" = [ordered]@{
            name   = "Musical Readability / 音楽的可読性"
            status = $HR002
            note   = $HR002Note
        }
        "HR-003" = [ordered]@{
            name   = "Visual Design"
            status = $HR003
            note   = $HR003Note
        }
    }
}
$human | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $bundlePath "human_review.json") -Encoding utf8

$finalStatus = if ($eligible) {
    "ELIGIBLE_FOR_READY_REVIEW"
} elseif ($identityIntegrity -ne "PASS") {
    "IDENTITY_INTEGRITY_ERROR"
} elseif (-not $allGatesPass) {
    "GATES_NOT_PASS"
} else {
    "HUMAN_REVIEW_NOT_PASS"
}

$final = [ordered]@{
    schema_version        = 1
    finalized_at          = (Get-Date).ToString("o")
    tested_commit_sha     = $identity.tested_commit_sha
    tested_tree_sha       = $identity.tested_tree_sha
    executable_sha256     = $identity.executable.sha256
    identity_integrity    = $identityIntegrity
    gates                 = [ordered]@{ B = $gateB; C = $gateC; I = $gateI }
    human_review          = [ordered]@{ "HR-001" = $HR001; "HR-002" = $HR002; "HR-003" = $HR003 }
    ready_review_eligible = $eligible
    status                = $finalStatus
    note                  = "This file does not change PR state. Ready-for-review and merge remain explicit repository actions."
}
$final | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $bundlePath "final_review.json") -Encoding utf8

$markdown = @"
# Final Windows Validation Review

## Tested identity

- Commit SHA: `$($identity.tested_commit_sha)`
- Tree SHA: `$($identity.tested_tree_sha)`
- PhraseCollector: `$($identity.executable.path)`
- PhraseCollector SHA-256: `$($identity.executable.sha256)`
- Identity integrity: **$identityIntegrity**
- Reviewer: `$Reviewer`

## Gate results

| Gate | Status |
|---|---|
| B | $gateB |
| C | $gateC |
| I | $gateI |

## Human Review

| Test | Status | Note |
|---|---|---|
| HR-001 UX / 操作性 | $HR001 | $HR001Note |
| HR-002 Musical Readability / 音楽的可読性 | $HR002 | $HR002Note |
| HR-003 Visual Design | $HR003 | $HR003Note |

## Final status

**$finalStatus**

Ready-for-review eligible: **$eligible**

This result does not itself mark the PR Ready or merge it. Those actions are permitted only after this bundle is reviewed and only when the exact tested tree/executable identity is still the intended release candidate.
"@
$markdown | Set-Content -LiteralPath (Join-Path $bundlePath "FINAL_REVIEW.md") -Encoding utf8

Write-Host "Final status: $finalStatus"
Write-Host "Ready-for-review eligible: $eligible"
Write-Host "Bundle: $bundlePath"

if ($eligible) { exit 0 }
if ($identityIntegrity -ne "PASS") { exit 5 }
if (@($gateB, $gateC, $gateI) -contains "ERROR") { exit 5 }
if (@($gateB, $gateC, $gateI) -contains "ABORTED") { exit 130 }
if (@($gateB, $gateC, $gateI, $HR001, $HR002, $HR003) -contains "BLOCKED") { exit 3 }
exit 4
