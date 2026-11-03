param(
    [string]$Regions='',
    [string]$PreviousRun='C:\Users\paola\Tesis\03_Resultados\Agroclima\vigente\correlaciones\maize_ONI_frecuencias\ONI_regional_20261020_111438',
    [string]$Output='',
    [int]$Bootstrap=2000,
    [int]$Seed=20261019,
    [int]$MinYears=5,
    [string]$Python=(Join-Path $PSScriptRoot '.venv\Scripts\python.exe')
)
$ErrorActionPreference='Stop'
# Reuse exactly the region assignment already used in the previous run.
if (-not $Regions) { $Regions=Join-Path $PreviousRun 'regiones_utilizadas.csv' }
if (-not (Test-Path -LiteralPath $Regions)) { throw "No se encuentra la tabla de regiones: $Regions" }
if (-not (Test-Path -LiteralPath $Python)) { throw "No se encuentra Python: $Python" }
$seasonArgs=@('-u','-X','utf8',(Join-Path $PSScriptRoot 'oni_regional.py'),'--regions',$Regions,'--measure-mode','seasonal','--regionalization-status','provisional','--bootstrap',$Bootstrap,'--seed',$Seed,'--min-years',$MinYears)
if ($Output) { $seasonArgs+=@('--output',$Output) }
Write-Host 'ONI regional: episodios por temporada (calor) y dias de lluvia por temporada (MAT).'
Write-Host 'Se conservan las regiones anteriores y se crea una salida nueva en la tesis. No usa MJO ni GEE.'
& $Python @seasonArgs
if ($LASTEXITCODE -ne 0) { throw 'El analisis no termino. No usar salidas sin completed.json. Los resultados anteriores se conservan.' }
