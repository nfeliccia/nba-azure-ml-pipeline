# Login (interactive)
az login
az account set --subscription "<YOUR_SUBSCRIPTION_ID>"

# Create the service principal with NO role assignment yet
$spName = "sp-nba-home-uploader"
$sp = az ad sp create-for-rbac --name $spName --skip-assignment | ConvertFrom-Json

$APP_ID   = $sp.appId
$TENANT_ID = $sp.tenant
$CLIENT_SECRET = $sp.password

# Get the service principal objectId (needed for RBAC in Bicep)
$SP_OBJECT_ID = az ad sp show --id $APP_ID --query id -o tsv

"$APP_ID `n$TENANT_ID `n$SP_OBJECT_ID" | Out-Host
# IMPORTANT: store $CLIENT_SECRET somewhere safe right now (password manager).
