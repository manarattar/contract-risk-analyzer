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
param chatModelName string = 'gpt-5.4-mini'
param chatModelVersion string = '2026-03-17'
param chatCapacity int = 10
param embeddingCapacity int = 10
param corsOrigins string = '*'

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

output frontendUrl string = core.outputs.frontendUrl
output backendInternalFqdn string = core.outputs.backendInternalFqdn
output openaiEndpoint string = core.outputs.openaiEndpoint
output searchEndpoint string = core.outputs.searchEndpoint
output storageAccountUrl string = core.outputs.storageAccountUrl
