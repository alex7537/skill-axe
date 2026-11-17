[CmdletBinding()]
param(
    [string]$ActiveRoot = (Join-Path ([Environment]::GetFolderPath('UserProfile')) '.codex/skills'),
    [string]$BackupRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [string]$Query = '',
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

function Read-SkillFrontmatter {
    param(
        [System.IO.FileInfo]$File,
        [string]$Source
    )

    $lines = New-Object System.Collections.Generic.List[string]
    $reader = [System.IO.File]::OpenText($File.FullName)
    try {
        $first = $reader.ReadLine()
        if ($null -eq $first -or $first.Trim() -ne '---') { return $null }
        $lines.Add($first)
        while (($line = $reader.ReadLine()) -ne $null) {
            $lines.Add($line)
            if ($line.Trim() -eq '---') { break }
        }
    } finally {
        $reader.Dispose()
    }

    $closing = $lines.Count - 1
    if ($closing -lt 2 -or $lines[$closing].Trim() -ne '---') { return $null }

    $name = $null
    $description = $null
    for ($i = 1; $i -lt $closing; $i++) {
        if ($lines[$i] -match '^name:\s*["'']?(.*?)["'']?\s*$') {
            $name = $Matches[1].Trim()
            continue
        }
        if ($lines[$i] -match '^description:\s*(.*)$') {
            $value = $Matches[1].Trim().Trim('"').Trim("'")
            if ($value -match '^[>|][-+]?\s*$') {
                $parts = New-Object System.Collections.Generic.List[string]
                for ($j = $i + 1; $j -lt $closing; $j++) {
                    if ($lines[$j] -match '^[A-Za-z0-9_-]+:\s*') { break }
                    if ($lines[$j] -match '^\s+(.+)$') { $parts.Add($Matches[1].Trim()) }
                }
                $description = ($parts -join ' ').Trim()
            } else {
                $description = $value
            }
        }
    }

    if (-not $name) { return $null }
    [pscustomobject]@{
        Name = $name
        Description = $description
        Source = $Source
        Path = $File.FullName
    }
}

$items = New-Object System.Collections.Generic.List[object]
foreach ($root in @(
    [pscustomobject]@{ Path = $ActiveRoot; Source = 'active' },
    [pscustomobject]@{ Path = $BackupRoot; Source = 'backup' }
)) {
    if (-not (Test-Path -LiteralPath $root.Path -PathType Container)) { continue }
    Get-ChildItem -LiteralPath $root.Path -Filter 'SKILL.md' -File -Recurse | ForEach-Object {
        $item = Read-SkillFrontmatter -File $_ -Source $root.Source
        if ($null -ne $item) { $items.Add($item) }
    }
}

$activeNames = @{}
foreach ($item in $items) {
    if ($item.Source -eq 'active') { $activeNames[$item.Name.ToLowerInvariant()] = $true }
}

$results = $items | Where-Object {
    $_.Source -eq 'active' -or -not $activeNames.ContainsKey($_.Name.ToLowerInvariant())
}

if ($Query.Trim()) {
    $terms = $Query.ToLowerInvariant() -split '\s+' | Where-Object { $_ }
    $results = $results | ForEach-Object {
        $haystack = (($_.Name + ' ' + $_.Description).ToLowerInvariant())
        $score = 0
        foreach ($term in $terms) { if ($haystack.Contains($term)) { $score++ } }
        if ($score -gt 0) {
            $_ | Add-Member -NotePropertyName Score -NotePropertyValue $score -PassThru
        }
    } | Sort-Object @{ Expression = 'Score'; Descending = $true }, @{ Expression = 'Name'; Descending = $false }
} else {
    $results = $results | Sort-Object Name
}

if ($Json) {
    $results | ConvertTo-Json -Depth 3
} else {
    $results | Format-Table -AutoSize Name, Source, Description, Path
}
