param([Parameter(Mandatory=$true)][string]$OutputRoot)
$ErrorActionPreference = 'Stop'
$mjoGcloud = 'C:\Users\paola\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd'
$mjoPython = (Join-Path $PSScriptRoot '.venv\Scripts\python.exe')
& $mjoGcloud auth application-default login --scopes=https://www.googleapis.com/auth/cloud-platform
if ($LASTEXITCODE -ne 0) { throw 'No se completó el inicio de sesión. No se lanzó el cálculo.' }
& $mjoPython -u -X utf8 (Join-Path $PSScriptRoot 'ejecutar_cinco_fases_mjo.py') --output $OutputRoot --workers-per-phase 2
if ($LASTEXITCODE -ne 0) { throw 'El cálculo se detuvo. Revisar los registros de cada fase.' }
