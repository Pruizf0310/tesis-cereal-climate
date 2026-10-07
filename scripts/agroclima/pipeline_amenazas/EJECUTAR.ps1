param([ValidateSet('prepare','authenticate','export','status','analyze')][string]$Paso='prepare')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno Python.' }
}
& './.venv/Scripts/python.exe' -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
& './.venv/Scripts/python.exe' pipeline.py $Paso
if ($LASTEXITCODE -ne 0) { throw 'Revisar el error mostrado por el pipeline.' }
