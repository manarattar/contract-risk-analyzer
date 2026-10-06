param(
  [string]$ResourceGroupName = 'rg-contract-analyzer',
  [string]$Location = 'swedencentral',
  [string]$AdminLogin = 'craadmin',
  [string[]]$ContactEmails,
  [securestring]$AdminPassword,
  [string]$BackendImage = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest',
  [string]$FrontendImage = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest',
  [int]$ChatCapacity = 10,
  [int]$EmbeddingCapacity = 10
)
$ErrorActionPreference = 'Stop'
$az = (Get-Command az -ErrorAction SilentlyContinue).Source
if (-not $az) { $az = 'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd' }
if (-not (Test-Path $az)) { throw 'Azure CLI not found.' }
if (-not $AdminPassword) { $AdminPassword = Read-Host 'PostgreSQL admin password' -AsSecureString }
if (-not $ContactEmails -or $ContactEmails.Count -eq 0) { $ContactEmails = @((Read-Host 'Budget contact email')) }
if ($ContactEmails | Where-Object { [string]::IsNullOrWhiteSpace($_) }) { throw 'Contact emails must be nonempty.' }
$plainPassword = [System.Net.NetworkCredential]::new('', $AdminPassword).Password
try {
  $env:CRA_RESOURCE_GROUP_NAME = $ResourceGroupName
  $env:CRA_LOCATION = $Location
  $env:CRA_POSTGRES_ADMIN_LOGIN = $AdminLogin
  $env:CRA_POSTGRES_ADMIN_PASSWORD = $plainPassword
  $env:CRA_CONTACT_EMAILS = $ContactEmails -join ','
  $env:CRA_BACKEND_IMAGE = $BackendImage
  $env:CRA_FRONTEND_IMAGE = $FrontendImage
  $env:CRA_CHAT_CAPACITY = [string]$ChatCapacity
  $env:CRA_EMBEDDING_CAPACITY = [string]$EmbeddingCapacity
  & $az deployment sub what-if --subscription 'Azure for Students' --name 'contract-analyzer-phase2' --location $Location --parameters "$PSScriptRoot/main.bicepparam" --output json
  if ($LASTEXITCODE -ne 0) { throw "Azure what-if failed: $LASTEXITCODE" }
} finally {
  $plainPassword = $null
  'CRA_RESOURCE_GROUP_NAME', 'CRA_LOCATION', 'CRA_POSTGRES_ADMIN_LOGIN', 'CRA_POSTGRES_ADMIN_PASSWORD', 'CRA_CONTACT_EMAILS', 'CRA_BACKEND_IMAGE', 'CRA_FRONTEND_IMAGE', 'CRA_CHAT_CAPACITY', 'CRA_EMBEDDING_CAPACITY' | ForEach-Object { Remove-Item "Env:$_" -ErrorAction SilentlyContinue }
}
