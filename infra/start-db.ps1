param([string]$ResourceGroupName = 'rg-contract-analyzer')
$ErrorActionPreference = 'Stop'
$az = (Get-Command az -ErrorAction SilentlyContinue).Source
if (-not $az) { $az = 'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd' }
if (-not (Test-Path $az)) { throw 'Azure CLI not found.' }
$servers = @(& $az postgres flexible-server list --subscription 'Azure for Students' -g $ResourceGroupName --query '[].name' --output tsv)
if ($LASTEXITCODE -ne 0) { throw "Could not list PostgreSQL servers: $LASTEXITCODE" }
$servers = @($servers | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
if ($servers.Count -ne 1) { throw "Expected one PostgreSQL Flexible Server in $ResourceGroupName; found $($servers.Count)." }
& $az postgres flexible-server start --subscription 'Azure for Students' -g $ResourceGroupName -n $servers[0]
if ($LASTEXITCODE -ne 0) { throw "Could not start PostgreSQL server: $LASTEXITCODE" }
