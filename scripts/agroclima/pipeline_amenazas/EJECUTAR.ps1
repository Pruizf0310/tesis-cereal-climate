param([ValidateSet('run','prepare','download','authenticate','export','status','analyze')][string]$Paso='run', [string]$Proyecto='')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno Python.' }
}
& './.venv/Scripts/python.exe' -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
if ($Paso -eq 'run' -and -not $Proyecto -and -not $env:EE_PROJECT -and -not $env:GOOGLE_CLOUD_PROJECT) {
    $taskConfig = Get-Content -LiteralPath './config.json' -Raw | ConvertFrom-Json
    if ($taskConfig.project -like 'PONER_*') { $Proyecto = Read-Host 'ID de tu proyecto habilitado en GEE' }
}
if ($Proyecto) { & './.venv/Scripts/python.exe' pipeline.py $Paso --project $Proyecto }
else { & './.venv/Scripts/python.exe' pipeline.py $Paso }
if ($LASTEXITCODE -ne 0) { throw 'Revisar el error mostrado por el pipeline.' }
