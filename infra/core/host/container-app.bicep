metadata description = 'Creates a public Azure Container App with a user-assigned identity.'

param name string
param location string = resourceGroup().location
param tags object = {}
param serviceName string
param containerAppsEnvironmentName string
param containerRegistryName string
param identityName string
param env array = []
@secure()
param secrets object = {}
param targetPort int = 8010
param imageName string = ''

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
  tags: tags
}

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: containerRegistryName
}

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: containerAppsEnvironmentName
}

var acrPullRoleDefinitionId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '7f951dda-4ed3-4680-a7ca-43fe172d538d'
)

resource registryPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, identity.id, acrPullRoleDefinitionId)
  scope: registry
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: acrPullRoleDefinitionId
  }
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: union(tags, { 'azd-service-name': serviceName })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: targetPort
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: registry.properties.loginServer
          identity: identity.id
        }
      ]
      secrets: map(items(secrets), secret => {
        name: secret.key
        value: secret.value
      })
    }
    template: {
      containers: [
        {
          name: serviceName
          image: empty(imageName) ? 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' : imageName
          env: concat(env, [
            {
              name: 'AZURE_CLIENT_ID'
              value: identity.properties.clientId
            }
          ])
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
  dependsOn: [
    registryPullRole
  ]
}

output identityName string = identity.name
output identityPrincipalId string = identity.properties.principalId
output imageName string = app.properties.template.containers[0].image
output name string = app.name
output uri string = 'https://${app.properties.configuration.ingress.fqdn}'
