Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SUBSCRIPTION_ID = "659bc9fe-df16-4de2-902f-cf9883772bc7"
$spName = "sp-nba-home-uploader"

az login
az account set --subscription $SUBSCRIPTION_ID

# Create SP (no RBAC yet)
$sp = az ad sp create-for-rbac --name $spName --skip-assignment | ConvertFrom-Json

$APP_ID        = $sp.appId
$TENANT_ID     = $sp.tenant
$CLIENT_SECRET = $sp.password

$SP_OBJECT_ID = az ad sp show --id $APP_ID --query id -o tsv

@"
AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID
AZURE_TENANT_ID=$TENANT_ID
AZURE_CLIENT_ID=$APP_ID
AZURE_CLIENT_SECRET=$CLIENT_SECRET
AZURE_SP_OBJECT_ID=$SP_OBJECT_ID
"@ | Set-Content -Encoding utf8 .\.env

Write-Host "Wrote .env (DO NOT COMMIT). ClientId=$APP_ID TenantId=$TENANT_ID SP_ObjectId=$SP_OBJECT_ID"
