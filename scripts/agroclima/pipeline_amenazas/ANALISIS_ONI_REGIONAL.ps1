param(
    [string]$Regions='',
    [switch]$Proposal,
    [string]$Output='',
    [int]$Bootstrap=2000,
    [int]$Seed=20261019,
    [int]$MinYears=5,
    [string]$Python=(Join-Path $PSScriptRoot '.venv\Scripts\python.exe')
)
$ErrorActionPreference='Stop'
if ($Proposal -and $Regions) { throw 'Usa -Regions o -Proposal, no ambos.' }
if ($Proposal) { $Regions='C:\Users\paola\Tesis\03_Resultados\Agroclima\vigente\correlaciones\maize_ONI_frecuencias\propuesta_regiones_geograficas_20261020\regiones_propuestas_para_revisar.csv' }
if (-not $Regions) { throw 'Indica -Regions con tu tabla revisada o -Proposal para usar explicitamente la propuesta provisional.' }
if (-not (Test-Path -LiteralPath $Regions)) { throw "No se encuentra la tabla de regiones: $Regions" }
if (-not (Test-Path -LiteralPath $Python)) { throw "No se encuentra Python: $Python" }
$regionalArgs=@('-u','-X','utf8',(Join-Path $PSScriptRoot 'oni_regional.py'),'--regions',$Regions,'--bootstrap',$Bootstrap,'--seed',$Seed,'--min-years',$MinYears)
if ($Output) { $regionalArgs+=@('--output',$Output) }
Write-Host 'ONI regional: soporte fijo por contraste y bootstrap compartido de temporadas. Sin GEE ni MJO.'
& $Python @regionalArgs
if ($LASTEXITCODE -ne 0) { throw 'El analisis regional no termino. No usar salidas sin completed.json.' }
