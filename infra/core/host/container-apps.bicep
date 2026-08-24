metadata description = 'Creates an Azure Container Registry and Azure Container Apps environment.'

param location string = resourceGroup().location
param tags object = {}
param containerAppsEnvironmentName string
param containerRegistryName string
param logAnalyticsWorkspaceName string = ''

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: containerRegistryName
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
  }
}

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' existing = if (!empty(logAnalyticsWorkspaceName)) {
  name: logAnalyticsWorkspaceName
}

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerAppsEnvironmentName
  location: location
  tags: tags
  properties: !empty(logAnalyticsWorkspaceName) ? {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace!.properties.customerId
        sharedKey: logAnalyticsWorkspace!.listKeys().primarySharedKey
      }
    }
  } : {
    appLogsConfiguration: {
      destination: 'none'
    }
  }
}

output environmentName string = environment.name
output registryLoginServer string = registry.properties.loginServer
output registryName string = registry.name
