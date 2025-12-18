Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Import-DotEnv {
    param([string]$Path = ".env")
    if (-not (Test-Path $Path)) { throw "Missing $Path" }

    Get-Content $Path |
        Where-Object { $_ -and $_ -notmatch '^\s*#' } |
        ForEach-Object {
            $name, $value = $_ -split '=', 2
            $name  = $name.Trim()
            $value = $value.Trim().Trim('"').Trim("'")
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
}

Import-DotEnv ".\.env"

az login
az account set --subscription $env:AZURE_SUBSCRIPTION_ID

$rg  = "rg-nba-landing"
$loc = "eastus"

# Must be globally unique, lowercase, 3-24 chars
$stg = ("stnba" + (Get-Random -Minimum 10000000 -Maximum 99999999))

az group create -n $rg -l $loc | Out-Null

az deployment group create `
  -g $rg `
  -f .\infra\bicep\landingzone.bicep `
  -p location=$loc storageAccountName=$stg spObjectId=$env:AZURE_SP_OBJECT_ID
