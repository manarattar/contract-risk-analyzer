using './main.bicep'

param location = readEnvironmentVariable('CRA_LOCATION', 'swedencentral')
param resourceGroupName = readEnvironmentVariable('CRA_RESOURCE_GROUP_NAME', 'rg-contract-analyzer')
param namePrefix = 'contract-analyzer'
param postgresAdminLogin = readEnvironmentVariable('CRA_POSTGRES_ADMIN_LOGIN')
param postgresAdminPassword = readEnvironmentVariable('CRA_POSTGRES_ADMIN_PASSWORD')
param contactEmails = split(readEnvironmentVariable('CRA_CONTACT_EMAILS'), ',')
param backendImage = readEnvironmentVariable('CRA_BACKEND_IMAGE', 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest')
param frontendImage = readEnvironmentVariable('CRA_FRONTEND_IMAGE', 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest')
param chatModelName = readEnvironmentVariable('CRA_CHAT_MODEL_NAME', 'gpt-5-mini')
param chatModelVersion = readEnvironmentVariable('CRA_CHAT_MODEL_VERSION', '2025-08-07')
param chatCapacity = int(readEnvironmentVariable('CRA_CHAT_CAPACITY', '10'))
param embeddingCapacity = int(readEnvironmentVariable('CRA_EMBEDDING_CAPACITY', '10'))
