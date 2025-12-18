param location string = resourceGroup().location

@minLength(3)
@maxLength(24)
param storageAccountName string

// Service Principal objectId (principalId) from your .env: AZURE_SP_OBJECT_ID
param spObjectId string

var containerName = 'nba-raw'

// Storage Blob Data Contributor role definition id (built-in)
var storageBlobDataContributorRole = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
)

resource stg 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
  }
}

resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${stg.name}/default/${containerName}'
  properties: {}
}

resource ra 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(container.id, spObjectId, storageBlobDataContributorRole)
  scope: container
  properties: {
    roleDefinitionId: storageBlobDataContributorRole
    principalId: spObjectId
    principalType: 'ServicePrincipal'
  }
}

output storageAccount string = stg.name
output container string = containerName
