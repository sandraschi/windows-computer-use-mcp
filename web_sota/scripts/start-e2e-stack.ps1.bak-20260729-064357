# E2E stack: uvicorn backend (background) + Vite preview on 10788.
$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot
$WebPort = if ($env:PYWINAUTO_WEB_PORT) { [int]$env:PYWINAUTO_WEB_PORT } else { 10788 }
$BackendPort = if ($env:PYWINAUTO_BACKEND_PORT) { [int]$env:PYWINAUTO_BACKEND_PORT } else { 10789 }

$backend = & (Join-Path $ScriptDir "start-backend.ps1") -Background -Port $BackendPort

try {
    Set-Location (Split-Path -Parent $ScriptDir)
    if (-not (Test-Path "dist\index.html")) {
        Write-Host "dist/ missing — running npm run build" -ForegroundColor Yellow
        npm run build
    }
    npx vite preview --host 127.0.0.1 --port $WebPort --strictPort
}
finally {
    if ($backend -and -not $backend.HasExited) {
        Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    }
}
