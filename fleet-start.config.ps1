# Per-repo fleet start config for pywinauto-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'pywinauto-mcp'
    BackendPort  = 10789
    FrontendPort = 10788
    HealthPath   = '/api/v1/health'
    WebRoot      = 'D:\Dev\repos\pywinauto-mcp\web_sota'
    NssmService  = 'mcp-pywinauto-mcp'
    Backend = @{
        # 'nssm', not 'uvicorn' -- this backend runs as a persistent NSSM
        # Windows service, but under a DIFFERENT name than this repo's
        # config Name ('mcp-pywinauto-mcp', not 'pywinauto-mcp') -- hence
        # the explicit NssmService override above; Start-FleetNssmWebapp
        # falls back to Name only when NssmService isn't set, which would
        # look for a service that doesn't exist under that name. With
        # Kind='uvicorn' the generic port-conflict path only health-checks
        # an already-running backend when -ReuseIfRunning is passed;
        # without it, a healthy NSSM-held port gets reported as blocked and
        # the launcher exits 1 -- an instacrash on plain double-click even
        # though the service is fine. Same bug found and fixed in
        # discord-mcp's fleet-start.config.ps1, 2026-09-08.
        Kind          = 'nssm'
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
