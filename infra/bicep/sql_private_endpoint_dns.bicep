targetScope = 'resourceGroup'

param location string = resourceGroup().location
param vnetName string = 'vnet-nba-ml'
param privateEndpointName string = 'pe-sql'
param sqlServerResourceId string  // full resourceId of Microsoft.Sql/servers/<name>

@description('Must match the recommended SQL Private Link DNS zone.')
param privateDnsZoneName string = 'privatelink.database.windows.net'

var subnetId = resourceId('Microsoft.Network/virtualNetworks/subnets', vnetName, 'snet-private-endpoints')

resource dnsZone 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: privateDnsZoneName
  location: 'global'
}

resource dnsLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: dnsZone
  name: 'link-${vnetName}'
  location: 'global'
  properties: {
    virtualNetwork: { id: resourceId('Microsoft.Network/virtualNetworks', vnetName) }
    registrationEnabled: false
  }
}

resource pe 'Microsoft.Network/privateEndpoints@2024-05-01' = {
  name: privateEndpointName
  location: location
  properties: {
    subnet: { id: subnetId }
    privateLinkServiceConnections: [
      {
        name: 'sql-connection'
        properties: {
          privateLinkServiceId: sqlServerResourceId
          groupIds: [ 'sqlServer' ]
        }
      }
    ]
  }
}

resource peDns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2025-03-01' = {
  parent: pe
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'sql-dns'
        properties: {
          privateDnsZoneId: dnsZone.id
        }
      }
    ]
  }
}

output privateEndpointId string = pe.id
