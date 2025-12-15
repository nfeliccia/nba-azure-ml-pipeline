targetScope = 'resourceGroup'

@description('Azure region for resources.')
param location string = resourceGroup().location

@description('Logical SQL Server name (must be globally unique).')
param sqlServerName string

@description('Database name.')
param sqlDatabaseName string = 'nba'

@description('SQL admin login (required by SQL logical server creation).')
param sqlAdminLogin string

@secure()
@description('SQL admin password (do not store in git; pass at deploy time).')
param sqlAdminPassword string

@description('Entra ID (Azure AD) admin display name (user or group).')
param aadAdminLogin string

@description('Entra ID objectId (GUID) of the admin user/group.')
param aadAdminObjectId string

@description('Default: DISABLE public access. Set true temporarily for dev/testing.')
param enablePublicNetworkAccess bool = false

@description('If public access is enabled, optionally restrict to a single IPv4 address (your current IP).')
param allowedIp string = ''

@description('Optional: allow Azure services to access this SQL server (implements the portal checkbox).')
param allowAzureServices bool = false

@description('Database SKU name, e.g., GP_S_Gen5_1.')
param skuName string = 'GP_S_Gen5_1'

resource sqlServer 'Microsoft.Sql/servers@2024-11-01-preview' = {
  name: sqlServerName
  location: location
  properties: {
    version: '12.0'
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword

    minimalTlsVersion: '1.2'
    publicNetworkAccess: enablePublicNetworkAccess ? 'Enabled' : 'Disabled'
    restrictOutboundNetworkAccess: 'Enabled'
  }
}

resource sqlAadAdmin 'Microsoft.Sql/servers/administrators@2024-11-01-preview' = {
  parent: sqlServer
  name: 'ActiveDirectory'
  properties: {
    administratorType: 'ActiveDirectory'
    login: aadAdminLogin
    sid: aadAdminObjectId
    tenantId: tenant().tenantId
    // NOTE: some api versions accept principalType here; if it errors, delete this line

  }
}


resource sqlAadOnly 'Microsoft.Sql/servers/azureADOnlyAuthentications@2024-11-01-preview' = {
  parent: sqlServer
  name: 'Default'
  dependsOn: [
    sqlAadAdmin
  ]
  properties: {
    azureADOnlyAuthentication: true
  }
}


resource sqlDb 'Microsoft.Sql/servers/databases@2024-11-01-preview' = {
  parent: sqlServer
  name: sqlDatabaseName
  location: location
  sku: {
    name: skuName
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
  }
}

resource fwMyIp 'Microsoft.Sql/servers/firewallRules@2024-11-01-preview' = if (enablePublicNetworkAccess && allowedIp != '') {
  parent: sqlServer
  name: 'AllowMyIp'
  properties: {
    startIpAddress: allowedIp
    endIpAddress: allowedIp
  }
}

resource fwAzureServices 'Microsoft.Sql/servers/firewallRules@2024-11-01-preview' = if (enablePublicNetworkAccess && allowAzureServices) {
  parent: sqlServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

output sqlServerFqdn string = '${sqlServerName}.${environment().suffixes.sqlServerHostname}'
output databaseName string = sqlDatabaseName
