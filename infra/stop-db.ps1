param([string]$ResourceGroupName = 'rg-contract-analyzer')
$ErrorActionPreference = 'Stop'
$az = (Get-Command az -ErrorAction SilentlyContinue).Source
if (-not $az) { $az = 'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd' }
if (-not (Test-Path $az)) { throw 'Azure CLI not found.' }
$ErrorActionPreference = 'Continue'
$servers = @(& $az postgres flexible-server list --subscription 'Azure for Students' -g $ResourceGroupName --query '[].name' --output tsv 2>&1 | ForEach-Object { if ($_ -is [System.Management.Automation.ErrorRecord]) { Write-Host $_.Exception.Message } else { $_ } })
$listExitCode = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($listExitCode -ne 0) { throw "Could not list PostgreSQL servers: $listExitCode" }
$servers = @($servers | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
if ($servers.Count -ne 1) { throw "Expected one PostgreSQL Flexible Server in $ResourceGroupName; found $($servers.Count)." }
$ErrorActionPreference = 'Continue'
& $az postgres flexible-server stop --subscription 'Azure for Students' -g $ResourceGroupName -n $servers[0] 2>&1 | ForEach-Object { if ($_ -is [System.Management.Automation.ErrorRecord]) { Write-Host $_.Exception.Message } else { $_ } } | Out-Host
$azExitCode = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($azExitCode -ne 0) { throw "Could not stop PostgreSQL server: $azExitCode" }
