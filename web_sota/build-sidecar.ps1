#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Build the PyInstaller sidecar for the windows-computer-use-mcp Tauri operator shell.
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Triple = "x86_64-pc-windows-msvc"

Write-Host "=== windows-computer-use-mcp sidecar build ===" -ForegroundColor Cyan

Push-Location $Root
try {
    $pi = uv run pyinstaller --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "-> Installing PyInstaller..." -ForegroundColor Yellow
        uv pip install pyinstaller "charset-normalizer>=3.4.5"
    }
    else {
        Write-Host "-> PyInstaller: $pi" -ForegroundColor Gray
    }

    Remove-Item -Recurse -Force "$Root\build\windows-computer-use-backend" -ErrorAction SilentlyContinue
    Remove-Item -Force "$Root\dist\windows-computer-use-backend.exe" -ErrorAction SilentlyContinue

    Write-Host "-> Running PyInstaller..." -ForegroundColor Yellow
    uv run pyinstaller windows-computer-use-backend.spec --clean --noconfirm
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed (exit $LASTEXITCODE)" }

    $src = "$Root\dist\windows-computer-use-backend.exe"
    $resourceDir = "$Root\web_sota\src-tauri\resources"
    $devDir = "$Root\web_sota\src-tauri\binaries"
    $bundled = "$resourceDir\windows-computer-use-backend.exe"
    $devCopy = "$devDir\windows-computer-use-backend-$Triple.exe"

    if (-not (Test-Path $src)) { throw "Build output not found: $src" }

    New-Item -ItemType Directory -Path $resourceDir -Force | Out-Null
    New-Item -ItemType Directory -Path $devDir -Force | Out-Null
    Copy-Item $src $bundled -Force
    Copy-Item $src $devCopy -Force

    $sizeMB = [math]::Round((Get-Item $bundled).Length / 1MB, 1)
    Write-Host "=== Backend embedded ===" -ForegroundColor Green
    Write-Host "  bundle resource: $bundled ($sizeMB MB)" -ForegroundColor Cyan
    Write-Host "  dev fallback:    $devCopy" -ForegroundColor Gray
}
finally {
    Pop-Location
}
