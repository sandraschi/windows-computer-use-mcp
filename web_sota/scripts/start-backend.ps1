# Start uvicorn backend for e2e / preview (foreground or background via -Background).
param(
    [int]$Port = 10789,
    [switch]$Background
)

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$srcPath = Join-Path $RepoRoot "src"
$cmd = "`$env:PYTHONPATH = '$srcPath'; Set-Location '$RepoRoot'; uv run uvicorn windows_computer_use_mcp.server:app --host 127.0.0.1 --port $Port --log-level warning"

if ($Background) {
    $proc = Start-Process pwsh -ArgumentList "-NoProfile", "-Command", $cmd -PassThru -WindowStyle Hidden
    Write-Host "Backend PID $($proc.Id) on port $Port"
    & (Join-Path $PSScriptRoot "wait-health.ps1") -Url "http://127.0.0.1:$Port/api/v1/health"
    return $proc
}

Invoke-Expression $cmd
