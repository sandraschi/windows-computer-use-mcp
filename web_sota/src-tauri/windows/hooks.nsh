; Kill UI + backend before install/uninstall (backend locks resources/*.exe).
!macro KillWindowsComputerUseFleetProcesses
  DetailPrint "Stopping windows-computer-use-mcp processes..."
  ExecWait 'taskkill /F /IM windows-computer-use-backend.exe /T' $0
  ExecWait 'taskkill /F /IM windows-computer-use-mcp-native.exe /T' $0
  !if "${INSTALLMODE}" == "currentUser"
    nsis_tauri_utils::KillProcessCurrentUser "windows-computer-use-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcessCurrentUser "windows-computer-use-mcp-native.exe"
    Pop $0
  !else
    nsis_tauri_utils::KillProcess "windows-computer-use-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcess "windows-computer-use-mcp-native.exe"
    Pop $0
  !endif
  Sleep 2000
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro KillWindowsComputerUseFleetProcesses
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro KillWindowsComputerUseFleetProcesses
!macroend

!macro NSIS_HOOK_POSTINSTALL
  ; Option 1: Register MCP in Cursor / Claude Desktop
  IfFileExists "$INSTDIR\resources\install-mcp-clients.ps1" 0 tesseract_hook
    DetailPrint "Optional: register windows-computer-use-mcp in Cursor / Claude Desktop"
    ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\resources\install-mcp-clients.ps1" -Interactive'
  tesseract_hook:
  ; Option 2: Install Tesseract OCR (required for OCR features)
  IfFileExists "$INSTDIR\resources\install-tesseract.ps1" 0 hook_done
    DetailPrint "Optional: install Tesseract OCR for text extraction"
    ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\resources\install-tesseract.ps1" -Interactive'
  hook_done:
!macroend
