param(
    [string]$InputDir = '',
    [string]$TesisRoot = 'C:\Users\paola\Tesis',
    [string]$Output = '',
    [string]$Python = ''
)
$ErrorActionPreference = 'Stop'
if (-not $InputDir) {
    $InputDir = Join-Path $TesisRoot '03_Resultados\Agroclima\vigente\correlaciones\maize_ONI_frecuencias\matriz_frecuencias_ONI_20261019_152551'
}
if (-not $Python) {
    $Python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
}
if (-not (Test-Path -LiteralPath $Python)) { throw "No se encontro Python: $Python. Usa -Python para indicar otra ruta." }
$correctionScript = Join-Path $PSScriptRoot 'corregir_matriz_cobertura_espacial.py'
if (-not (Test-Path -LiteralPath $correctionScript)) { throw "Falta el script $correctionScript" }
$correctionArgs = @('-u', '-X', 'utf8', $correctionScript, '--root', $TesisRoot, '--input', $InputDir)
if ($Output) { $correctionArgs += @('--output', $Output) }
Write-Host 'Corrigiendo una COPIA de la matriz desde los caches locales. Sin GEE ni descargas.'
& $Python @correctionArgs
if ($LASTEXITCODE -ne 0) { throw 'La correccion no termino. No usar salidas sin completed.json. La entrada sigue intacta.' }
