targetScope = 'resourceGroup'

param tags object = {}
param resourceName string
param azureSearchSkuName string = 'standard'
param storageAccountResourceId string
param containerName string = 'knowledge'
param aiServicesAccountName string = ''
param aiProjectName string = ''
param principalId string
param principalType string
param connectionName string = 'azure-ai-search-connection'
param location string = resourceGroup().location

resource aiAccount 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = if (!empty(aiServicesAccountName) && !empty(aiProjectName)) {
  name: aiServicesAccountName

  resource aiProject 'projects' existing = {
    name: aiProjectName
  }
}

resource searchService 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: resourceName
  location: location
  tags: tags
  sku: {
    name: azureSearchSkuName
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    disableLocalAuth: false
    publicNetworkAccess: 'enabled'
  }
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: last(split(storageAccountResourceId, '/'))
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' existing = {
  parent: storageAccount
  name: 'default'
}

resource storageContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: containerName
  properties: {
    publicAccess: 'None'
  }
}

resource searchToStorageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, searchService.id, 'Storage Blob Data Contributor', uniqueString(deployment().name))
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: searchService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource searchToAIServicesRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(aiServicesAccountName)) {
  name: guid(aiServicesAccountName, searchService.id, 'Cognitive Services OpenAI User', uniqueString(deployment().name))
  scope: aiAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: searchService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource searchToAIServicesUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(aiServicesAccountName)) {
  name: guid(aiServicesAccountName, searchService.id, 'Cognitive Services User', uniqueString(deployment().name))
  scope: aiAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908')
    principalId: searchService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource aiServicesToSearchServiceRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(aiServicesAccountName) && !empty(aiProjectName)) {
  name: guid(searchService.id, aiServicesAccountName, aiProjectName, 'Search Service Contributor', uniqueString(deployment().name))
  scope: searchService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7ca78c08-252a-4471-8644-bb5ff32d4ba0')
    principalId: aiAccount::aiProject!.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource aiServicesToSearchDataRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(aiServicesAccountName) && !empty(aiProjectName)) {
  name: guid(searchService.id, aiServicesAccountName, aiProjectName, 'Search Index Data Contributor', uniqueString(deployment().name))
  scope: searchService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')
    principalId: aiAccount::aiProject!.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource userToSearchRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, principalId, 'Search Index Data Contributor', uniqueString(deployment().name))
  scope: searchService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')
    principalId: principalId
    principalType: principalType
  }
}

resource userToSearchServiceContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, principalId, 'Search Service Contributor', uniqueString(deployment().name))
  scope: searchService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7ca78c08-252a-4471-8644-bb5ff32d4ba0')
    principalId: principalId
    principalType: principalType
  }
}

module aiSearchConnection '../ai/connection.bicep' = if (!empty(aiServicesAccountName) && !empty(aiProjectName)) {
  name: 'ai-search-connection-creation'
  params: {
    aiServicesAccountName: aiServicesAccountName
    aiProjectName: aiProjectName
    connectionConfig: {
      name: connectionName
      category: 'CognitiveSearch'
      target: 'https://${searchService.name}.search.windows.net'
      authType: 'AAD'
      isSharedToAll: true
      metadata: {
        ApiVersion: '2024-07-01'
        ResourceId: searchService.id
        ApiType: 'Azure'
        type: 'azure_ai_search'
      }
    }
  }
  dependsOn: [
    aiServicesToSearchDataRoleAssignment
  ]
}

output searchServiceName string = searchService.name
output searchServiceId string = searchService.id
output searchServicePrincipalId string = searchService.identity.principalId
output storageAccountName string = storageAccount.name
output storageAccountId string = storageAccount.id
output containerName string = storageContainer.name
output searchConnectionName string = (!empty(aiServicesAccountName) && !empty(aiProjectName)) ? aiSearchConnection!.outputs.connectionName : ''
output searchConnectionId string = (!empty(aiServicesAccountName) && !empty(aiProjectName)) ? aiSearchConnection!.outputs.connectionId : ''
