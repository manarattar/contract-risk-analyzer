param location string
param githubOwner string
param githubRepo string
param githubEnvironment string
param searchServiceId string

resource search 'Microsoft.Search/searchServices@2024-06-01-preview' existing = {
  name: last(split(searchServiceId, '/'))
}

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'contract-analyzer-github'
  location: location
}

resource federation 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = {
  parent: identity
  name: 'github-azure'
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    audiences: ['api://AzureADTokenExchange']
    subject: 'repo:${githubOwner}/${githubRepo}:environment:${githubEnvironment}'
  }
}

// Contributor at RG scope is required by az containerapp update; narrower custom roles are possible later.
resource contributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, identity.id, 'contributor')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b24988ac-6180-42a0-ab88-20f7382dd24c')
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource searchServiceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchServiceId, identity.id, 'search-service-contributor')
  scope: search
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7ca78c08-252a-4471-8644-bb5ff32d4ba0')
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

output clientId string = identity.properties.clientId
