$ErrorActionPreference = 'Stop'
$runtime = Join-Path $PSScriptRoot '..\scripts\chef_runtime.ps1'
$testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('personal-skill-chef-test-' + [Guid]::NewGuid().ToString('N'))

try {
    [System.IO.Directory]::CreateDirectory($testRoot) | Out-Null
    & $runtime -Action Init -ProjectRoot $testRoot -Objective 'Verify supervised runtime' -Mode 'local-change' | Out-Null

    $proposalPath = Join-Path $testRoot '.codex\skill-chef\orders-next.json'
    $proposal = [ordered]@{
        orders = @(
            [ordered]@{
                id = 'upgrade'
                title = 'Upgrade and verify the Skill'
                rationale = 'A deterministic state transition test'
                stages = @(
                    [ordered]@{ id = 'inspect'; skill = 'personal-skill-chef'; deliverable = 'Inspection'; evidence = 'Observed state'; mutation = 'none'; group = 0 },
                    [ordered]@{ id = 'change'; skill = 'skill-creator'; deliverable = 'Validated change'; evidence = 'Passing validation'; mutation = 'local'; group = 1 }
                )
            }
        )
    }
    [System.IO.File]::WriteAllText($proposalPath, ($proposal | ConvertTo-Json -Depth 10), [System.Text.UTF8Encoding]::new($false))

    $validated = & $runtime -Action Validate -ProjectRoot $testRoot | ConvertFrom-Json
    if (-not $validated.valid) { throw 'Expected proposal to validate.' }
    $promoted = & $runtime -Action Promote -ProjectRoot $testRoot | ConvertFrom-Json
    if ($promoted.promoted -ne 1) { throw 'Expected one promoted order.' }

    $next = & $runtime -Action Next -ProjectRoot $testRoot | ConvertFrom-Json
    if ($next.stage_id -ne 'inspect') { throw 'Expected inspect to be the next stage.' }
    & $runtime -Action Start -ProjectRoot $testRoot | Out-Null
    & $runtime -Action Complete -ProjectRoot $testRoot -Result 'Inspection evidence recorded' | Out-Null

    $next = & $runtime -Action Next -ProjectRoot $testRoot | ConvertFrom-Json
    if ($next.stage_id -ne 'change') { throw 'Expected change to be the next stage.' }
    & $runtime -Action Start -ProjectRoot $testRoot | Out-Null
    & $runtime -Action Complete -ProjectRoot $testRoot -Result 'Validation passed' | Out-Null

    $status = & $runtime -Action Status -ProjectRoot $testRoot | ConvertFrom-Json
    if ($status.status -ne 'completed') { throw 'Expected completed runtime status.' }
    if ($status.stages.completed -ne 2) { throw 'Expected two completed stages.' }

    $readOnlyRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('personal-skill-chef-test-' + [Guid]::NewGuid().ToString('N'))
    [System.IO.Directory]::CreateDirectory($readOnlyRoot) | Out-Null
    & $runtime -Action Init -ProjectRoot $readOnlyRoot -Objective 'Verify mutation gate' -Mode 'read-only' | Out-Null
    $blockedPath = Join-Path $readOnlyRoot '.codex\skill-chef\orders-next.json'
    [System.IO.File]::WriteAllText($blockedPath, ($proposal | ConvertTo-Json -Depth 10), [System.Text.UTF8Encoding]::new($false))
    $blocked = $false
    try { & $runtime -Action Validate -ProjectRoot $readOnlyRoot | Out-Null } catch { $blocked = $_.Exception.Message -like '*exceeds read-only mode*' }
    if (-not $blocked) { throw 'Expected read-only mutation gate to reject the proposal.' }

    Write-Output 'chef_runtime tests passed'
} finally {
    foreach ($path in @($testRoot, $readOnlyRoot)) {
        if ($path -and $path.StartsWith([System.IO.Path]::GetTempPath(), [StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $path)) {
            Remove-Item -LiteralPath $path -Recurse -Force
        }
    }
}
