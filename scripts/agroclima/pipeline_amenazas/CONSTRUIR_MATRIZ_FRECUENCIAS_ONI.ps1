param(
    [string]$TesisRoot = 'C:\Users\paola\Tesis',
    [string]$Output = '',
    [string]$Python = ''
)
$ErrorActionPreference = 'Stop'
if (-not $Python) {
    $Python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
}
if (-not (Test-Path -LiteralPath $Python)) {
    throw "No se encontró Python en $Python. Indica un entorno con numpy y pandas mediante -Python."
}
$matrixScript = Join-Path $PSScriptRoot 'construir_matriz_frecuencias_oni.py'
if (-not (Test-Path -LiteralPath $matrixScript)) { throw "Falta el script: $matrixScript" }
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'correlacion_oni_amenazas.py'))) {
    throw 'Falta correlacion_oni_amenazas.py junto al script principal.'
}
& $Python -c 'import numpy, pandas'
if ($LASTEXITCODE -ne 0) { throw 'El entorno necesita numpy y pandas. No se instaló ni modificó nada.' }
$matrixArgs = @('-u', '-X', 'utf8', $matrixScript, '--root', $TesisRoot)
if ($Output) { $matrixArgs += @('--output', $Output) }
Write-Host 'Construyendo matriz local. No consulta GEE ni descarga datos.'
& $Python @matrixArgs
if ($LASTEXITCODE -ne 0) {
    throw 'La ejecución no terminó. No usar la salida sin completed.json. Revisa el error y usa una carpeta nueva al repetir.'
}
