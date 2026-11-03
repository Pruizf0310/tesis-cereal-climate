param(
    [string]$InputDir='C:\Users\paola\Tesis\03_Resultados\Agroclima\vigente\correlaciones\maize_ONI_frecuencias\ONI_regional_conteos_temporada_20261020_144451',
    [string]$Output='',
    [int]$Dpi=400,
    [string]$Formats='png,svg',
    [string]$Scales='',
    [string]$Python=(Join-Path $PSScriptRoot '.venv\Scripts\python.exe')
)
$ErrorActionPreference='Stop'
if (-not (Test-Path -LiteralPath $Python)) { throw "No se encuentra Python: $Python" }
$regionalMapArgs=@('-u','-X','utf8',(Join-Path $PSScriptRoot 'mapas_oni_regionales_temporada.py'),'--input',$InputDir,'--dpi',$Dpi,'--formats',$Formats)
if ($Output) { $regionalMapArgs+=@('--output',$Output) }
if ($Scales) { $regionalMapArgs+=@('--scales',$Scales) }
Write-Host 'Generando SEIS MAPAS REGIONALES con paneles de intervalos, en episodios/dias por temporada. Sin recalcular bootstrap ni usar MJO.'
& $Python @regionalMapArgs
if ($LASTEXITCODE -ne 0) { throw 'La exportacion no termino. Revisar el error; las tablas anteriores siguen intactas.' }
