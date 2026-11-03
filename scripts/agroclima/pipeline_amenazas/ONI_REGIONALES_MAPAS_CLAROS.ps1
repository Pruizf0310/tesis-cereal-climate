param(
    [string]$InputDir='C:\Users\paola\Tesis\03_Resultados\Agroclima\vigente\correlaciones\maize_ONI_frecuencias\ONI_regional_conteos_temporada_20261020_144451',
    [string]$Output='',
    [int]$Bootstrap=2000,
    [int]$MinPixels=30,
    [int]$Dpi=300,
    [string]$Formats='png,svg',
    [string]$Python=(Join-Path $PSScriptRoot '.venv\Scripts\python.exe')
)
$ErrorActionPreference='Stop'
if (-not (Test-Path -LiteralPath $Python)) { throw "No se encuentra Python: $Python" }
$clearArgs=@('-u','-X','utf8',(Join-Path $PSScriptRoot 'oni_regional_maiz_y_contexto.py'),'--input',$InputDir,'--bootstrap',$Bootstrap,'--min-pixels',$MinPixels,'--dpi',$Dpi,'--formats',$Formats)
if ($Output) { $clearArgs+=@('--output',$Output) }
Write-Host 'Recalculando IC por ANIOS y graficando SOLO MAIZ con anios, frecuencias y cobertura visibles.'
& $Python @clearArgs
if ($LASTEXITCODE -ne 0) { throw 'La ejecucion no termino. No usar salidas sin completed.json. Datos previos intactos.' }
