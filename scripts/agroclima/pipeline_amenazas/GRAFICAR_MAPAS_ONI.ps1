param(
    [string]$SensitivityDir = '',
    [string]$Output = '',
    [int]$Dpi = 450,
    [string]$Formats = 'png,svg',
    [string]$Scales = '',
    [string]$Outline = 'C:\Users\paola\Tesis\Repositorio\tesis-cereal-climate\web-v2\public\data\world_outline.geojson',
    [string]$Python = (Join-Path $PSScriptRoot '.venv\Scripts\python.exe')
)
$ErrorActionPreference='Stop'
if (-not $SensitivityDir) { $SensitivityDir='C:\Users\paola\Tesis\03_Resultados\Agroclima\vigente\correlaciones\maize_ONI_frecuencias\sensibilidad_ONI_20261019_211459' }
if (-not (Test-Path -LiteralPath $Python)) { throw "No se encuentra Python: $Python" }
& $Python -c 'import numpy,pandas,matplotlib'
if ($LASTEXITCODE -ne 0) { throw 'Se requieren numpy, pandas y matplotlib; no se instalo nada.' }
$mapArgs=@('-u','-X','utf8',(Join-Path $PSScriptRoot 'graficar_contrastes_oni_elegantes.py'),'--sensitivity',$SensitivityDir,'--outline',$Outline,'--dpi',$Dpi,'--formats',$Formats)
if ($Output) { $mapArgs+=@('--output',$Output) }
if ($Scales) { $mapArgs+=@('--scales',$Scales) }
Write-Host 'Graficando original y sensibilidad con escalas comunes congeladas. Sin GEE ni descargas.'
& $Python @mapArgs
if ($LASTEXITCODE -ne 0) { throw 'Los mapas no terminaron. Revisar el error; no sobrescribe datos de analisis.' }
