targetScope = 'subscription'

@description('Azure region allowed by the Azure for Students subscription policy.')
@allowed(['austriaeast', 'polandcentral', 'switzerlandnorth', 'belgiumcentral', 'swedencentral'])
param location string = 'swedencentral'
param resourceGroupName string = 'rg-contract-analyzer'
param namePrefix string = 'contract-analyzer'
param postgresAdminLogin string
@secure()
param postgresAdminPassword string
@minLength(1)
param contactEmails string[]
param budgetAmount int = 10
param backendImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
param frontendImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
param chatModelName string = 'gpt-5-mini'
param chatModelVersion string = '2025-08-07'
param chatCapacity int = 10
param embeddingCapacity int = 10
param corsOrigins string = '*'
param githubOwner string = 'manarattar'
param githubRepo string = 'contract-risk-analyzer'
param githubEnvironment string = 'azure'

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
}

module core 'modules/core.bicep' = {
  name: 'core'
  scope: rg
  params: {
    location: location
    namePrefix: namePrefix
    postgresAdminLogin: postgresAdminLogin
    postgresAdminPassword: postgresAdminPassword
    backendImage: backendImage
    frontendImage: frontendImage
    chatModelName: chatModelName
    chatModelVersion: chatModelVersion
    chatCapacity: chatCapacity
    embeddingCapacity: embeddingCapacity
    corsOrigins: corsOrigins
  }
}

module budget 'modules/budget.bicep' = {
  name: 'budget'
  scope: rg
  params: {
    amount: budgetAmount
    contactEmails: contactEmails
  }
}

module githubIdentity 'modules/github-identity.bicep' = {
  name: 'github-identity'
  scope: rg
  params: {
    location: location
    githubOwner: githubOwner
    githubRepo: githubRepo
    githubEnvironment: githubEnvironment
    searchServiceId: core.outputs.searchServiceId
  }
}

output frontendUrl string = core.outputs.frontendUrl
output backendInternalFqdn string = core.outputs.backendInternalFqdn
output openaiEndpoint string = core.outputs.openaiEndpoint
output searchEndpoint string = core.outputs.searchEndpoint
output storageAccountUrl string = core.outputs.storageAccountUrl
output githubIdentityClientId string = githubIdentity.outputs.clientId
output tenantId string = tenant().tenantId
output subscriptionId string = subscription().subscriptionId
output resourceGroup string = rg.name
