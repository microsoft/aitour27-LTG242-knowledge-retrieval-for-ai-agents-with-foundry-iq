targetScope = 'resourceGroup'

@description('AI Services account name')
param aiServicesAccountName string

@description('AI project name')
param aiProjectName string

type ConnectionConfig = {
  name: string
  category: string
  target: string
  authType: 'AAD' | 'AccessKey' | 'AccountKey' | 'ApiKey' | 'CustomKeys' | 'ManagedIdentity' | 'None' | 'OAuth2' | 'PAT' | 'ProjectManagedIdentity' | 'SAS' | 'ServicePrincipal' | 'UsernamePassword'
  audience: string?
  isSharedToAll: bool?
  credentials: object?
  metadata: object?
}

@description('Connection configuration')
param connectionConfig ConnectionConfig

@secure()
@description('API key for ApiKey-based connections.')
param apiKey string = ''

resource aiAccount 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: aiServicesAccountName

  resource project 'projects' existing = {
    name: aiProjectName
  }
}

resource connection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  parent: aiAccount::project
  name: connectionConfig.name
  properties: {
    category: connectionConfig.category
    target: connectionConfig.target
    #disable-next-line BCP036
    authType: connectionConfig.authType
    audience: connectionConfig.?audience
    isSharedToAll: connectionConfig.?isSharedToAll ?? true
    credentials: connectionConfig.authType == 'ApiKey' ? {
      key: apiKey
    } : connectionConfig.?credentials
    metadata: connectionConfig.?metadata
  }
}

output connectionName string = connection.name
output connectionId string = connection.id
