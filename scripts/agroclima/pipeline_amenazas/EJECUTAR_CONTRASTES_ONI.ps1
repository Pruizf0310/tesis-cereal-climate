param(
    [string]$InputDir = '',
    [string]$Output = '',
    [int]$Bootstrap = 2000,
    [int]$Seed = 20261019,
    [int]$MinYears = 5,
    [string]$Regions = '',
    [string]$Python = (Join-Path $PSScriptRoot '.venv\Scripts\python.exe')
)
$ErrorActionPreference = 'Stop'
if (-not $InputDir) {
    $InputDir = 'C:\Users\paola\Tesis\03_Resultados\Agroclima\vigente\correlaciones\maize_ONI_frecuencias\matriz_frecuencias_ONI_corregida_20261019_165114'
}
if (-not (Test-Path -LiteralPath $Python)) { throw "No se encuentra Python: $Python" }
& $Python -c 'import numpy, pandas'
if ($LASTEXITCODE -ne 0) { throw 'El entorno requiere numpy y pandas; no se instalo nada.' }
$oniArgs = @('-u', '-X', 'utf8', (Join-Path $PSScriptRoot 'contrastes_frecuencias_oni.py'), '--input', $InputDir, '--bootstrap', $Bootstrap, '--seed', $Seed, '--min-years', $MinYears)
if ($Output) { $oniArgs += @('--output', $Output) }
if ($Regions) { $oniArgs += @('--regions', $Regions) }
Write-Host 'Calculando medias y contrastes ONI con bootstrap de temporadas. CPU local; sin GEE.'
& $Python @oniArgs
if ($LASTEXITCODE -ne 0) { throw 'El analisis no termino; no usar salidas sin completed.json. La matriz permanece intacta.' }
