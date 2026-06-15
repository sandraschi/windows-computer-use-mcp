# Register windows-computer-use-mcp in Cursor and/or Claude Desktop (HTTP streamable MCP).
param(
    [switch]$Cursor,
    [switch]$Claude,
    [switch]$Interactive
)

$ErrorActionPreference = "Stop"

$ServerKey = "windows-computer-use-mcp"
$McpUrl = "http://127.0.0.1:10789/mcp"

function Get-CursorConfigPath {
    Join-Path $env:USERPROFILE ".cursor\mcp.json"
}

function Get-ClaudeConfigPath {
    Join-Path $env:APPDATA "Claude\claude_desktop_config.json"
}

function Backup-ConfigFile {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }
    $dir = Split-Path -Parent $Path
    $file = Split-Path -Leaf $Path
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    if ($file -match '^(.+)\.json$') {
        $backupName = "$($Matches[1])_$stamp.json.bak"
    } else {
        $backupName = "${file}_$stamp.bak"
    }
    $backup = Join-Path $dir $backupName
    Copy-Item -LiteralPath $Path -Destination $backup -Force
    Write-Host "Backup: $backup"
    return $backup
}

function Register-McpClient {
    param([string]$Path)

    $root = [ordered]@{}
    if (Test-Path $Path) {
        $raw = Get-Content -Path $Path -Raw -Encoding UTF8
        if (-not [string]::IsNullOrWhiteSpace($raw)) {
            $parsed = $raw | ConvertFrom-Json
            foreach ($prop in $parsed.PSObject.Properties) {
                if ($prop.Name -ne "mcpServers") {
                    $root[$prop.Name] = $prop.Value
                }
            }
        }
    }

    $servers = [ordered]@{}
    if (Test-Path $Path) {
        $raw = Get-Content -Path $Path -Raw -Encoding UTF8
        if (-not [string]::IsNullOrWhiteSpace($raw)) {
            $parsed = $raw | ConvertFrom-Json
            if ($parsed.mcpServers) {
                foreach ($prop in $parsed.mcpServers.PSObject.Properties) {
                    $servers[$prop.Name] = @{ url = $prop.Value.url }
                }
            }
        }
    }

    $servers[$ServerKey] = @{ url = $McpUrl }
    $root["mcpServers"] = $servers

    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Backup-ConfigFile -Path $Path | Out-Null
    $json = ($root | ConvertTo-Json -Depth 8)
    Set-Content -Path $Path -Value $json -Encoding UTF8
}

function Show-InstallDialog {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    $form = New-Object System.Windows.Forms.Form
    $form.Text = "Pywinauto MCP — AI client setup"
    $form.Width = 460
    $form.Height = 260
    $form.StartPosition = "CenterScreen"
    $form.FormBorderStyle = "FixedDialog"
    $form.MaximizeBox = $false
    $form.MinimizeBox = $false

    $label = New-Object System.Windows.Forms.Label
    $label.Text = "Register the MCP server so Cursor or Claude Desktop can call pywinauto tools.`n`nKeep the operator app running while you use MCP."
    $label.AutoSize = $false
    $label.Width = 420
    $label.Height = 70
    $label.Location = New-Object System.Drawing.Point(15, 15)
    $form.Controls.Add($label)

    $cursorBox = New-Object System.Windows.Forms.CheckBox
    $cursorBox.Text = "Cursor (mcp.json)"
    $cursorBox.Checked = $true
    $cursorBox.Location = New-Object System.Drawing.Point(20, 95)
    $form.Controls.Add($cursorBox)

    $claudeBox = New-Object System.Windows.Forms.CheckBox
    $claudeBox.Text = "Claude Desktop (claude_desktop_config.json)"
    $claudeBox.Checked = $false
    $claudeBox.Location = New-Object System.Drawing.Point(20, 125)
    $form.Controls.Add($claudeBox)

    $ok = New-Object System.Windows.Forms.Button
    $ok.Text = "Register"
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
        Cursor = $cursorBox.Checked
        Claude = $claudeBox.Checked
    }
}

if ($Interactive -and -not $Cursor -and -not $Claude) {
    $choice = Show-InstallDialog
    if (-not $choice.Proceed) {
        Write-Host "Skipped MCP client registration."
        exit 0
    }
    if ($choice.Cursor) { $Cursor = $true }
    if ($choice.Claude) { $Claude = $true }
}

if (-not $Cursor -and -not $Claude) {
    Write-Host "Nothing to register. Pass -Cursor, -Claude, or -Interactive."
    exit 0
}

$updated = @()
if ($Cursor) {
    $path = Get-CursorConfigPath
    Register-McpClient -Path $path
    $updated += "Cursor ($path)"
}
if ($Claude) {
    $path = Get-ClaudeConfigPath
    Register-McpClient -Path $path
    $updated += "Claude Desktop ($path)"
}

Write-Host "Registered $ServerKey -> $McpUrl"
foreach ($item in $updated) {
    Write-Host "  - $item"
}
