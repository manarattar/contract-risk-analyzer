param(
  [string]$ResourceGroupName = 'rg-contract-analyzer',
  [string]$Location = 'swedencentral',
  [string]$AdminLogin = 'craadmin',
  [string[]]$ContactEmails,
  [securestring]$AdminPassword,
  [string]$BackendImage,
  [string]$FrontendImage,
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
  $placeholderImage = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
  if (-not $env:CRA_BACKEND_IMAGE -and -not $BackendImage) {
    $ErrorActionPreference = 'Continue'
    $BackendImage = (& $az containerapp show --subscription 'Azure for Students' -g $ResourceGroupName -n 'contract-analyzer-backend' --query 'properties.template.containers[0].image' --output tsv 2>$null)
    $imageExitCode = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($imageExitCode -ne 0 -or -not $BackendImage) { $BackendImage = $placeholderImage }
  }
  if (-not $env:CRA_FRONTEND_IMAGE -and -not $FrontendImage) {
    $ErrorActionPreference = 'Continue'
    $FrontendImage = (& $az containerapp show --subscription 'Azure for Students' -g $ResourceGroupName -n 'contract-analyzer-frontend' --query 'properties.template.containers[0].image' --output tsv 2>$null)
    $imageExitCode = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($imageExitCode -ne 0 -or -not $FrontendImage) { $FrontendImage = $placeholderImage }
  }
  $env:CRA_RESOURCE_GROUP_NAME = $ResourceGroupName
  $env:CRA_LOCATION = $Location
  $env:CRA_POSTGRES_ADMIN_LOGIN = $AdminLogin
  $env:CRA_POSTGRES_ADMIN_PASSWORD = $plainPassword
  $env:CRA_CONTACT_EMAILS = $ContactEmails -join ','
  if (-not $env:CRA_BACKEND_IMAGE) { $env:CRA_BACKEND_IMAGE = $BackendImage }
  if (-not $env:CRA_FRONTEND_IMAGE) { $env:CRA_FRONTEND_IMAGE = $FrontendImage }
  $env:CRA_CHAT_CAPACITY = [string]$ChatCapacity
  $env:CRA_EMBEDDING_CAPACITY = [string]$EmbeddingCapacity
  $ErrorActionPreference = 'Continue'
  & $az deployment sub create --subscription 'Azure for Students' --name 'contract-analyzer-phase2' --location $Location --parameters "$PSScriptRoot/main.bicepparam" --output json 2>&1 | Out-Host
  $azExitCode = $LASTEXITCODE
  $ErrorActionPreference = 'Stop'
  if ($azExitCode -ne 0) { throw "Azure deployment failed: $azExitCode" }
} finally {
  $plainPassword = $null
  'CRA_RESOURCE_GROUP_NAME', 'CRA_LOCATION', 'CRA_POSTGRES_ADMIN_LOGIN', 'CRA_POSTGRES_ADMIN_PASSWORD', 'CRA_CONTACT_EMAILS', 'CRA_BACKEND_IMAGE', 'CRA_FRONTEND_IMAGE', 'CRA_CHAT_CAPACITY', 'CRA_EMBEDDING_CAPACITY' | ForEach-Object { Remove-Item "Env:$_" -ErrorAction SilentlyContinue }
}
