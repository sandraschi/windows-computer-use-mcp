; Kill UI + backend before install/uninstall (backend locks resources/*.exe).
; Multi-layer: Stop-Process (same-user) + taskkill (any user) + NSIS plugin.
; For SYSTEM/other-user zombie processes, the Rust free_port() function has a
; UAC elevation fallback that fires on the next app launch.
!macro KillPywinautoMcpFleetProcesses
  DetailPrint "Stopping pywinauto-mcp processes..."

  ; Stop-Process (same-user) + taskkill /F /IM (any user)
  ExecWait 'powershell -NoProfile -Command "Stop-Process -Name pywinauto-mcp-backend -Force -ErrorAction SilentlyContinue; Stop-Process -Name pywinauto-mcp-native -Force -ErrorAction SilentlyContinue; taskkill /F /IM pywinauto-mcp-backend.exe /T; taskkill /F /IM pywinauto-mcp-native.exe /T"' $0

  ; NSIS plugin fallback
  !if "${INSTALLMODE}" == "currentUser"
    nsis_tauri_utils::KillProcessCurrentUser "pywinauto-mcp-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcessCurrentUser "pywinauto-mcp-native.exe"
    Pop $0
  !else
    nsis_tauri_utils::KillProcess "pywinauto-mcp-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcess "pywinauto-mcp-native.exe"
    Pop $0
  !endif

  Sleep 3000
!macroend

!macro UninstallPrevious
  DetailPrint "Checking for previous installation..."
  !if "${INSTALLMODE}" == "currentUser"
    ReadRegStr $R0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${IDENTIFIER}" "UninstallString"
  !else
    ReadRegStr $R0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${IDENTIFIER}" "UninstallString"
  !endif

  ${If} $R0 != ""
    DetailPrint "Found previous installation at $R0"
    ExecWait '"$R0" /S' $0
    DetailPrint "Previous uninstall exit code: $0"
    Sleep 1500
  ${EndIf}
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro KillPywinautoMcpFleetProcesses
  !insertmacro UninstallPrevious
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro KillPywinautoMcpFleetProcesses
!macroend
