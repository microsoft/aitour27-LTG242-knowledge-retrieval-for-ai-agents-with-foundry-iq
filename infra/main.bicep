targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the azd environment.')
param environmentName string

@minLength(1)
@maxLength(90)
@description('Name of the resource group to create.')
param resourceGroupName string = 'rg-${environmentName}'

@minLength(1)
@description('Primary Azure region. It must support Foundry hosted agents and the selected models.')
param location string

@description('Object ID of the user or application running azd.')
param principalId string

@description('Principal type of the identity running azd.')
param principalType string

@description('Model deployments serialized by the azure.ai.agents azd extension.')
param aiProjectDeploymentsJson string = '[]'

@description('Enable Application Insights and Log Analytics.')
param enableMonitoring bool = true

@description('Azure AI Search SKU.')
@allowed([
  'basic'
  'standard'
  'standard2'
  'standard3'
  'storage_optimized_l1'
  'storage_optimized_l2'
])
param searchServiceSku string = 'standard'

@description('Enable PostgreSQL infrastructure for MCP-backed relational tools.')
param enablePostgres bool = true

@secure()
@description('Shared API key used by Azure AI Search to call the PostgreSQL MCP server.')
param mcpApiKey string

@description('Previously deployed PostgreSQL MCP image supplied by azd.')
param servicePostgresMcpImageName string = ''

var configuredDeployments = json(aiProjectDeploymentsJson)
var fallbackDeployments = [
  {
    name: 'gpt-5.4'
    model: {
      format: 'OpenAI'
      name: 'gpt-5.4'
      version: '2026-03-05'
    }
    sku: {
      name: 'GlobalStandard'
      capacity: 200
    }
  }
  {
    name: 'text-embedding-3-large'
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-large'
      version: '1'
    }
    sku: {
      name: 'GlobalStandard'
      capacity: 30
    }
  }
]
var deployments = empty(configuredDeployments) ? fallbackDeployments : configuredDeployments
var embeddingDeployments = filter(deployments, deployment => contains(toLower(deployment.model.name), 'embedding'))
var chatDeployments = filter(deployments, deployment => !contains(toLower(deployment.model.name), 'embedding'))
var tags = {
  'azd-env-name': environmentName
}

// Keeps globally scoped resource names deterministic and within length limits.
var resourceToken = toLower(uniqueString(subscription().subscriptionId, environmentName))

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

var postgresServerName = 'pg-${resourceToken}'
var postgresDatabaseName = 'ontology'
var postgresEntraAdministratorName = 'admin${uniqueString(rg.id, principalId)}'

module postgresServer 'core/database/postgresql/flexibleserver.bicep' = if (enablePostgres) {
  scope: rg
  name: 'postgresql'
  params: {
    name: postgresServerName
    location: location
    tags: tags
    sku: {
      name: 'Standard_B1ms'
      tier: 'Burstable'
    }
    storage: {
      storageSizeGB: 32
    }
    version: '16'
    authType: 'EntraOnly'
    entraAdministratorName: postgresEntraAdministratorName
    entraAdministratorObjectId: principalId
    entraAdministratorType: principalType
    databaseNames: [
      postgresDatabaseName
    ]
    allowAzureIPsFirewall: true
    allowAllIPsFirewall: true
    allowedExtensions: 'vector,pg_trgm'
  }
}

module aiProject 'core/ai/ai-project.bicep' = {
  scope: rg
  name: 'ai-project'
  params: {
    tags: tags
    location: location
    aiFoundryProjectName: 'ai-project-${environmentName}'
    principalId: principalId
    principalType: principalType
    deployments: deployments
    enableMonitoring: enableMonitoring
    searchServiceSku: searchServiceSku
  }
}

module containerApps 'core/host/container-apps.bicep' = if (enablePostgres) {
  scope: rg
  params: {
    location: location
    tags: tags
    containerAppsEnvironmentName: 'cae-${resourceToken}'
    containerRegistryName: 'cr${resourceToken}'
    logAnalyticsWorkspaceName: aiProject.outputs.LOG_ANALYTICS_WORKSPACE_NAME
  }
}

module postgresMcp 'postgres-mcp.bicep' = if (enablePostgres) {
  scope: rg
  params: {
    name: 'postgres-mcp-${resourceToken}'
    location: location
    tags: tags
    containerAppsEnvironmentName: containerApps!.outputs.environmentName
    containerRegistryName: containerApps!.outputs.registryName
    postgresHost: postgresServer!.outputs.POSTGRES_DOMAIN_NAME
    postgresDatabase: postgresDatabaseName
    mcpApiKey: mcpApiKey
    imageName: servicePostgresMcpImageName
    tenantId: tenant().tenantId
    applicationInsightsConnectionString: aiProject.outputs.APPLICATIONINSIGHTS_CONNECTION_STRING
  }
}

