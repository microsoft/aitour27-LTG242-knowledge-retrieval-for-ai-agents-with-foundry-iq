param name string
param location string = resourceGroup().location
param tags object = {}

param sku object
param storage object

@allowed([
  'Password'
  'EntraOnly'
])
param authType string = 'Password'

param administratorLogin string = ''
@secure()
param administratorLoginPassword string = ''

@description('Entra admin role name')
param entraAdministratorName string = ''

@description('Entra admin role object ID (in Entra)')
param entraAdministratorObjectId string = ''

@description('Entra admin user type')
@allowed([
  'User'
  'Group'
  'ServicePrincipal'
])
param entraAdministratorType string = 'User'

param databaseNames array = []
param allowAzureIPsFirewall bool = false
param allowAllIPsFirewall bool = false
param allowedSingleIPs array = []

@description('Comma-delimited extension allow list for azure.extensions')
param allowedExtensions string = 'vector'

// PostgreSQL version
param version string

var authProperties = authType == 'Password' ? {
  administratorLogin: administratorLogin
  administratorLoginPassword: administratorLoginPassword
  authConfig: {
    passwordAuth: 'Enabled'
  }
} : {
  authConfig: {
    activeDirectoryAuth: 'Enabled'
    passwordAuth: 'Disabled'
  }
}

resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2022-12-01' = {
  location: location
  tags: tags
  name: name
  sku: sku
  properties: union(authProperties, {
    version: version
    storage: storage
    highAvailability: {
      mode: 'Disabled'
    }
  })

  resource database 'databases' = [for databaseName in databaseNames: {
    name: databaseName
  }]
}

resource firewall_all 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-03-01-preview' = if (allowAllIPsFirewall) {
  parent: postgresServer
  name: 'allow-all-IPs'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '255.255.255.255'
  }
}

resource firewall_azure 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-03-01-preview' = if (allowAzureIPsFirewall) {
  parent: postgresServer
  name: 'allow-all-azure-internal-IPs'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

@batchSize(1)
resource firewall_single 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-03-01-preview' = [for ip in allowedSingleIPs: {
  parent: postgresServer
  name: 'allow-single-${replace(ip, '.', '')}'
  properties: {
    startIpAddress: ip
    endIpAddress: ip
  }
}]

resource addAddUser 'Microsoft.DBforPostgreSQL/flexibleServers/administrators@2023-03-01-preview' = if (authType == 'EntraOnly') {
  parent: postgresServer
  name: entraAdministratorObjectId
  properties: {
    tenantId: subscription().tenantId
    principalType: entraAdministratorType
    principalName: entraAdministratorName
  }
  dependsOn: [firewall_all, firewall_azure]
}

resource configurations 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2023-03-01-preview' = {
  name: 'azure.extensions'
  parent: postgresServer
  properties: {
    value: allowedExtensions
    source: 'user-override'
  }
  dependsOn: [
    addAddUser
    firewall_all
    firewall_azure
    firewall_single
  ]
}

output POSTGRES_DOMAIN_NAME string = postgresServer.properties.fullyQualifiedDomainName
