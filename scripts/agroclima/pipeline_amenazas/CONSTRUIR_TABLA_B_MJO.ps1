param(
    [switch]$Pilot,
    [string]$Output='',
    [string]$TesisRoot='C:\Users\paola\Tesis',
    [string]$Python=(Join-Path $PSScriptRoot '.venv\Scripts\python.exe')
)
$ErrorActionPreference='Stop'
if (-not (Test-Path -LiteralPath $Python)) { throw "No se encuentra Python: $Python" }
$dailyArgs=@('-u','-X','utf8',(Join-Path $PSScriptRoot 'construir_tabla_B_mjo.py'),'--root',$TesisRoot)
if ($Output) { $dailyArgs+=@('--output',$Output) }
if ($Pilot) { $dailyArgs+=@('--pixels','71854,74033,81973') }
Write-Host 'Reconstruyendo Tabla B diaria desde caches locales. Sin GEE ni descargas.'
& $Python @dailyArgs
if ($LASTEXITCODE -ne 0) { throw 'Tabla B no terminada; no usar salidas sin completed.json. Repetir con otra carpeta de salida.' }
