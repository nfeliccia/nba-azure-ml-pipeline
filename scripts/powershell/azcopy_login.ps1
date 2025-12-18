# scripts/powershell/azcopy_login_from_env.ps1
# Reads .\nba-azure-ml-pipeline.env and logs into AzCopy using a Service Principal.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Import-DotEnvFile
{
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path))
    {
        throw "Missing env file: $Path"
    }

    Get-Content $Path |
            Where-Object { $_ -and $_ -notmatch '^\s*#' } |
            ForEach-Object {
                $name, $value = $_ -split '=', 2
                if (-not $name)
                {
                    return
                }

                $name = $name.Trim()
                $value = ($value ?? "").Trim().Trim('"').Trim("'")

                # Set for this PowerShell process
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$envPath = Join-Path $repoRoot ".env"

Import-DotEnvFile -Path $envPath
# Validate required vars
$required = @("AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET")

$missing = foreach ($name in $required)
{
    $item = Get-Item -Path ("env:{0}" -f $name) -ErrorAction SilentlyContinue
    if (-not $item -or [string]::IsNullOrWhiteSpace($item.Value))
    {
        $name
    }
}

if (@($missing).Count -gt 0)
{
    throw ("Missing required env var(s) in {0}: {1}" -f $envPath, ($missing -join ", "))
}

# AzCopy expects the secret in this env var name
$env:AZCOPY_SPA_CLIENT_SECRET = $env:AZURE_CLIENT_SECRET

# Optional: show non-sensitive context
Write-Host "AzCopy SP login with TenantId=$( $env:AZURE_TENANT_ID ) ClientId=$( $env:AZURE_CLIENT_ID )"

# Login
azcopy login --service-principal --application-id $env:AZURE_CLIENT_ID --tenant-id $env:AZURE_TENANT_ID