output AZURE_RESOURCE_GROUP string = resourceGroupName
output AZURE_AI_ACCOUNT_ID string = aiProject.outputs.accountId
output AZURE_AI_PROJECT_ID string = aiProject.outputs.projectId
output AZURE_AI_FOUNDRY_PROJECT_ID string = aiProject.outputs.projectId
output AZURE_AI_ACCOUNT_NAME string = aiProject.outputs.aiServicesAccountName
output AZURE_AI_PROJECT_NAME string = aiProject.outputs.projectName
output AZURE_AI_PROJECT_ENDPOINT string = aiProject.outputs.AZURE_AI_PROJECT_ENDPOINT
output FOUNDRY_PROJECT_ENDPOINT string = aiProject.outputs.AZURE_AI_PROJECT_ENDPOINT
output MICROSOFT_FOUNDRY_PROJECT_ENDPOINT string = aiProject.outputs.AZURE_AI_PROJECT_ENDPOINT
output MICROSOFT_FOUNDRY_PROJECT_ID string = aiProject.outputs.projectId

output AZURE_AI_MODEL_DEPLOYMENT_NAME string = string(chatDeployments[0].name)
output AZURE_OPENAI_CHATGPT_DEPLOYMENT string = string(chatDeployments[0].name)
output AZURE_OPENAI_CHATGPT_MODEL_NAME string = string(chatDeployments[0].model.name)
output AZURE_OPENAI_EMBEDDING_DEPLOYMENT string = string(embeddingDeployments[0].name)
output AZURE_OPENAI_EMBEDDING_MODEL_NAME string = string(embeddingDeployments[0].model.name)
output AZURE_OPENAI_ENDPOINT string = aiProject.outputs.AZURE_OPENAI_ENDPOINT
output AZURE_OPENAI_SERVICE_NAME string = aiProject.outputs.aiServicesAccountName

output AZURE_AI_SEARCH_SERVICE_NAME string = aiProject.outputs.search.serviceName
output AZURE_AI_SEARCH_SERVICE_ENDPOINT string = aiProject.outputs.search.serviceEndpoint
output AZURE_SEARCH_SERVICE_NAME string = aiProject.outputs.search.serviceName
output AZURE_SEARCH_SERVICE_ENDPOINT string = aiProject.outputs.search.serviceEndpoint

output AZURE_STORAGE_CONNECTION_NAME string = aiProject.outputs.storage.connectionName
output AZURE_STORAGE_ACCOUNT_NAME string = aiProject.outputs.storage.accountName
output APPLICATIONINSIGHTS_CONNECTION_STRING string = aiProject.outputs.APPLICATIONINSIGHTS_CONNECTION_STRING
output APPLICATIONINSIGHTS_RESOURCE_ID string = aiProject.outputs.APPLICATIONINSIGHTS_RESOURCE_ID
output AZURE_TENANT_ID string = tenant().tenantId
output POSTGRES_HOST string = enablePostgres ? postgresServer!.outputs.POSTGRES_DOMAIN_NAME : ''
output POSTGRES_DATABASE string = enablePostgres ? postgresDatabaseName : ''
output POSTGRES_SSL string = enablePostgres ? 'require' : ''
output POSTGRES_AUTH_TYPE string = enablePostgres ? 'EntraOnly' : ''
output POSTGRES_AAD_ADMIN_NAME string = enablePostgres ? postgresEntraAdministratorName : ''
output POSTGRES_USERNAME string = enablePostgres ? postgresEntraAdministratorName : ''
output POSTGRES_MCP_URL string = enablePostgres ? '${postgresMcp!.outputs.SERVICE_POSTGRES_MCP_URI}/mcp' : ''
output AZURE_CONTAINER_ENVIRONMENT_NAME string = enablePostgres ? containerApps!.outputs.environmentName : ''
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = enablePostgres ? containerApps!.outputs.registryLoginServer : ''
output AZURE_CONTAINER_REGISTRY_NAME string = enablePostgres ? containerApps!.outputs.registryName : ''
output SERVICE_POSTGRES_MCP_IDENTITY_PRINCIPAL_ID string = enablePostgres ? postgresMcp!.outputs.SERVICE_POSTGRES_MCP_IDENTITY_PRINCIPAL_ID : ''
output SERVICE_POSTGRES_MCP_IDENTITY_NAME string = enablePostgres ? postgresMcp!.outputs.SERVICE_POSTGRES_MCP_IDENTITY_NAME : ''
output SERVICE_POSTGRES_MCP_IMAGE_NAME string = enablePostgres ? postgresMcp!.outputs.SERVICE_POSTGRES_MCP_IMAGE_NAME : ''
output SERVICE_POSTGRES_MCP_NAME string = enablePostgres ? postgresMcp!.outputs.SERVICE_POSTGRES_MCP_NAME : ''
output SERVICE_POSTGRES_MCP_URI string = enablePostgres ? postgresMcp!.outputs.SERVICE_POSTGRES_MCP_URI : ''
