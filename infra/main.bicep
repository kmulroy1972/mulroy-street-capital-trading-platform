@description('The name of the environment (dev, staging, prod)')
param environmentName string

@description('The Azure region where resources will be deployed')
param location string = resourceGroup().location

@description('The prefix for resource naming')
param resourcePrefix string = 'alpaca-trader'

@description('PostgreSQL admin username')
param dbAdminUsername string = 'alpacaadmin'

@description('PostgreSQL admin password')
@secure()
param dbAdminPassword string

@description('Alpaca API Key ID')
@secure()
param alpacaApiKeyId string

@description('Alpaca Secret Key')
@secure()
param alpacaSecretKey string

@description('JWT Secret for API authentication')
@secure()
param jwtSecret string

var uniqueSuffix = uniqueString(resourceGroup().id)
var namePrefix = '${resourcePrefix}-${environmentName}'

// Azure Container Registry
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: 'acr${uniqueSuffix}'
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
  tags: {
    environment: environmentName
    project: 'alpaca-trader'
  }
}

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${namePrefix}-kv-${uniqueSuffix}'
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    accessPolicies: []
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enableRbacAuthorization: true
  }
  tags: {
    environment: environmentName
    project: 'alpaca-trader'
  }
}

// Store secrets in Key Vault
resource alpacaApiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'APCA-API-KEY-ID'
  properties: {
    value: alpacaApiKeyId
  }
}

resource alpacaSecretKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'APCA-API-SECRET-KEY'
  properties: {
    value: alpacaSecretKey
  }
}

resource jwtSecretSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'JWT-SECRET'
  properties: {
    value: jwtSecret
  }
}

// PostgreSQL Flexible Server
resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' = {
  name: '${namePrefix}-postgres-${uniqueSuffix}'
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    administratorLogin: dbAdminUsername
    administratorLoginPassword: dbAdminPassword
    version: '15'
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
  }
  tags: {
    environment: environmentName
    project: 'alpaca-trader'
  }
}

// PostgreSQL Database
resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-06-01-preview' = {
  parent: postgresServer
  name: 'alpaca_trader'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// PostgreSQL Firewall Rule (Allow Azure services)
resource postgresFirewallRule 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-06-01-preview' = {
  parent: postgresServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// Redis Cache
resource redisCache 'Microsoft.Cache/redis@2023-08-01' = {
  name: '${namePrefix}-redis-${uniqueSuffix}'
  location: location
  properties: {
    sku: {
      name: 'Basic'
      family: 'C'
      capacity: 0
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
    redisConfiguration: {
      'maxmemory-policy': 'allkeys-lru'
    }
  }
  tags: {
    environment: environmentName
    project: 'alpaca-trader'
  }
}

// Store database and Redis URLs in Key Vault
resource databaseUrlSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'DATABASE-URL'
  properties: {
    value: 'postgresql://${dbAdminUsername}:${dbAdminPassword}@${postgresServer.properties.fullyQualifiedDomainName}:5432/alpaca_trader'
  }
}

resource redisUrlSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'REDIS-URL'
  properties: {
    value: 'rediss://:${redisCache.listKeys().primaryKey}@${redisCache.properties.hostName}:6380/0'
  }
}

// Container Apps Environment
resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: '${namePrefix}-env-${uniqueSuffix}'
  location: location
  properties: {
    daprAIInstrumentationKey: null
    daprAIConnectionString: null
    vnetConfiguration: null
  }
  tags: {
    environment: environmentName
    project: 'alpaca-trader'
  }
}

// Managed Identity for API app
resource apiManagedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${namePrefix}-api-identity'
  location: location
  tags: {
    environment: environmentName
    project: 'alpaca-trader'
  }
}

// Managed Identity for Engine app
resource engineManagedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${namePrefix}-engine-identity'
  location: location
  tags: {
    environment: environmentName
    project: 'alpaca-trader'
  }
}

// Key Vault access policy for API managed identity
resource apiKeyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, apiManagedIdentity.id, 'Key Vault Secrets User')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: apiManagedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Key Vault access policy for Engine managed identity
resource engineKeyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, engineManagedIdentity.id, 'Key Vault Secrets User')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: engineManagedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Container App for API
resource alpacaApiApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${namePrefix}-api'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${apiManagedIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        allowInsecure: false
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: apiManagedIdentity.id
        }
      ]
      secrets: [
        {
          name: 'keyvault-uri'
          value: keyVault.properties.vaultUri
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'alpaca-api'
          image: '${containerRegistry.properties.loginServer}/alpaca-api:latest'
          env: [
            {
              name: 'AZURE_CLIENT_ID'
              value: apiManagedIdentity.properties.clientId
            }
            {
              name: 'KEY_VAULT_URI'
              secretRef: 'keyvault-uri'
            }
            {
              name: 'ENVIRONMENT'
              value: environmentName
            }
          ]
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
  tags: {
    environment: environmentName
    project: 'alpaca-trader'
  }
}

// Container App for Engine
resource alpacaEngineApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${namePrefix}-engine'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${engineManagedIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: engineManagedIdentity.id
        }
      ]
      secrets: [
        {
          name: 'keyvault-uri'
          value: keyVault.properties.vaultUri
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'alpaca-engine'
          image: '${containerRegistry.properties.loginServer}/alpaca-engine:latest'
          env: [
            {
              name: 'AZURE_CLIENT_ID'
              value: engineManagedIdentity.properties.clientId
            }
            {
              name: 'KEY_VAULT_URI'
              secretRef: 'keyvault-uri'
            }
            {
              name: 'ENVIRONMENT'
              value: environmentName
            }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
  tags: {
    environment: environmentName
    project: 'alpaca-trader'
  }
}

// Static Web App for Next.js UI
resource staticWebApp 'Microsoft.Web/staticSites@2023-01-01' = {
  name: '${namePrefix}-web-${uniqueSuffix}'
  location: location
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    repositoryUrl: null
    branch: null
    buildProperties: {
      skipGithubActionWorkflowGeneration: true
    }
  }
  tags: {
    environment: environmentName
    project: 'alpaca-trader'
  }
}

// Outputs
output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output containerRegistryName string = containerRegistry.name
output apiAppUrl string = alpacaApiApp.properties.configuration.ingress.fqdn
output engineAppName string = alpacaEngineApp.name
output keyVaultUri string = keyVault.properties.vaultUri
output keyVaultName string = keyVault.name
output staticWebAppUrl string = staticWebApp.properties.defaultHostname
output postgresServerName string = postgresServer.name
output postgresServerFqdn string = postgresServer.properties.fullyQualifiedDomainName
output redisCacheName string = redisCache.name
output containerAppsEnvironmentName string = containerAppsEnvironment.name