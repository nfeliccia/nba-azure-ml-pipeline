targetScope = 'resourceGroup'

param location string = resourceGroup().location
param vnetName string = 'vnet-nba-ml'
param vnetCidr string = '10.40.0.0/16'

param subnetPrivateEndpointsCidr string = '10.40.1.0/24'
param subnetComputeCidr string = '10.40.2.0/24'
param subnetBastionCidr string = '10.40.3.0/26' // must be named AzureBastionSubnet

resource vnet 'Microsoft.Network/virtualNetworks@2024-05-01' = {
  name: vnetName
  location: location
  properties: {
    addressSpace: { addressPrefixes: [vnetCidr] }
    subnets: [
      {
        name: 'snet-private-endpoints'
        properties: {
          addressPrefix: subnetPrivateEndpointsCidr
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
      {
        name: 'snet-compute'
        properties: {
          addressPrefix: subnetComputeCidr
        }
      }
      {
        name: 'AzureBastionSubnet'
        properties: {
          addressPrefix: subnetBastionCidr
        }
      }
    ]
  }
}

output vnetId string = vnet.id
