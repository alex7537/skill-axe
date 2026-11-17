[CmdletBinding()]
param(
    [string]$ProjectPath = (Get-Location).Path,
    [string]$CookieFile,
    [string]$Url
)

$ErrorActionPreference = 'Stop'

function Write-Section {
    param([string]$Name)
    Write-Output "`n## $Name"
}

function Get-CommandSummary {
    param([string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $command) {
        return [pscustomobject]@{ Name = $Name; Found = $false; Path = $null; Version = $null }
    }

    $version = $null
    try {
        $version = $command.Version.ToString()
    } catch {
        $version = $null
    }
    [pscustomobject]@{
        Name = $Name
        Found = $true
        Path = $command.Source
        Version = $version
    }
}

function Get-CookieMetadata {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return [pscustomobject]@{ Exists = $false; Path = $Path }
    }

    $item = Get-Item -LiteralPath $Path
    $valid = 0
    $expired = 0
    $secure = 0
    $domains = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $hasNetscapeHeader = $false

    foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
        if ($line -match '^# Netscape HTTP Cookie File') {
            $hasNetscapeHeader = $true
            continue
        }
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) {
            continue
        }
        $fields = $line -split "`t"
        if ($fields.Count -lt 7) {
            continue
        }
        $valid++
        [void]$domains.Add($fields[0])
        if ($fields[3] -eq 'TRUE') { $secure++ }
        $expiry = 0L
        if ([Int64]::TryParse($fields[4], [ref]$expiry) -and $expiry -gt 0 -and $expiry -lt $now) {
            $expired++
        }
    }

    [pscustomobject]@{
        Exists = $true
        Path = $item.FullName
        Bytes = $item.Length
        LastWriteTime = $item.LastWriteTime
        NetscapeHeader = $hasNetscapeHeader
        ValidRecordCount = $valid
        DomainCount = $domains.Count
        Domains = @($domains | Sort-Object)
        SecureRecordCount = $secure
        ExpiredRecordCount = $expired
    }
}

Write-Output '# Parabolic / yt-dlp read-only diagnostic'
Write-Output ("Timestamp: {0}" -f (Get-Date -Format o))
Write-Output 'This script does not change application, network, cookie, or project state.'

Write-Section 'System'
[pscustomobject]@{
    OS = [System.Environment]::OSVersion.VersionString
    PowerShell = $PSVersionTable.PSVersion.ToString()
    ProcessArchitecture = [System.Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture.ToString()
} | Format-List | Out-String | Write-Output

Write-Section 'Resolved commands'
@('python', 'yt-dlp', 'ffmpeg', 'deno') |
    ForEach-Object { Get-CommandSummary $_ } |
    Format-Table -AutoSize |
    Out-String |
    Write-Output

Write-Section 'Parabolic installation candidates'
$programFiles = [Environment]::GetFolderPath('ProgramFiles')
$parabolicRoot = Join-Path $programFiles 'Nickvision Parabolic\Release'
if (Test-Path -LiteralPath $parabolicRoot -PathType Container) {
    $diagnosticExecutables = @(
        'Nickvision.Parabolic.WinUI.exe',
        'yt-dlp.exe',
        'ffmpeg.exe',
        'ffprobe.exe',
        'ffplay.exe',
        'deno.exe',
        'aria2c.exe'
    )
    Get-ChildItem -LiteralPath $parabolicRoot -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -in $diagnosticExecutables } |
        Select-Object Name, Length, LastWriteTime |
        Format-Table -AutoSize |
        Out-String |
        Write-Output
} else {
    Write-Output "Not found: $parabolicRoot"
}

Write-Section 'Project environment'
if (Test-Path -LiteralPath $ProjectPath -PathType Container) {
    $project = Get-Item -LiteralPath $ProjectPath
    $venvPython = Join-Path $project.FullName '.venv\Scripts\python.exe'
    [pscustomobject]@{
        Path = $project.FullName
        VenvPythonExists = Test-Path -LiteralPath $venvPython -PathType Leaf
        RequirementsExists = Test-Path -LiteralPath (Join-Path $project.FullName 'requirements.txt') -PathType Leaf
    } | Format-List | Out-String | Write-Output

    if (Test-Path -LiteralPath $venvPython -PathType Leaf) {
        try {
            $ytDlpVersion = & $venvPython -c "import importlib.metadata as m; print(m.version('yt-dlp'))" 2>$null
            Write-Output "Project yt-dlp package: $ytDlpVersion"
        } catch {
            Write-Output 'Project yt-dlp package: unavailable'
        }
    }
} else {
    Write-Output "Project not found: $ProjectPath"
}

Write-Section 'Proxy indicators'
@('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY') | ForEach-Object {
    $value = [Environment]::GetEnvironmentVariable($_)
    [pscustomobject]@{ Variable = $_; Configured = -not [string]::IsNullOrWhiteSpace($value) }
} | Format-Table -AutoSize | Out-String | Write-Output

if ($CookieFile) {
    Write-Section 'Cookie metadata (values and names suppressed)'
    Get-CookieMetadata -Path $CookieFile | Format-List | Out-String | Write-Output
}

if ($Url) {
    Write-Section 'URL host reachability'
    try {
        $uri = [Uri]$Url
        if (-not $uri.IsAbsoluteUri -or [string]::IsNullOrWhiteSpace($uri.DnsSafeHost)) {
            throw 'URL must be absolute and include a host.'
        }
        Write-Output "Scheme: $($uri.Scheme)"
        Write-Output "Host: $($uri.DnsSafeHost)"
        try {
            $addresses = [System.Net.Dns]::GetHostAddresses($uri.DnsSafeHost) |
                ForEach-Object { $_.IPAddressToString }
            Write-Output ("DNS addresses: {0}" -f ($addresses -join ', '))
        } catch {
            Write-Output "DNS failed: $($_.Exception.Message)"
        }
        $port = if ($uri.Port -gt 0) { $uri.Port } elseif ($uri.Scheme -eq 'http') { 80 } else { 443 }
        $tcp = Test-NetConnection -ComputerName $uri.DnsSafeHost -Port $port -InformationLevel Detailed -WarningAction SilentlyContinue
        [pscustomobject]@{
            RemotePort = $port
            TcpTestSucceeded = $tcp.TcpTestSucceeded
            RemoteAddress = $tcp.RemoteAddress
            InterfaceAlias = $tcp.InterfaceAlias
        } | Format-List | Out-String | Write-Output
    } catch {
        Write-Output "URL check failed: $($_.Exception.Message)"
    }
}
