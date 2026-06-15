#!/usr/bin/env pwsh
param(
    [switch]$NoSign,
    [string]$OutputDir = "dist"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $RepoRoot

Write-Host "=== windows-computer-use-mcp MCPB Package Builder ===" -ForegroundColor Cyan

$McpbExe = $null
if (Get-Command mcpb -ErrorAction SilentlyContinue) {
    $McpbExe = (Get-Command mcpb).Source
} else {
    $candidates = @(
        (Join-Path $env:APPDATA "npm\mcpb.cmd"),
        (Join-Path $env:ProgramFiles "nodejs\mcpb.cmd")
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            $McpbExe = $candidate
            break
        }
    }
}
if (-not $McpbExe) {
    Write-Host "ERROR: mcpb not found. Install: npm install -g @anthropic-ai/mcpb" -ForegroundColor Red
    exit 1
}
Write-Host "Using: $McpbExe" -ForegroundColor Green

$srcPackage = Join-Path $RepoRoot "src\windows_computer_use_mcp"
$dstPackage = Join-Path $RepoRoot "mcpb\src\windows_computer_use_mcp"
if (-not (Test-Path $srcPackage)) {
    Write-Host "ERROR: Source not found: $srcPackage" -ForegroundColor Red
    exit 1
}
if (Test-Path $dstPackage) {
    Remove-Item $dstPackage -Recurse -Force
}
Copy-Item -Path $srcPackage -Destination $dstPackage -Recurse -Force
Get-ChildItem -Path $dstPackage -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }
Write-Host "Synced src/windows_computer_use_mcp -> mcpb/src/windows_computer_use_mcp" -ForegroundColor Green

$mcpbManifest = Join-Path $RepoRoot "mcpb\manifest.json"
& $McpbExe validate $mcpbManifest
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Manifest validation failed" -ForegroundColor Red
    exit 1
}
Write-Host "Manifest validation passed" -ForegroundColor Green

$distDir = Join-Path $RepoRoot $OutputDir
if (-not (Test-Path $distDir)) {
    New-Item -ItemType Directory -Path $distDir -Force | Out-Null
}

$packagePath = Join-Path $distDir "windows-computer-use-mcp.mcpb"
if (Test-Path $packagePath) {
    Remove-Item $packagePath -Force
}

Push-Location (Join-Path $RepoRoot "mcpb")
try {
    $relOut = Join-Path ".." $OutputDir
    & $McpbExe pack "." (Join-Path $relOut "windows-computer-use-mcp.mcpb")
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: MCPB pack failed" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}

if (Test-Path $packagePath) {
    $sizeMb = [math]::Round((Get-Item $packagePath).Length / 1MB, 2)
    Write-Host "Built: $packagePath ($sizeMb MB)" -ForegroundColor Green
} else {
    Write-Host "ERROR: Package not found after build" -ForegroundColor Red
    exit 1
}
