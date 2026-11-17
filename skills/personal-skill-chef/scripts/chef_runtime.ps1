[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Init', 'Status', 'Validate', 'Promote', 'Next', 'Start', 'Complete', 'Fail')]
    [string]$Action,

    [string]$ProjectRoot = (Get-Location).Path,
    [string]$Objective,
    [ValidateSet('read-only', 'local-change', 'external-mutation')]
    [string]$Mode = 'read-only',
    [string]$OrderId,
    [string]$StageId,
    [string]$Result,
    [string]$Reason
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$runtimeDir = Join-Path $ProjectRoot '.codex\skill-chef'
$misePath = Join-Path $runtimeDir 'mise.json'
$ordersNextPath = Join-Path $runtimeDir 'orders-next.json'
$ordersPath = Join-Path $runtimeDir 'orders.json'

function Get-Now {
    return [DateTime]::UtcNow.ToString('o')
}

function Read-JsonFile {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required runtime file is missing: $Path"
    }
    try {
        return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    } catch {
        throw "Invalid JSON in $Path`: $($_.Exception.Message)"
    }
}

function Write-JsonAtomic {
    param([string]$Path, [object]$Value)
    $parent = Split-Path -Parent $Path
    [System.IO.Directory]::CreateDirectory($parent) | Out-Null
    $temp = Join-Path $parent ('.tmp-' + [Guid]::NewGuid().ToString('N') + '.json')
    $json = $Value | ConvertTo-Json -Depth 20
    [System.IO.File]::WriteAllText($temp, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temp -Destination $Path -Force
}

function Set-Property {
    param([object]$Object, [string]$Name, [object]$Value)
    $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force
}

function Get-SkillNameSet {
    $inventory = Join-Path $PSScriptRoot 'inventory_skills.ps1'
    $raw = & $inventory -Json | Out-String
    if (-not $raw.Trim()) { throw 'The personal Skill inventory is empty.' }
    $items = @($raw | ConvertFrom-Json)
    $names = @{}
    foreach ($item in $items) { $names[$item.Name.ToLowerInvariant()] = $true }
    return $names
}

function Get-ValidationErrors {
    param([object]$Proposal, [string]$RuntimeMode)
    $errors = New-Object System.Collections.Generic.List[string]
    $skillNames = Get-SkillNameSet

    if ($null -eq $Proposal.PSObject.Properties['orders']) {
        $errors.Add('Top-level property "orders" is required.')
        return $errors
    }

    $orderIds = @{}
    foreach ($order in @($Proposal.orders)) {
        if (-not $order.id -or -not "$($order.id)".Trim()) {
            $errors.Add('Every order requires a non-empty id.')
            continue
        }
        $orderKey = "$($order.id)".ToLowerInvariant()
        if ($orderIds.ContainsKey($orderKey)) { $errors.Add("Duplicate order id: $($order.id)") }
        $orderIds[$orderKey] = $true
        if (-not $order.title -or -not "$($order.title)".Trim()) { $errors.Add("Order $($order.id) requires a title.") }

        $stages = @($order.stages)
        if ($stages.Count -eq 0) {
            $errors.Add("Order $($order.id) requires at least one stage.")
            continue
        }

        $stageIds = @{}
        $lastGroup = -1
        foreach ($stage in $stages) {
            $prefix = "Order $($order.id) stage $($stage.id)"
            if (-not $stage.id -or -not "$($stage.id)".Trim()) {
                $errors.Add("Order $($order.id) has a stage without an id.")
                continue
            }
            $stageKey = "$($stage.id)".ToLowerInvariant()
            if ($stageIds.ContainsKey($stageKey)) { $errors.Add("Duplicate stage id in order $($order.id): $($stage.id)") }
            $stageIds[$stageKey] = $true

            if (-not $stage.skill -or -not $skillNames.ContainsKey("$($stage.skill)".ToLowerInvariant())) {
                $errors.Add("$prefix references an unavailable Skill: $($stage.skill)")
            }
            if (-not $stage.deliverable -or -not "$($stage.deliverable)".Trim()) { $errors.Add("$prefix requires a deliverable.") }
            if (-not $stage.evidence -or -not "$($stage.evidence)".Trim()) { $errors.Add("$prefix requires evidence.") }

            $mutation = if ($stage.mutation) { "$($stage.mutation)" } else { 'none' }
            if ($mutation -notin @('none', 'local', 'external')) {
                $errors.Add("$prefix has invalid mutation '$mutation'.")
            } elseif ($RuntimeMode -eq 'read-only' -and $mutation -ne 'none') {
                $errors.Add("$prefix exceeds read-only mode with mutation '$mutation'.")
            } elseif ($RuntimeMode -eq 'local-change' -and $mutation -eq 'external') {
                $errors.Add("$prefix requires external-mutation mode.")
            }

            if ($null -ne $stage.PSObject.Properties['group']) {
                $group = 0
                if (-not [int]::TryParse("$($stage.group)", [ref]$group) -or $group -lt 0) {
                    $errors.Add("$prefix has an invalid group.")
                } elseif ($group -lt $lastGroup) {
                    $errors.Add("$prefix moves backward from group $lastGroup to $group.")
                } else {
                    $lastGroup = $group
                }
            }
        }
    }
    return $errors
}

function Get-NextStage {
    param([object]$OrdersFile)
    foreach ($order in @($OrdersFile.orders)) {
        if ($order.status -ne 'active') { continue }
        foreach ($stage in @($order.stages)) {
            if ($stage.status -eq 'active') {
                return [pscustomobject]@{ order = $order; stage = $stage }
            }
            if ($stage.status -eq 'pending') {
                return [pscustomobject]@{ order = $order; stage = $stage }
            }
        }
    }
    return $null
}

function Find-Stage {
    param([object]$OrdersFile, [string]$WantedOrder, [string]$WantedStage, [string[]]$Statuses)
    foreach ($order in @($OrdersFile.orders)) {
        if ($WantedOrder -and $order.id -ne $WantedOrder) { continue }
        foreach ($stage in @($order.stages)) {
            if ($WantedStage -and $stage.id -ne $WantedStage) { continue }
            if ($stage.status -in $Statuses) { return [pscustomobject]@{ order = $order; stage = $stage } }
        }
    }
    return $null
}

function Update-MiseStatus {
    param([string]$Status, [object]$HistoryItem)
    $mise = Read-JsonFile $misePath
    Set-Property $mise 'status' $Status
    Set-Property $mise 'updated_at' (Get-Now)
    if ($null -ne $HistoryItem) {
        $history = @($mise.recent_history)
        $history += $HistoryItem
        if ($history.Count -gt 20) { $history = $history[($history.Count - 20)..($history.Count - 1)] }
        Set-Property $mise 'recent_history' $history
    }
    Write-JsonAtomic $misePath $mise
}

if ($Action -eq 'Init') {
    if (-not $Objective.Trim()) { throw 'Init requires -Objective.' }
    if (Test-Path -LiteralPath $misePath) { throw "Runtime already initialized: $runtimeDir" }
    [System.IO.Directory]::CreateDirectory($runtimeDir) | Out-Null
    $now = Get-Now
    $mise = [ordered]@{
        format_version = 1
        objective = $Objective
        mode = $Mode
        status = 'ready'
        created_at = $now
        updated_at = $now
        resources = [ordered]@{ max_concurrency = 1; active = 0; available = 1 }
        recent_history = @()
        warnings = @('Supervised runtime: stages are never executed automatically.')
    }
    Write-JsonAtomic $misePath $mise
    Write-JsonAtomic $ordersPath ([ordered]@{ format_version = 1; orders = @() })
    [pscustomobject]@{ initialized = $true; runtime_dir = $runtimeDir; mode = $Mode; objective = $Objective } | ConvertTo-Json -Depth 5
    exit 0
}

if (-not (Test-Path -LiteralPath $misePath -PathType Leaf)) {
    throw "Runtime is not initialized: $runtimeDir"
}

$mise = Read-JsonFile $misePath

if ($Action -eq 'Validate') {
    $proposal = Read-JsonFile $ordersNextPath
    $errors = @(Get-ValidationErrors $proposal $mise.mode)
    if ($errors.Count -gt 0) { throw ('Order validation failed: ' + ($errors -join ' | ')) }
    [pscustomobject]@{ valid = $true; order_count = @($proposal.orders).Count; path = $ordersNextPath } | ConvertTo-Json -Depth 5
    exit 0
}

if ($Action -eq 'Promote') {
    $proposal = Read-JsonFile $ordersNextPath
    $errors = @(Get-ValidationErrors $proposal $mise.mode)
    if ($errors.Count -gt 0) { throw ('Order validation failed: ' + ($errors -join ' | ')) }
    $current = if (Test-Path -LiteralPath $ordersPath) { Read-JsonFile $ordersPath } else { [pscustomobject]@{ format_version = 1; orders = @() } }
    $merged = New-Object System.Collections.Generic.List[object]
    foreach ($item in @($current.orders)) { $merged.Add($item) }
    $existingById = @{}
    for ($i = 0; $i -lt $merged.Count; $i++) { $existingById["$($merged[$i].id)".ToLowerInvariant()] = $i }
    $promoted = 0
    foreach ($incoming in @($proposal.orders)) {
        $key = "$($incoming.id)".ToLowerInvariant()
        foreach ($stage in @($incoming.stages)) {
            Set-Property $stage 'status' 'pending'
            if ($null -eq $stage.PSObject.Properties['mutation']) { Set-Property $stage 'mutation' 'none' }
            if ($null -eq $stage.PSObject.Properties['group']) { Set-Property $stage 'group' 0 }
        }
        Set-Property $incoming 'status' 'active'
        Set-Property $incoming 'promoted_at' (Get-Now)
        if ($existingById.ContainsKey($key)) {
            $index = $existingById[$key]
            if ($merged[$index].status -eq 'failed') { $merged[$index] = $incoming; $promoted++ }
            continue
        }
        $existingById[$key] = $merged.Count
        $merged.Add($incoming)
        $promoted++
    }
    $mergedOrders = @($merged | ForEach-Object { $_ })
    Write-JsonAtomic $ordersPath ([ordered]@{ format_version = 1; orders = $mergedOrders })
    Remove-Item -LiteralPath $ordersNextPath
    Update-MiseStatus 'ready' ([pscustomobject]@{ at = Get-Now; type = 'orders.promoted'; summary = "$promoted order(s) promoted" })
    [pscustomobject]@{ promoted = $promoted; total_orders = $merged.Count; path = $ordersPath } | ConvertTo-Json -Depth 5
    exit 0
}

$orders = Read-JsonFile $ordersPath

if ($Action -eq 'Next') {
    $next = Get-NextStage $orders
    if ($null -eq $next) { [pscustomobject]@{ available = $false } | ConvertTo-Json; exit 0 }
    [pscustomobject]@{
        available = $true
        order_id = $next.order.id
        order_title = $next.order.title
        stage_id = $next.stage.id
        skill = $next.stage.skill
        deliverable = $next.stage.deliverable
        evidence = $next.stage.evidence
        mutation = $next.stage.mutation
        status = $next.stage.status
    } | ConvertTo-Json -Depth 5
    exit 0
}

if ($Action -eq 'Start') {
    $target = Find-Stage $orders $OrderId $StageId @('pending')
    if ($null -eq $target) { throw 'No matching pending stage was found.' }
    Set-Property $target.stage 'status' 'active'
    Set-Property $target.stage 'started_at' (Get-Now)
    Write-JsonAtomic $ordersPath $orders
    Update-MiseStatus 'running' ([pscustomobject]@{ at = Get-Now; type = 'stage.started'; order_id = $target.order.id; stage_id = $target.stage.id })
    [pscustomobject]@{ started = $true; order_id = $target.order.id; stage_id = $target.stage.id; skill = $target.stage.skill } | ConvertTo-Json -Depth 5
    exit 0
}

if ($Action -in @('Complete', 'Fail')) {
    $target = Find-Stage $orders $OrderId $StageId @('active')
    if ($null -eq $target) { throw 'No matching active stage was found. Start the stage before recording its outcome.' }
    $now = Get-Now
    if ($Action -eq 'Complete') {
        if (-not $Result.Trim()) { throw 'Complete requires -Result with an evidence summary.' }
        Set-Property $target.stage 'status' 'completed'
        Set-Property $target.stage 'completed_at' $now
        Set-Property $target.stage 'result' $Result
        $allComplete = @($target.order.stages | Where-Object { $_.status -ne 'completed' }).Count -eq 0
        if ($allComplete) { Set-Property $target.order 'status' 'completed'; Set-Property $target.order 'completed_at' $now }
        $eventType = 'stage.completed'
        $summary = $Result
    } else {
        if (-not $Reason.Trim()) { throw 'Fail requires -Reason.' }
        Set-Property $target.stage 'status' 'failed'
        Set-Property $target.stage 'failed_at' $now
        Set-Property $target.stage 'reason' $Reason
        Set-Property $target.order 'status' 'failed'
        $eventType = 'stage.failed'
        $summary = $Reason
    }
    Write-JsonAtomic $ordersPath $orders
    $hasRemaining = @($orders.orders | Where-Object { $_.status -eq 'active' }).Count -gt 0
    $runtimeStatus = if ($Action -eq 'Fail') { 'blocked' } elseif ($hasRemaining) { 'ready' } else { 'completed' }
    Update-MiseStatus $runtimeStatus ([pscustomobject]@{ at = $now; type = $eventType; order_id = $target.order.id; stage_id = $target.stage.id; summary = $summary })
    [pscustomobject]@{ recorded = $true; outcome = $Action.ToLowerInvariant(); order_id = $target.order.id; stage_id = $target.stage.id; runtime_status = $runtimeStatus } | ConvertTo-Json -Depth 5
    exit 0
}

if ($Action -eq 'Status') {
    $allStages = @($orders.orders | ForEach-Object { @($_.stages) })
    $counts = @{}
    foreach ($state in @('pending', 'active', 'completed', 'failed')) { $counts[$state] = @($allStages | Where-Object status -eq $state).Count }
    [pscustomobject]@{
        runtime_dir = $runtimeDir
        objective = $mise.objective
        mode = $mise.mode
        status = $mise.status
        orders = @($orders.orders).Count
        stages = $counts
        recent_history = @($mise.recent_history)
    } | ConvertTo-Json -Depth 10
}
