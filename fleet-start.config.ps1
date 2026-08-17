# Per-repo fleet start config for pywinauto-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'pywinauto-mcp'
    BackendPort  = 10789
    FrontendPort = 10788
    HealthPath   = '/api/v1/health'
    WebRoot      = 'D:\Dev\repos\pywinauto-mcp\web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'windows_computer_use_mcp.server:app'
        Env           = @{ WEB_PORT = '10789' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
