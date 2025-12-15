targetScope = 'resourceGroup'

@description('Azure region for resources.')
param location string = resourceGroup().location

@description('Existing VNet name (already deployed).')
param vnetName string = 'vnet-nba-ml'

@description('Compute subnet name (already deployed).')
param computeSubnetName string = 'snet-compute'

@description('Bastion subnet name must be exactly AzureBastionSubnet (already deployed).')
param bastionSubnetName string = 'AzureBastionSubnet'

@description('VM name.')
param vmName string = 'vm-nba-runner'

@description('VM size.')
param vmSize string = 'Standard_B2s'

@description('Admin username for the Linux VM.')
param adminUsername string = 'azureuser'

@description('SSH public key for admin user (paste contents of id_rsa.pub).')
param sshPublicKey string

@description('Name for Bastion host.')
param bastionName string = 'bas-nba'

@description('Name for Bastion public IP.')
param bastionPublicIpName string = 'pip-bas-nba'

var vnetId = resourceId('Microsoft.Network/virtualNetworks', vnetName)
var computeSubnetId = resourceId('Microsoft.Network/virtualNetworks/subnets', vnetName, computeSubnetName)
var bastionSubnetId = resourceId('Microsoft.Network/virtualNetworks/subnets', vnetName, bastionSubnetName)

resource nsg 'Microsoft.Network/networkSecurityGroups@2024-05-01' = {
  name: 'nsg-${vmName}'
  location: location
  properties: {
    securityRules: [
      {
        name: 'AllowSSHFromBastionSubnet'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '22'
          sourceAddressPrefix: '10.40.3.0/26' // your AzureBastionSubnet CIDR
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'DenyAllInbound'
        properties: {
          priority: 4096
          direction: 'Inbound'
          access: 'Deny'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
        }
      }
    ]
  }
}

resource nic 'Microsoft.Network/networkInterfaces@2024-05-01' = {
  name: 'nic-${vmName}'
  location: location
  properties: {
    networkSecurityGroup: {
      id: nsg.id
    }
    ipConfigurations: [
      {
        name: 'ipconfig1'
        properties: {
          privateIPAllocationMethod: 'Dynamic'
          subnet: {
            id: computeSubnetId
          }
          // No public IP here on purpose
        }
      }
    ]
  }
}

resource vm 'Microsoft.Compute/virtualMachines@2024-03-01' = {
  name: vmName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    hardwareProfile: {
      vmSize: vmSize
    }
    osProfile: {
      computerName: vmName
      adminUsername: adminUsername
      linuxConfiguration: {
        disablePasswordAuthentication: true
        ssh: {
          publicKeys: [
            {
              path: '/home/${adminUsername}/.ssh/authorized_keys'
              keyData: sshPublicKey
            }
          ]
        }
      }
    }
    storageProfile: {
      imageReference: {
        publisher: 'Canonical'
        offer: '0001-com-ubuntu-server-jammy'
        sku: '22_04-lts'
        version: 'latest'
      }
      osDisk: {
        createOption: 'FromImage'
        managedDisk: {
          storageAccountType: 'Premium_LRS'
        }
      }
    }
    networkProfile: {
      networkInterfaces: [
        {
          id: nic.id
        }
      ]
    }
  }
}

resource bastionPip 'Microsoft.Network/publicIPAddresses@2024-05-01' = {
  name: bastionPublicIpName
  location: location
  sku: {
    name: 'Standard'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
  }
}

resource bastion 'Microsoft.Network/bastionHosts@2024-05-01' = {
  name: bastionName
  location: location
  properties: {
    ipConfigurations: [
      {
        name: 'bastionIpConfig'
        properties: {
          subnet: {
            id: bastionSubnetId
          }
          publicIPAddress: {
            id: bastionPip.id
          }
        }
      }
    ]
  }
}

output vmPrivateIp string = nic.properties.ipConfigurations[0].properties.privateIPAddress
output bastionResourceName string = bastion.name
