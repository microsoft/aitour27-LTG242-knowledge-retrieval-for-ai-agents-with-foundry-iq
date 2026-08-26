targetScope = 'resourceGroup'

@description('Resource name for the HNS-enabled storage account for KB 2.')
param resourceName string

@description('Location for the storage account.')
param location string = resourceGroup().location

@description('Tags for the storage account.')
param tags object = {}

@description('Principal ID of the Search service managed identity.')
param searchServicePrincipalId string

@description('Principal type of the Search service identity.')
param searchServicePrincipalType string = 'ServicePrincipal'

@description('Principal ID of the provisioning user or application.')
param provisioningPrincipalId string

@description('Principal type of the provisioning identity.')
param provisioningPrincipalType string = 'User'

// Create HNS-enabled storage account for KB 2
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: resourceName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    accessTier: 'Hot'
    isHnsEnabled: true
  }
}

// Create the KB 2 filesystem container with HNS
resource kb2Container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: '${storageAccount.name}/default/kb2-sourcing'
  properties: {
    publicAccess: 'None'
  }
}

// Grant Search service managed identity Storage Blob Data Reader on the account
resource searchReaderRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, searchServicePrincipalId, 'Storage Blob Data Reader')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1')
    principalId: searchServicePrincipalId
    principalType: searchServicePrincipalType
  }
}

// Grant provisioning identity Storage Blob Data Owner for setup and ACL operations
resource provisioningOwnerRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, provisioningPrincipalId, 'Storage Blob Data Owner')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b')
    principalId: provisioningPrincipalId
    principalType: provisioningPrincipalType
  }
}

output storageAccountName string = storageAccount.name
output storageAccountId string = storageAccount.id
output containerName string = kb2Container.name
output containerResourceId string = '${storageAccount.id}/blobServices/default/containers/kb2-sourcing'
