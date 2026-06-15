# Install Tesseract OCR 5.x silently (optional dependency for OCR features).
param(
    [switch]$Interactive,
    [string]$InstallDir = "$env:ProgramFiles\Tesseract-OCR",
    [string]$Version = "5.5.0.20251114"
)

$ErrorActionPreference = "Stop"

$InstallerUrl = "https://github.com/UB-Mannheim/tesseract/releases/download/v$Version/tesseract-ocr-w64-setup-$Version.exe"
$InstallerName = "tesseract-ocr-w64-setup-$Version.exe"
$TempDir = "$env:TEMP\tesseract-install"
$InstallerPath = "$TempDir\$InstallerName"

function Test-TesseractInstalled {
    $paths = @(
        "$InstallDir\tesseract.exe",
        "${env:ProgramFiles}\Tesseract-OCR\tesseract.exe",
        "${env:ProgramFiles(x86)}\Tesseract-OCR\tesseract.exe"
    )
    foreach ($p in $paths) {
        if (Test-Path $p) {
            try {
                $ver = & $p --version 2>&1 | Select-Object -First 1
                return $true, $p, $ver
            } catch { continue }
        }
    }
    try {
        $ver = tesseract --version 2>&1 | Select-Object -First 1
        return $true, "PATH", $ver
    } catch { }
    return $false, $null, $null
}

function Show-InstallDialog {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    $form = New-Object System.Windows.Forms.Form
    $form.Text = "Windows Computer Use — Optional Components"
    $form.Width = 460
    $form.Height = 260
    $form.StartPosition = "CenterScreen"
    $form.FormBorderStyle = "FixedDialog"
    $form.MaximizeBox = $false
    $form.MinimizeBox = $false

    $label = New-Object System.Windows.Forms.Label
    $label.Text = "Tesseract OCR enables text extraction from screenshots and images.`n`nRequired by: automation_visual(extract_text), assert_text, OCR scanning."
    $label.AutoSize = $false
    $label.Width = 420
    $label.Height = 60
    $label.Location = New-Object System.Drawing.Point(15, 15)
    $form.Controls.Add($label)

    $tessBox = New-Object System.Windows.Forms.CheckBox
    $tessBox.Text = "Install Tesseract OCR 5.x (${Version}) — 15 MB download"
    $tessBox.Checked = $true
    $tessBox.Location = New-Object System.Drawing.Point(20, 85)
    $form.Controls.Add($tessBox)

    $langLabel = New-Object System.Windows.Forms.Label
    $langLabel.Text = "Additional languages (comma-separated, e.g. deu, fra, spa):"
    $langLabel.AutoSize = $true
    $langLabel.Location = New-Object System.Drawing.Point(35, 115)
    $form.Controls.Add($langLabel)

    $langBox = New-Object System.Windows.Forms.TextBox
    $langBox.Text = "eng"
    $langBox.Width = 200
    $langBox.Location = New-Object System.Drawing.Point(35, 135)
    $form.Controls.Add($langBox)

    $ok = New-Object System.Windows.Forms.Button
    $ok.Text = "Install"
    $ok.DialogResult = [System.Windows.Forms.DialogResult]::OK
    $ok.Location = New-Object System.Drawing.Point(250, 175)
    $form.Controls.Add($ok)

    $skip = New-Object System.Windows.Forms.Button
    $skip.Text = "Skip"
    $skip.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
    $skip.Location = New-Object System.Drawing.Point(340, 175)
    $form.Controls.Add($skip)

    $form.AcceptButton = $ok
    $form.CancelButton = $skip
    $result = $form.ShowDialog()

    return [pscustomobject]@{
        Proceed = ($result -eq [System.Windows.Forms.DialogResult]::OK)
        InstallTesseract = $tessBox.Checked
        Languages = $langBox.Text
    }
}

# ── Main ──────────────────────────────────────────────────────────────

$installed, $installedPath, $installedVer = Test-TesseractInstalled
if ($installed) {
    Write-Host "Tesseract already installed: $installedVer ($installedPath)" -ForegroundColor Green
    if (-not $Interactive) { exit 0 }
    $choice = Show-InstallDialog
    if (-not $choice.Proceed -or -not $choice.InstallTesseract) {
        Write-Host "Skipped."
        exit 0
    }
    exit 0
}

if ($Interactive) {
    $choice = Show-InstallDialog
    if (-not $choice.Proceed -or -not $choice.InstallTesseract) {
        Write-Host "Skipped Tesseract installation."
        exit 0
    }
}

New-Item -ItemType Directory -Force -Path $TempDir | Out-Null

Write-Host "Downloading Tesseract OCR $Version..." -ForegroundColor Cyan
try {
    $wc = New-Object System.Net.WebClient
    $wc.DownloadFile($InstallerUrl, $InstallerPath)
} catch {
    Write-Host "Download failed: $_" -ForegroundColor Red
    Write-Host "Try downloading manually from: $InstallerUrl" -ForegroundColor Yellow
    exit 1
}

Write-Host "Installing Tesseract OCR silently..." -ForegroundColor Yellow
$proc = Start-Process -FilePath $InstallerPath -ArgumentList "/S" -Wait -PassThru
if ($proc.ExitCode -ne 0) {
    Write-Host "Installation failed (exit code $($proc.ExitCode))." -ForegroundColor Red
    Write-Host "Try installing manually: $InstallerPath" -ForegroundColor Yellow
    exit $proc.ExitCode
}

# Verify
$ok, $path, $ver = Test-TesseractInstalled
if ($ok) {
    Write-Host "Tesseract installed: $ver" -ForegroundColor Green

    # Add to PATH if installed to custom dir
    if ($path -ne "PATH" -and $path) {
        $dir = Split-Path -Parent $path
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if ($currentPath -notlike "*$dir*") {
            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$dir", "User")
            Write-Host "Added $dir to user PATH." -ForegroundColor Gray
        }
    }

    # Cleanup
    Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
    Write-Host "Done." -ForegroundColor Green
} else {
    Write-Host "Installation completed but tesseract.exe not found on PATH." -ForegroundColor Yellow
    Write-Host "You may need to add $InstallDir to your PATH manually." -ForegroundColor Yellow
}
