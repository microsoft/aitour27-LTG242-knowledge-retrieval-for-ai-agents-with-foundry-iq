param name string
param location string = resourceGroup().location
param tags object = {}
param containerAppsEnvironmentName string
param containerRegistryName string
param postgresHost string
param postgresDatabase string
@secure()
param mcpApiKey string
param imageName string = ''
param tenantId string
param applicationInsightsConnectionString string = ''
param serviceName string = 'postgres-mcp'

var identityName = 'id-${name}'

module app 'core/host/container-app.bicep' = {
  params: {
    name: name
    location: location
    tags: tags
    serviceName: serviceName
    identityName: identityName
    containerAppsEnvironmentName: containerAppsEnvironmentName
    containerRegistryName: containerRegistryName
    imageName: imageName
    targetPort: empty(imageName) ? 80 : 8010
    secrets: {
      'mcp-api-key': mcpApiKey
    }
    env: [
      {
        name: 'POSTGRES_HOST'
        value: postgresHost
      }
      {
        name: 'POSTGRES_DATABASE'
        value: postgresDatabase
      }
      {
        name: 'POSTGRES_USERNAME'
        value: identityName
      }
      {
        name: 'POSTGRES_SSL'
        value: 'require'
      }
      {
        name: 'AZURE_TENANT_ID'
        value: tenantId
      }
      {
        name: 'MCP_API_KEY'
        secretRef: 'mcp-api-key'
      }
      {
        name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
        value: applicationInsightsConnectionString
      }
    ]
  }
}

output SERVICE_POSTGRES_MCP_IDENTITY_PRINCIPAL_ID string = app.outputs.identityPrincipalId
output SERVICE_POSTGRES_MCP_IDENTITY_NAME string = app.outputs.identityName
output SERVICE_POSTGRES_MCP_IMAGE_NAME string = app.outputs.imageName
output SERVICE_POSTGRES_MCP_NAME string = app.outputs.name
output SERVICE_POSTGRES_MCP_URI string = app.outputs.uri
