param([string]$OutputRoot = '')
$ErrorActionPreference = 'Stop'
$maizePython = (Join-Path $PSScriptRoot '.venv\Scripts\python.exe')
if (-not (Test-Path -LiteralPath $maizePython)) { throw "No se encuentra el entorno Python: $maizePython" }
$maizeOutput = $OutputRoot
if (-not $maizeOutput) { $maizeOutput = Join-Path (Split-Path $PSScriptRoot -Parent) ('outputs\maize_sql_' + (Get-Date -Format 'yyyyMMdd_HHmmss')) }
foreach ($maizeAlignment in @('same-label', 'maturity-year')) {
    & $maizePython -X utf8 (Join-Path $PSScriptRoot 'maize_base_sql.py') --alignment $maizeAlignment --output $maizeOutput
    if ($LASTEXITCODE -ne 0) { throw "Falló el escenario $maizeAlignment. Se conserva la salida para revisión." }
}
Write-Host "Bases y gráficas completas: $maizeOutput"
