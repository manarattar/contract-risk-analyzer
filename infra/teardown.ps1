param([string]$ResourceGroupName = 'rg-contract-analyzer')
$ErrorActionPreference = 'Stop'
$az = (Get-Command az -ErrorAction SilentlyContinue).Source
if (-not $az) { $az = 'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd' }
if (-not (Test-Path $az)) { throw 'Azure CLI not found.' }
$ErrorActionPreference = 'Continue'
& $az group delete --subscription 'Azure for Students' --name $ResourceGroupName --yes 2>&1 | Out-Host
$azExitCode = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($azExitCode -ne 0) { throw "Azure resource group deletion failed: $azExitCode" }
